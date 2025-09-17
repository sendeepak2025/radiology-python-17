"""
Performance monitoring and metrics collection service.
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import psutil
import json

from services.redis_service import RedisService
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""
    timestamp: str
    total_studies: int
    studies_today: int
    total_reports: int
    reports_today: int
    avg_report_time: float
    ai_processing_queue_size: int
    active_users: int
    error_rate: float
    response_time_avg: float

@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    id: str
    type: str
    severity: str
    message: str
    threshold: float
    current_value: float
    timestamp: str
    resolved: bool = False

class SimpleMetricsCollector:
    """Simple metrics collector for testing."""
    
    def __init__(self):
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
    
    def increment_counter(self, name: str, value: float):
        """Increment a counter metric."""
        self.counters[name] = self.counters.get(name, 0) + value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric."""
        self.gauges[name] = value
    
    def record_histogram(self, name: str, value: float):
        """Record a histogram value."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)

class SimplePerformanceMonitor:
    """Simple performance monitor for testing."""
    
    def __init__(self):
        self.requests = []
    
    def record_request(self, response_time: float, status_code: int, endpoint: str):
        """Record a request."""
        self.requests.append({
            'response_time': response_time,
            'status_code': status_code,
            'endpoint': endpoint,
            'timestamp': datetime.utcnow()
        })
    
    def get_performance_metrics(self, window_seconds: int):
        """Get performance metrics for a time window."""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        recent_requests = [r for r in self.requests if r['timestamp'] > cutoff]
        
        if not recent_requests:
            return type('PerformanceMetrics', (), {'avg_response_time': 0.0})()
        
        avg_response_time = sum(r['response_time'] for r in recent_requests) / len(recent_requests)
        return type('PerformanceMetrics', (), {'avg_response_time': avg_response_time})()

class MonitoringService:
    """Service for system and application monitoring."""
    
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate': 5.0,
            'response_time_avg': 2000.0,  # milliseconds
            'queue_size': 100
        }
        self.metrics_history = []
        self.active_alerts = {}
        
        # Add the required attributes for testing
        self.metrics_collector = SimpleMetricsCollector()
        self.performance_monitor = SimplePerformanceMonitor()
        
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                # Windows doesn't have load average
                load_avg = [0.0, 0.0, 0.0]
            
            # Active connections
            connections = len(psutil.net_connections())
            
            return SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=round(memory_used_gb, 2),
                memory_total_gb=round(memory_total_gb, 2),
                disk_percent=disk.percent,
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_connections=connections,
                load_average=load_avg
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            raise
    
    async def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics."""
        try:
            db = next(get_db())
            
            # Database queries for application metrics
            total_studies = db.execute(text("SELECT COUNT(*) FROM studies")).scalar()
            studies_today = db.execute(text(
                "SELECT COUNT(*) FROM studies WHERE DATE(created_at) = CURRENT_DATE"
            )).scalar()
            
            total_reports = db.execute(text("SELECT COUNT(*) FROM reports")).scalar()
            reports_today = db.execute(text(
                "SELECT COUNT(*) FROM reports WHERE DATE(created_at) = CURRENT_DATE"
            )).scalar()
            
            # Average report generation time (in seconds)
            avg_time_result = db.execute(text("""
                SELECT AVG(EXTRACT(EPOCH FROM (finalized_at - created_at)))
                FROM reports 
                WHERE finalized_at IS NOT NULL 
                AND created_at >= NOW() - INTERVAL '24 hours'
            """)).scalar()
            avg_report_time = float(avg_time_result or 0)
            
            # Queue metrics
            queue_stats = await self.redis_service.get_queue_stats("ai_processing")
            queue_size = queue_stats.get("queued", 0) + queue_stats.get("processing", 0)
            
            # Active users (from Redis sessions)
            active_users = await self._count_active_users()
            
            # Error rate (from recent logs)
            error_rate = await self._calculate_error_rate()
            
            # Response time average (from cached metrics)
            response_time_avg = await self._get_avg_response_time()
            
            db.close()
            
            return ApplicationMetrics(
                timestamp=datetime.utcnow().isoformat(),
                total_studies=total_studies or 0,
                studies_today=studies_today or 0,
                total_reports=total_reports or 0,
                reports_today=reports_today or 0,
                avg_report_time=avg_report_time,
                ai_processing_queue_size=queue_size,
                active_users=active_users,
                error_rate=error_rate,
                response_time_avg=response_time_avg
            )
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {str(e)}")
            raise
    
    async def _count_active_users(self) -> int:
        """Count active users from Redis sessions."""
        try:
            # Count active sessions (sessions updated in last 30 minutes)
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)
            
            # This would depend on your session management implementation
            # For now, return a mock value
            return 5  # Mock active users
            
        except Exception as e:
            logger.error(f"Error counting active users: {str(e)}")
            return 0
    
    async def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent requests."""
        try:
            # Get error count from Redis cache
            error_count = await self.redis_service.get_cache("error_count_1h") or 0
            total_requests = await self.redis_service.get_cache("request_count_1h") or 1
            
            return (error_count / total_requests) * 100 if total_requests > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {str(e)}")
            return 0.0
    
    async def _get_avg_response_time(self) -> float:
        """Get average response time from cached metrics."""
        try:
            avg_time = await self.redis_service.get_cache("avg_response_time_1h") or 0
            return float(avg_time)
            
        except Exception as e:
            logger.error(f"Error getting average response time: {str(e)}")
            return 0.0
    
    async def check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Check for performance alerts based on thresholds."""
        try:
            alerts = []
            
            # System alerts
            if system_metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
                alerts.append(PerformanceAlert(
                    id=f"cpu_high_{int(time.time())}",
                    type="system",
                    severity="warning",
                    message=f"High CPU usage: {system_metrics.cpu_percent:.1f}%",
                    threshold=self.alert_thresholds['cpu_percent'],
                    current_value=system_metrics.cpu_percent,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            if system_metrics.memory_percent > self.alert_thresholds['memory_percent']:
                alerts.append(PerformanceAlert(
                    id=f"memory_high_{int(time.time())}",
                    type="system",
                    severity="warning",
                    message=f"High memory usage: {system_metrics.memory_percent:.1f}%",
                    threshold=self.alert_thresholds['memory_percent'],
                    current_value=system_metrics.memory_percent,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            if system_metrics.disk_percent > self.alert_thresholds['disk_percent']:
                alerts.append(PerformanceAlert(
                    id=f"disk_high_{int(time.time())}",
                    type="system",
                    severity="critical",
                    message=f"High disk usage: {system_metrics.disk_percent:.1f}%",
                    threshold=self.alert_thresholds['disk_percent'],
                    current_value=system_metrics.disk_percent,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            # Application alerts
            if app_metrics.error_rate > self.alert_thresholds['error_rate']:
                alerts.append(PerformanceAlert(
                    id=f"error_rate_high_{int(time.time())}",
                    type="application",
                    severity="warning",
                    message=f"High error rate: {app_metrics.error_rate:.1f}%",
                    threshold=self.alert_thresholds['error_rate'],
                    current_value=app_metrics.error_rate,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            if app_metrics.response_time_avg > self.alert_thresholds['response_time_avg']:
                alerts.append(PerformanceAlert(
                    id=f"response_time_high_{int(time.time())}",
                    type="application",
                    severity="warning",
                    message=f"High response time: {app_metrics.response_time_avg:.0f}ms",
                    threshold=self.alert_thresholds['response_time_avg'],
                    current_value=app_metrics.response_time_avg,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            if app_metrics.ai_processing_queue_size > self.alert_thresholds['queue_size']:
                alerts.append(PerformanceAlert(
                    id=f"queue_size_high_{int(time.time())}",
                    type="application",
                    severity="warning",
                    message=f"Large AI processing queue: {app_metrics.ai_processing_queue_size} jobs",
                    threshold=self.alert_thresholds['queue_size'],
                    current_value=app_metrics.ai_processing_queue_size,
                    timestamp=datetime.utcnow().isoformat()
                ))
            
            # Store alerts
            for alert in alerts:
                await self._store_alert(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            return []
    
    async def _store_alert(self, alert: PerformanceAlert):
        """Store alert in Redis."""
        try:
            alert_key = f"alert:{alert.id}"
            await self.redis_service.set_cache(
                alert_key,
                asdict(alert),
                expiration=86400  # 24 hours
            )
            
            # Add to active alerts list
            await self.redis_service.redis_client.lpush(
                "active_alerts",
                alert.id
            )
            
            # Limit active alerts list to 100 items
            await self.redis_service.redis_client.ltrim("active_alerts", 0, 99)
            
            logger.warning(f"Alert generated: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")
    
    async def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get all active alerts."""
        try:
            alert_ids = await self.redis_service.redis_client.lrange("active_alerts", 0, -1)
            alerts = []
            
            for alert_id in alert_ids:
                alert_id_str = alert_id.decode() if isinstance(alert_id, bytes) else alert_id
                alert_data = await self.redis_service.get_cache(f"alert:{alert_id_str}")
                
                if alert_data:
                    alerts.append(PerformanceAlert(**alert_data))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    async def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved."""
        try:
            alert_data = await self.redis_service.get_cache(f"alert:{alert_id}")
            
            if alert_data:
                alert_data['resolved'] = True
                alert_data['resolved_at'] = datetime.utcnow().isoformat()
                
                await self.redis_service.set_cache(
                    f"alert:{alert_id}",
                    alert_data,
                    expiration=86400
                )
                
                # Remove from active alerts
                await self.redis_service.redis_client.lrem("active_alerts", 0, alert_id)
                
                logger.info(f"Alert {alert_id} resolved")
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {str(e)}")
    
    async def store_metrics(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Store metrics in Redis for historical analysis."""
        try:
            timestamp = datetime.utcnow()
            
            # Store current metrics
            await self.redis_service.set_cache(
                "current_system_metrics",
                asdict(system_metrics),
                expiration=300  # 5 minutes
            )
            
            await self.redis_service.set_cache(
                "current_app_metrics",
                asdict(app_metrics),
                expiration=300  # 5 minutes
            )
            
            # Store historical metrics (time series)
            metrics_key = f"metrics:{timestamp.strftime('%Y-%m-%d:%H')}"
            historical_data = {
                "system": asdict(system_metrics),
                "application": asdict(app_metrics)
            }
            
            await self.redis_service.set_cache(
                metrics_key,
                historical_data,
                expiration=604800  # 7 days
            )
            
            # Add to metrics timeline
            await self.redis_service.redis_client.zadd(
                "metrics_timeline",
                {metrics_key: timestamp.timestamp()}
            )
            
            # Keep only last 168 hours (7 days) of metrics
            cutoff_time = timestamp - timedelta(days=7)
            await self.redis_service.redis_client.zremrangebyscore(
                "metrics_timeline",
                0,
                cutoff_time.timestamp()
            )
            
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")
    
    async def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for the specified number of hours."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get metrics keys in time range
            metrics_keys = await self.redis_service.redis_client.zrangebyscore(
                "metrics_timeline",
                start_time.timestamp(),
                end_time.timestamp()
            )
            
            history = []
            for key in metrics_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                metrics_data = await self.redis_service.get_cache(key_str)
                
                if metrics_data:
                    history.append(metrics_data)
            
            return sorted(history, key=lambda x: x['system']['timestamp'])
            
        except Exception as e:
            logger.error(f"Error getting metrics history: {str(e)}")
            return []
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for dashboard."""
        try:
            # Get current metrics
            system_metrics = await self.redis_service.get_cache("current_system_metrics")
            app_metrics = await self.redis_service.get_cache("current_app_metrics")
            
            # Get active alerts
            active_alerts = await self.get_active_alerts()
            
            # Get queue statistics
            queue_stats = await self.redis_service.get_queue_stats("ai_processing")
            
            # Calculate uptime (mock for now)
            uptime_hours = 24.5  # Mock uptime
            
            return {
                "system": system_metrics,
                "application": app_metrics,
                "alerts": {
                    "active_count": len(active_alerts),
                    "alerts": [asdict(alert) for alert in active_alerts[:5]]  # Top 5 alerts
                },
                "queue": queue_stats,
                "uptime_hours": uptime_hours,
                "health_status": "healthy" if len(active_alerts) == 0 else "warning",
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {str(e)}")
            return {}
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        try:
            summary = {
                "counters": self.metrics_collector.counters,
                "gauges": self.metrics_collector.gauges,
                "histograms": {k: len(v) for k, v in self.metrics_collector.histograms.items()},
                "performance": {
                    "total_requests": len(self.performance_monitor.requests)
                }
            }
            return summary
        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return {"error": str(e)}
    
    async def run_monitoring_loop(self, interval: int = 60):
        """Run continuous monitoring loop."""
        logger.info(f"Starting monitoring loop with {interval}s interval")
        
        while True:
            try:
                # Collect metrics
                system_metrics = await self.collect_system_metrics()
                app_metrics = await self.collect_application_metrics()
                
                # Store metrics
                await self.store_metrics(system_metrics, app_metrics)
                
                # Check for alerts
                alerts = await self.check_alerts(system_metrics, app_metrics)
                
                if alerts:
                    logger.warning(f"Generated {len(alerts)} new alerts")
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(interval)

# Global monitoring service instance
monitoring_service = None

async def get_monitoring_service() -> MonitoringService:
    """Get monitoring service instance."""
    global monitoring_service
    
    if monitoring_service is None:
        from services.redis_service import RedisService
        redis_service = RedisService()
        await redis_service.connect()
        monitoring_service = MonitoringService(redis_service)
    
    return monitoring_service

class MetricsCollector:
    """Simplified metrics collector for testing purposes."""
    
    def __init__(self):
        self.metrics = {}
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect basic system metrics."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if hasattr(psutil.disk_usage('/'), 'percent') else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return self.collect_system_metrics()