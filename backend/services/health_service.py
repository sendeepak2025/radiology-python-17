"""
Health check service for monitoring system components.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from services.redis_service import RedisService
from exceptions import KiroException

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    response_time_ms: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    checks: List[HealthCheck]
    timestamp: float
    version: str
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "checks": [check.to_dict() for check in self.checks],
            "timestamp": self.timestamp,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "summary": {
                "total_checks": len(self.checks),
                "healthy_checks": len([c for c in self.checks if c.status == HealthStatus.HEALTHY]),
                "degraded_checks": len([c for c in self.checks if c.status == HealthStatus.DEGRADED]),
                "unhealthy_checks": len([c for c in self.checks if c.status == HealthStatus.UNHEALTHY])
            }
        }


class HealthService:
    """Service for performing health checks on system components."""
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.start_time = time.time()
        self.redis_service = RedisService()
    
    async def check_database(self, timeout: float = 5.0) -> HealthCheck:
        """Check database connectivity and performance."""
        start_time = time.time()
        
        try:
            db = next(get_db())
            
            # Test basic connectivity
            result = db.execute(text("SELECT 1")).scalar()
            
            # Test performance with a simple query
            db.execute(text("SELECT COUNT(*) FROM studies")).scalar()
            
            response_time = (time.time() - start_time) * 1000
            
            if response_time > 1000:  # > 1 second
                status = HealthStatus.DEGRADED
                message = f"Database responding slowly ({response_time:.0f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Database connection healthy"
            
            return HealthCheck(
                name="database",
                status=status,
                message=message,
                details={
                    "connection_pool_size": db.get_bind().pool.size(),
                    "checked_out_connections": db.get_bind().pool.checkedout(),
                    "query_result": result
                },
                response_time_ms=response_time,
                timestamp=time.time()
            )
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {str(exc)}")
            
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(exc)}",
                details={"error": str(exc)},
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    async def check_redis(self, timeout: float = 5.0) -> HealthCheck:
        """Check Redis connectivity and performance."""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            await self.redis_service.ping()
            
            # Test read/write operations
            test_key = "health_check_test"
            test_value = str(time.time())
            
            await self.redis_service.set(test_key, test_value, expire=60)
            retrieved_value = await self.redis_service.get(test_key)
            await self.redis_service.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if retrieved_value != test_value:
                raise Exception("Redis read/write test failed")
            
            if response_time > 500:  # > 500ms
                status = HealthStatus.DEGRADED
                message = f"Redis responding slowly ({response_time:.0f}ms)"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis connection healthy"
            
            # Get Redis info
            info = await self.redis_service.info()
            
            return HealthCheck(
                name="redis",
                status=status,
                message=message,
                details={
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "redis_version": info.get("redis_version", "unknown"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                },
                response_time_ms=response_time,
                timestamp=time.time()
            )
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {str(exc)}")
            
            return HealthCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(exc)}",
                details={"error": str(exc)},
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    async def check_orthanc(self, orthanc_url: str = "http://orthanc:8042", timeout: float = 5.0) -> HealthCheck:
        """Check Orthanc DICOM server connectivity."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Check Orthanc system endpoint
                response = await client.get(f"{orthanc_url}/system")
                response.raise_for_status()
                
                system_info = response.json()
                response_time = (time.time() - start_time) * 1000
                
                if response_time > 2000:  # > 2 seconds
                    status = HealthStatus.DEGRADED
                    message = f"Orthanc responding slowly ({response_time:.0f}ms)"
                else:
                    status = HealthStatus.HEALTHY
                    message = "Orthanc connection healthy"
                
                return HealthCheck(
                    name="orthanc",
                    status=status,
                    message=message,
                    details={
                        "version": system_info.get("Version", "unknown"),
                        "name": system_info.get("Name", "unknown"),
                        "database_version": system_info.get("DatabaseVersion", "unknown"),
                        "dicom_port": system_info.get("DicomPort", "unknown"),
                        "http_port": system_info.get("HttpPort", "unknown")
                    },
                    response_time_ms=response_time,
                    timestamp=time.time()
                )
                
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Orthanc health check failed: {str(exc)}")
            
            return HealthCheck(
                name="orthanc",
                status=HealthStatus.UNHEALTHY,
                message=f"Orthanc connection failed: {str(exc)}",
                details={"error": str(exc), "url": orthanc_url},
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    async def check_ai_service(self, ai_service_url: str = "http://ai-service:8080", timeout: float = 10.0) -> HealthCheck:
        """Check AI service connectivity."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Check AI service health endpoint
                response = await client.get(f"{ai_service_url}/health")
                response.raise_for_status()
                
                health_info = response.json()
                response_time = (time.time() - start_time) * 1000
                
                if response_time > 5000:  # > 5 seconds
                    status = HealthStatus.DEGRADED
                    message = f"AI service responding slowly ({response_time:.0f}ms)"
                else:
                    status = HealthStatus.HEALTHY
                    message = "AI service connection healthy"
                
                return HealthCheck(
                    name="ai_service",
                    status=status,
                    message=message,
                    details={
                        "service_status": health_info.get("status", "unknown"),
                        "model_version": health_info.get("model_version", "unknown"),
                        "gpu_available": health_info.get("gpu_available", False),
                        "queue_size": health_info.get("queue_size", 0)
                    },
                    response_time_ms=response_time,
                    timestamp=time.time()
                )
                
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"AI service health check failed: {str(exc)}")
            
            return HealthCheck(
                name="ai_service",
                status=HealthStatus.UNHEALTHY,
                message=f"AI service connection failed: {str(exc)}",
                details={"error": str(exc), "url": ai_service_url},
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    async def check_system_resources(self) -> HealthCheck:
        """Check system resource usage."""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "System resources critically high"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = HealthStatus.DEGRADED
                message = "System resources elevated"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
                },
                response_time_ms=response_time,
                timestamp=time.time()
            )
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"System resources health check failed: {str(exc)}")
            
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"System resources check failed: {str(exc)}",
                details={"error": str(exc)},
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    async def check_queue_health(self) -> HealthCheck:
        """Check job queue health."""
        start_time = time.time()
        
        try:
            # Check queue sizes and processing status
            queue_info = await self.redis_service.get_queue_info()
            
            response_time = (time.time() - start_time) * 1000
            
            pending_jobs = queue_info.get("pending_jobs", 0)
            failed_jobs = queue_info.get("failed_jobs", 0)
            
            if failed_jobs > 10 or pending_jobs > 100:
                status = HealthStatus.DEGRADED
                message = f"Queue has {pending_jobs} pending and {failed_jobs} failed jobs"
            elif failed_jobs > 0 or pending_jobs > 50:
                status = HealthStatus.DEGRADED
                message = f"Queue processing normally with some backlog"
            else:
                status = HealthStatus.HEALTHY
                message = "Queue processing normally"
            
            return HealthCheck(
                name="job_queue",
                status=status,
                message=message,
                details=queue_info,
                response_time_ms=response_time,
                timestamp=time.time()
            )
            
        except Exception as exc:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Queue health check failed: {str(exc)}")
            
            return HealthCheck(
                name="job_queue",
                status=HealthStatus.UNHEALTHY,
                message=f"Queue health check failed: {str(exc)}",
                details={"error": str(exc)},
                response_time_ms=response_time,
                timestamp=time.time()
            )
    
    async def perform_health_check(
        self,
        include_external: bool = True,
        orthanc_url: str = "http://orthanc:8042",
        ai_service_url: str = "http://ai-service:8080"
    ) -> SystemHealth:
        """Perform comprehensive health check."""
        logger.info("Starting comprehensive health check")
        
        # Run all health checks concurrently
        tasks = [
            self.check_database(),
            self.check_redis(),
            self.check_system_resources(),
            self.check_queue_health()
        ]
        
        if include_external:
            tasks.extend([
                self.check_orthanc(orthanc_url),
                self.check_ai_service(ai_service_url)
            ])
        
        checks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions in health checks
        valid_checks = []
        for i, check in enumerate(checks):
            if isinstance(check, Exception):
                logger.error(f"Health check {i} failed with exception: {str(check)}")
                # Create a failed health check
                valid_checks.append(HealthCheck(
                    name=f"check_{i}",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(check)}",
                    details={"error": str(check)},
                    response_time_ms=0,
                    timestamp=time.time()
                ))
            else:
                valid_checks.append(check)
        
        # Determine overall system status
        unhealthy_count = len([c for c in valid_checks if c.status == HealthStatus.UNHEALTHY])
        degraded_count = len([c for c in valid_checks if c.status == HealthStatus.DEGRADED])
        
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        uptime = time.time() - self.start_time
        
        system_health = SystemHealth(
            status=overall_status,
            checks=valid_checks,
            timestamp=time.time(),
            version=self.version,
            uptime_seconds=uptime
        )
        
        logger.info(f"Health check completed: {overall_status.value} ({len(valid_checks)} checks)")
        
        return system_health
    
    async def get_readiness_check(self) -> Dict[str, Any]:
        """Perform readiness check for Kubernetes/container orchestration."""
        try:
            # Check critical services only
            db_check = await self.check_database(timeout=2.0)
            redis_check = await self.check_redis(timeout=2.0)
            
            if db_check.status == HealthStatus.HEALTHY and redis_check.status == HealthStatus.HEALTHY:
                return {
                    "status": "ready",
                    "timestamp": time.time(),
                    "checks": {
                        "database": db_check.status.value,
                        "redis": redis_check.status.value
                    }
                }
            else:
                return {
                    "status": "not_ready",
                    "timestamp": time.time(),
                    "checks": {
                        "database": db_check.status.value,
                        "redis": redis_check.status.value
                    }
                }
        except Exception as exc:
            logger.error(f"Readiness check failed: {str(exc)}")
            return {
                "status": "not_ready",
                "timestamp": time.time(),
                "error": str(exc)
            }
    
    async def get_liveness_check(self) -> Dict[str, Any]:
        """Perform liveness check for Kubernetes/container orchestration."""
        try:
            # Simple check that the application is running
            return {
                "status": "alive",
                "timestamp": time.time(),
                "uptime_seconds": time.time() - self.start_time,
                "version": self.version
            }
        except Exception as exc:
            logger.error(f"Liveness check failed: {str(exc)}")
            return {
                "status": "not_alive",
                "timestamp": time.time(),
                "error": str(exc)
            }