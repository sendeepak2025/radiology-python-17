"""
Redis service for job queue and caching operations.
"""

import logging
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid

from config import settings

logger = logging.getLogger(__name__)

class RedisService:
    """Service for Redis operations including job queue management."""
    
    def __init__(self):
        self.redis_url = settings.redis_url
        self.pool = None
        self.redis_client = None
    
    async def connect(self):
        """Initialize Redis connection pool with fallback."""
        try:
            self.pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=settings.redis_pool_size,
                retry_on_timeout=True
            )
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Using fallback mode.")
            # Import and use fallback service
            from redis_fallback import redis_fallback
            self.redis_client = redis_fallback
            await self.redis_client.connect()
    
    async def disconnect(self):
        """Close Redis connections."""
        if self.redis_client:
            await self.redis_client.close()
        if self.pool:
            await self.pool.disconnect()
    
    async def enqueue_job(
        self,
        queue_name: str,
        job_data: Dict[str, Any],
        priority: int = 0,
        delay: Optional[int] = None
    ) -> str:
        """
        Enqueue a job for processing.
        
        Args:
            queue_name: Name of the queue
            job_data: Job payload data
            priority: Job priority (higher = more priority)
            delay: Delay in seconds before job becomes available
        
        Returns:
            Job ID
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            job_id = str(uuid.uuid4())
            
            job_payload = {
                "job_id": job_id,
                "queue": queue_name,
                "data": job_data,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "status": "queued"
            }
            
            if delay:
                # Schedule job for later execution
                execute_at = datetime.utcnow() + timedelta(seconds=delay)
                job_payload["execute_at"] = execute_at.isoformat()
                
                # Add to delayed jobs set
                await self.redis_client.zadd(
                    f"{queue_name}:delayed",
                    {json.dumps(job_payload): execute_at.timestamp()}
                )
            else:
                # Add to immediate queue with priority
                await self.redis_client.zadd(
                    f"{queue_name}:queue",
                    {json.dumps(job_payload): priority}
                )
            
            # Store job details
            await self.redis_client.hset(
                f"job:{job_id}",
                mapping={
                    "payload": json.dumps(job_payload),
                    "status": "queued",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Set job expiration (24 hours)
            await self.redis_client.expire(f"job:{job_id}", 86400)
            
            logger.info(f"Job {job_id} enqueued to {queue_name}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error enqueueing job: {str(e)}")
            raise
    
    async def dequeue_job(self, queue_name: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Dequeue a job for processing.
        
        Args:
            queue_name: Name of the queue
            timeout: Timeout in seconds for blocking operation
        
        Returns:
            Job data or None if no jobs available
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            # First, move any ready delayed jobs to the main queue
            await self._process_delayed_jobs(queue_name)
            
            # Get highest priority job from queue
            result = await self.redis_client.bzpopmax(
                f"{queue_name}:queue",
                timeout=timeout
            )
            
            if not result:
                return None
            
            queue_key, job_json, priority = result
            job_data = json.loads(job_json)
            job_id = job_data["job_id"]
            
            # Update job status
            await self.redis_client.hset(
                f"job:{job_id}",
                mapping={
                    "status": "processing",
                    "started_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Job {job_id} dequeued from {queue_name}")
            return job_data
            
        except Exception as e:
            logger.error(f"Error dequeuing job: {str(e)}")
            return None
    
    async def _process_delayed_jobs(self, queue_name: str):
        """Move ready delayed jobs to the main queue."""
        try:
            current_time = datetime.utcnow().timestamp()
            
            # Get jobs that are ready to execute
            ready_jobs = await self.redis_client.zrangebyscore(
                f"{queue_name}:delayed",
                0,
                current_time,
                withscores=True
            )
            
            for job_json, score in ready_jobs:
                job_data = json.loads(job_json)
                
                # Move to main queue
                await self.redis_client.zadd(
                    f"{queue_name}:queue",
                    {job_json: job_data["priority"]}
                )
                
                # Remove from delayed queue
                await self.redis_client.zrem(f"{queue_name}:delayed", job_json)
                
        except Exception as e:
            logger.error(f"Error processing delayed jobs: {str(e)}")
    
    async def complete_job(
        self,
        job_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Mark a job as completed or failed.
        
        Args:
            job_id: Job ID
            result: Job result data (if successful)
            error: Error message (if failed)
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            status = "failed" if error else "completed"
            
            update_data = {
                "status": status,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            if result:
                update_data["result"] = json.dumps(result)
            
            if error:
                update_data["error"] = error
            
            await self.redis_client.hset(f"job:{job_id}", mapping=update_data)
            
            logger.info(f"Job {job_id} marked as {status}")
            
        except Exception as e:
            logger.error(f"Error completing job {job_id}: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details."""
        try:
            if not self.redis_client:
                await self.connect()
            
            job_data = await self.redis_client.hgetall(f"job:{job_id}")
            
            if not job_data:
                return None
            
            # Convert bytes to strings
            result = {}
            for key, value in job_data.items():
                key_str = key.decode() if isinstance(key, bytes) else key
                value_str = value.decode() if isinstance(value, bytes) else value
                result[key_str] = value_str
            
            # Parse JSON fields
            if "payload" in result:
                result["payload"] = json.loads(result["payload"])
            if "result" in result:
                result["result"] = json.loads(result["result"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {str(e)}")
            return None
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """Get queue statistics."""
        try:
            if not self.redis_client:
                await self.connect()
            
            # Count jobs in different states
            queued_count = await self.redis_client.zcard(f"{queue_name}:queue")
            delayed_count = await self.redis_client.zcard(f"{queue_name}:delayed")
            
            # Get processing jobs (approximate)
            processing_pattern = f"job:*"
            processing_count = 0
            
            async for key in self.redis_client.scan_iter(match=processing_pattern):
                job_data = await self.redis_client.hget(key, "status")
                if job_data and job_data.decode() == "processing":
                    processing_count += 1
            
            return {
                "queue_name": queue_name,
                "queued": queued_count,
                "delayed": delayed_count,
                "processing": processing_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {}
    
    async def set_cache(
        self,
        key: str,
        value: Any,
        expiration: Optional[int] = None
    ):
        """Set a cache value."""
        try:
            if not self.redis_client:
                await self.connect()
            
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            
            if expiration:
                await self.redis_client.setex(key, expiration, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
                
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            raise
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get a cache value."""
        try:
            if not self.redis_client:
                await self.connect()
            
            value = await self.redis_client.get(key)
            
            if value is None:
                return None
            
            value_str = value.decode() if isinstance(value, bytes) else value
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    async def delete_cache(self, key: str):
        """Delete a cache key."""
        try:
            if not self.redis_client:
                await self.connect()
            
            await self.redis_client.delete(key)
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            if not self.redis_client:
                await self.connect()
            
            await self.redis_client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False