"""
Configuration settings for Kiro-mini backend.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database settings - Using SQLite only
    DATABASE_URL: str = "sqlite:///./kiro_mini.db"
    
    # Redis settings (fallback to local if not available)
    redis_url: str = "redis://localhost:6379/0"
    
    # External service URLs
    orthanc_url: str = "http://localhost:8042"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    # Security settings
    secret_key: str = "kiro-mini-secret-key-change-in-production"
    jwt_secret: str = "kiro-mini-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Application settings
    debug: bool = True
    log_level: str = "INFO"
    
    # DICOM settings
    dicom_aet: str = "KIRO-MINI"
    dicom_port: int = 4242
    
    # AI processing settings
    ai_processing_timeout: int = 10
    max_concurrent_jobs: int = 5
    
    # Billing settings
    default_provider_npi: str = "1234567890"
    default_facility_name: str = "Kiro Medical Center"
    default_facility_address: str = "123 Medical Drive, Healthcare City, HC 12345"
    
    # Storage settings
    storage_dir: str = "./uploads"
    
    # Performance settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    redis_pool_size: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields in the .env file

# Create settings instance
settings = Settings()

# Database configuration for SQLite
DATABASE_CONFIG = {
    "echo": settings.debug,
    "connect_args": {"check_same_thread": False}  # SQLite specific
}

# Redis configuration
REDIS_CONFIG = {
    "max_connections": settings.redis_pool_size,
    "retry_on_timeout": True,
    "socket_keepalive": True,
    "socket_keepalive_options": {},
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "detailed": {
            "formatter": "detailed",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": settings.log_level,
        "handlers": ["default"],
    },
    "loggers": {
        "kiro-mini": {
            "level": settings.log_level,
            "handlers": ["detailed"],
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "level": "INFO" if settings.debug else "WARNING",
            "handlers": ["default"],
            "propagate": False,
        },
    },
}