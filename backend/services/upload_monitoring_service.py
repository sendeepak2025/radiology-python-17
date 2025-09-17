"""
Upload Monitoring Service
Provides comprehensive monitoring, logging, and metrics collection for file uploads.
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@dataclass
class UploadMetrics:
    """Metrics for a single upload operation."""
    upload_id: str
    patient_id: str
    filename: str
    file_size: int
    file_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    bytes_processed: int = 0
    processing_stages: Dict[str, float] = None
    network_info: Dict[str, Any] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    def __post_init__(self):
        if self.processing_stages is None:
            self.processing_stages = {}
        if self.network_info is None:
            self.network_info = {}

@dataclass
class UploadHealthMetrics:
    """System-wide upload health metrics."""
    timestamp: datetime
    total_uploads: int
    successful_uploads: int
    failed_uploads: int
    average_upload_time: float
    average_file_size: float
    error_rate: float
    throughput_mbps: float
    active_uploads: int
    queue_size: int
    system_load: Dict[str, float]

class UploadMonitoringService:
    """Service for monitoring and logging upload operations."""
    
    def __init__(self):
        self.active_uploads: Dict[str, UploadMetrics] = {}
        self.completed_uploads: List[UploadMetrics] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.max_history_size = 1000
        
        # Performance tracking
        self.upload_times: List[float] = []
        self.file_sizes: List[int] = []
        self.throughput_samples: List[float] = []
        
        # System health
        self.last_health_check = datetime.utcnow()
        self.health_check_interval = timedelta(minutes=5)
        
    @asynccontextmanager
    async def monitor_upload(
        self, 
        upload_id: str, 
        patient_id: str, 
        filename: str, 
        file_size: int,
        request_info: Optional[Dict[str, Any]] = None
    ):
        """Context manager for monitoring an upload operation."""
        
        # Create upload metrics
        metrics = UploadMetrics(
            upload_id=upload_id,
            patient_id=patient_id,
            filename=filename,
            file_size=file_size,
            file_type=self._get_file_type(filename),
            start_time=datetime.utcnow(),
            user_agent=request_info.get('user_agent') if request_info else None,
            ip_address=request_info.get('ip_address') if request_info else None
        )
        
        # Add to active uploads
        self.active_uploads[upload_id] = metrics
        
        logger.info(f"📤 Starting upload monitoring: {upload_id} - {filename} ({file_size} bytes)")
        
        try:
            # Start timing
            start_time = time.time()
            
            yield metrics
            
            # Upload completed successfully
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            metrics.end_time = datetime.utcnow()
            metrics.duration_ms = duration_ms
            metrics.success = True
            metrics.bytes_processed = file_size
            
            # Calculate throughput
            if duration_ms > 0:
                throughput_mbps = (file_size / (1024 * 1024)) / (duration_ms / 1000)
                self.throughput_samples.append(throughput_mbps)
                
                # Keep only recent samples
                if len(self.throughput_samples) > 100:
                    self.throughput_samples = self.throughput_samples[-100:]
            
            # Track performance metrics
            self.upload_times.append(duration_ms)
            self.file_sizes.append(file_size)
            
            # Keep only recent samples
            if len(self.upload_times) > 100:
                self.upload_times = self.upload_times[-100:]
                self.file_sizes = self.file_sizes[-100:]
            
            logger.info(f"✅ Upload completed: {upload_id} - {duration_ms}ms")
            
        except Exception as error:
            # Upload failed
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            metrics.end_time = datetime.utcnow()
            metrics.duration_ms = duration_ms
            metrics.success = False
            metrics.error_message = str(error)
            metrics.error_type = type(error).__name__
            
            # Track error
            self.error_counts[metrics.error_type] += 1
            
            logger.error(f"❌ Upload failed: {upload_id} - {error}")
            
            # Re-raise the exception
            raise
            
        finally:
            # Move to completed uploads
            if upload_id in self.active_uploads:
                completed_metrics = self.active_uploads.pop(upload_id)
                self.completed_uploads.append(completed_metrics)
                
                # Keep history size manageable
                if len(self.completed_uploads) > self.max_history_size:
                    self.completed_uploads = self.completed_uploads[-self.max_history_size:]
    
    def log_upload_stage(self, upload_id: str, stage: str, duration_ms: float):
        """Log the duration of a specific upload stage."""
        if upload_id in self.active_uploads:
            self.active_uploads[upload_id].processing_stages[stage] = duration_ms
            logger.debug(f"📊 Upload stage: {upload_id} - {stage}: {duration_ms}ms")
    
    def update_upload_progress(self, upload_id: str, bytes_processed: int):
        """Update the progress of an active upload."""
        if upload_id in self.active_uploads:
            self.active_uploads[upload_id].bytes_processed = bytes_processed
            
            # Calculate progress percentage
            metrics = self.active_uploads[upload_id]
            progress = (bytes_processed / metrics.file_size) * 100 if metrics.file_size > 0 else 0
            
            logger.debug(f"📈 Upload progress: {upload_id} - {progress:.1f}%")
    
    def get_upload_status(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an upload."""
        if upload_id in self.active_uploads:
            metrics = self.active_uploads[upload_id]
            elapsed_ms = int((datetime.utcnow() - metrics.start_time).total_seconds() * 1000)
            progress = (metrics.bytes_processed / metrics.file_size) * 100 if metrics.file_size > 0 else 0
            
            return {
                'upload_id': upload_id,
                'status': 'active',
                'progress': progress,
                'elapsed_ms': elapsed_ms,
                'bytes_processed': metrics.bytes_processed,
                'file_size': metrics.file_size,
                'filename': metrics.filename
            }
        
        # Check completed uploads
        for metrics in reversed(self.completed_uploads):
            if metrics.upload_id == upload_id:
                return {
                    'upload_id': upload_id,
                    'status': 'completed' if metrics.success else 'failed',
                    'progress': 100 if metrics.success else 0,
                    'duration_ms': metrics.duration_ms,
                    'success': metrics.success,
                    'error_message': metrics.error_message,
                    'filename': metrics.filename
                }
        
        return None
    
    def get_health_metrics(self) -> UploadHealthMetrics:
        """Get current system health metrics."""
        now = datetime.utcnow()
        
        # Get recent uploads (last hour)
        recent_uploads = [
            m for m in self.completed_uploads 
            if m.end_time and (now - m.end_time).total_seconds() < 3600
        ]
        
        total_uploads = len(recent_uploads)
        successful_uploads = len([m for m in recent_uploads if m.success])
        failed_uploads = total_uploads - successful_uploads
        
        # Calculate averages
        avg_upload_time = 0
        avg_file_size = 0
        if recent_uploads:
            avg_upload_time = sum(m.duration_ms or 0 for m in recent_uploads) / len(recent_uploads)
            avg_file_size = sum(m.file_size for m in recent_uploads) / len(recent_uploads)
        
        # Calculate error rate
        error_rate = (failed_uploads / total_uploads) * 100 if total_uploads > 0 else 0
        
        # Calculate throughput
        throughput_mbps = sum(self.throughput_samples) / len(self.throughput_samples) if self.throughput_samples else 0
        
        # System load (simplified)
        system_load = {
            'active_uploads': len(self.active_uploads),
            'memory_usage': 0,  # Would be implemented with actual system monitoring
            'cpu_usage': 0,     # Would be implemented with actual system monitoring
            'disk_usage': 0     # Would be implemented with actual system monitoring
        }
        
        return UploadHealthMetrics(
            timestamp=now,
            total_uploads=total_uploads,
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            average_upload_time=avg_upload_time,
            average_file_size=avg_file_size,
            error_rate=error_rate,
            throughput_mbps=throughput_mbps,
            active_uploads=len(self.active_uploads),
            queue_size=0,  # Would be implemented with actual queue monitoring
            system_load=system_load
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns."""
        total_errors = sum(self.error_counts.values())
        
        # Get recent errors (last 24 hours)
        recent_errors = [
            m for m in self.completed_uploads 
            if not m.success and m.end_time and 
            (datetime.utcnow() - m.end_time).total_seconds() < 86400
        ]
        
        # Group errors by type
        error_types = defaultdict(int)
        for error in recent_errors:
            if error.error_type:
                error_types[error.error_type] += 1
        
        # Get error patterns
        error_patterns = []
        for error_type, count in error_types.items():
            if count > 1:  # Only include patterns with multiple occurrences
                error_patterns.append({
                    'error_type': error_type,
                    'count': count,
                    'percentage': (count / len(recent_errors)) * 100 if recent_errors else 0
                })
        
        return {
            'total_errors': total_errors,
            'recent_errors': len(recent_errors),
            'error_types': dict(error_types),
            'error_patterns': error_patterns,
            'most_common_error': max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and trends."""
        if not self.upload_times:
            return {
                'average_upload_time': 0,
                'median_upload_time': 0,
                'p95_upload_time': 0,
                'average_throughput': 0,
                'peak_throughput': 0
            }
        
        # Sort for percentile calculations
        sorted_times = sorted(self.upload_times)
        sorted_throughput = sorted(self.throughput_samples) if self.throughput_samples else [0]
        
        return {
            'average_upload_time': sum(self.upload_times) / len(self.upload_times),
            'median_upload_time': sorted_times[len(sorted_times) // 2],
            'p95_upload_time': sorted_times[int(len(sorted_times) * 0.95)],
            'average_throughput': sum(sorted_throughput) / len(sorted_throughput),
            'peak_throughput': max(sorted_throughput),
            'total_data_processed': sum(self.file_sizes),
            'average_file_size': sum(self.file_sizes) / len(self.file_sizes)
        }
    
    def log_diagnostic_info(self, upload_id: str, info: Dict[str, Any]):
        """Log diagnostic information for an upload."""
        logger.info(f"🔍 Upload diagnostics: {upload_id} - {json.dumps(info, default=str)}")
        
        if upload_id in self.active_uploads:
            self.active_uploads[upload_id].network_info.update(info)
    
    def clear_old_data(self, max_age_hours: int = 24):
        """Clear old monitoring data to prevent memory leaks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Remove old completed uploads
        self.completed_uploads = [
            m for m in self.completed_uploads 
            if m.end_time and m.end_time > cutoff_time
        ]
        
        logger.info(f"🧹 Cleared old monitoring data (older than {max_age_hours} hours)")
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename."""
        extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        
        type_mapping = {
            'dcm': 'DICOM',
            'dicom': 'DICOM',
            'pdf': 'PDF',
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'png': 'PNG',
            'txt': 'Text'
        }
        
        return type_mapping.get(extension, extension.upper())

# Global instance
upload_monitoring_service = UploadMonitoringService()