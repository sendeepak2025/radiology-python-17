"""
Logging Configuration for Upload Monitoring
Provides structured logging with different levels and output formats.
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'upload_id'):
            log_entry['upload_id'] = record.upload_id
        if hasattr(record, 'patient_id'):
            log_entry['patient_id'] = record.patient_id
        if hasattr(record, 'filename'):
            log_entry['filename'] = record.filename
        if hasattr(record, 'file_size'):
            log_entry['file_size'] = record.file_size
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        
        return json.dumps(log_entry, default=str)

class UploadLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds upload context to log records."""
    
    def process(self, msg, kwargs):
        # Add extra context to the log record
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs

def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/upload_monitoring.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_structured: bool = True
) -> None:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console logging
        enable_structured: Whether to use structured JSON logging
    """
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if enable_structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Use simpler format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ) if not enable_structured else formatter
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    
    # Upload monitoring logger
    upload_logger = logging.getLogger('upload_monitoring')
    upload_logger.setLevel(logging.DEBUG)
    
    # File upload service logger
    file_upload_logger = logging.getLogger('file_upload_service')
    file_upload_logger.setLevel(logging.DEBUG)
    
    # Patient routes logger
    patient_routes_logger = logging.getLogger('patient_routes')
    patient_routes_logger.setLevel(logging.DEBUG)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    logging.info(f"Logging configured - Level: {log_level}, File: {log_file}, Structured: {enable_structured}")

def get_upload_logger(upload_id: str = None, patient_id: str = None) -> UploadLoggerAdapter:
    """
    Get a logger adapter with upload context.
    
    Args:
        upload_id: Upload ID to include in logs
        patient_id: Patient ID to include in logs
    
    Returns:
        Logger adapter with upload context
    """
    logger = logging.getLogger('upload_monitoring')
    
    extra_context = {}
    if upload_id:
        extra_context['upload_id'] = upload_id
    if patient_id:
        extra_context['patient_id'] = patient_id
    
    return UploadLoggerAdapter(logger, extra_context)

def log_upload_event(
    event_type: str,
    upload_id: str,
    patient_id: str,
    filename: str = None,
    file_size: int = None,
    duration_ms: int = None,
    error_type: str = None,
    additional_data: Dict[str, Any] = None
) -> None:
    """
    Log a structured upload event.
    
    Args:
        event_type: Type of event (start, progress, complete, error)
        upload_id: Upload ID
        patient_id: Patient ID
        filename: Name of the file
        file_size: Size of the file in bytes
        duration_ms: Duration in milliseconds
        error_type: Type of error if applicable
        additional_data: Additional data to include in the log
    """
    logger = get_upload_logger(upload_id, patient_id)
    
    extra = {
        'event_type': event_type,
        'upload_id': upload_id,
        'patient_id': patient_id
    }
    
    if filename:
        extra['filename'] = filename
    if file_size is not None:
        extra['file_size'] = file_size
    if duration_ms is not None:
        extra['duration_ms'] = duration_ms
    if error_type:
        extra['error_type'] = error_type
    if additional_data:
        extra.update(additional_data)
    
    message = f"Upload {event_type}: {upload_id}"
    if filename:
        message += f" - {filename}"
    
    if event_type == 'error':
        logger.error(message, extra=extra)
    elif event_type == 'warning':
        logger.warning(message, extra=extra)
    else:
        logger.info(message, extra=extra)

# Performance monitoring decorator
def log_performance(func):
    """Decorator to log function performance."""
    import functools
    import time
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = f"{func.__module__}.{func.__name__}"
        
        logger = logging.getLogger('performance')
        logger.debug(f"Starting {function_name}")
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Completed {function_name}",
                extra={
                    'function': function_name,
                    'duration_ms': duration_ms,
                    'status': 'success'
                }
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Failed {function_name}: {str(e)}",
                extra={
                    'function': function_name,
                    'duration_ms': duration_ms,
                    'status': 'error',
                    'error_type': type(e).__name__
                }
            )
            
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = f"{func.__module__}.{func.__name__}"
        
        logger = logging.getLogger('performance')
        logger.debug(f"Starting {function_name}")
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Completed {function_name}",
                extra={
                    'function': function_name,
                    'duration_ms': duration_ms,
                    'status': 'success'
                }
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Failed {function_name}: {str(e)}",
                extra={
                    'function': function_name,
                    'duration_ms': duration_ms,
                    'status': 'error',
                    'error_type': type(e).__name__
                }
            )
            
            raise
    
    # Return appropriate wrapper based on whether function is async
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper