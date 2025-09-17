"""
Kiro-mini FastAPI Backend with Error Handling and Monitoring
Main application entry point for medical imaging and billing integration system.
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from database import engine, SessionLocal, Base
from models import Study, Report, Superbill, AuditLog
from schemas import (
    StudyIngest, StudyResponse, ReportCreate, ReportResponse,
    SuperbillCreate, SuperbillResponse, HealthResponse
)
from services.study_service import StudyService
from services.report_service import ReportService
from services.billing_service import BillingService
from services.ai_service import AIService
from services.measurement_service import MeasurementService
from services.workflow_service import WorkflowService
from services.realtime_billing_service import RealtimeBillingService
from services.websocket_billing_service import websocket_billing_service
from services.audit_service import AuditService
from services.report_version_service import ReportVersionService
from services.fhir_service import FHIRService
from services.x12_service import X12Service
from services.webhook_service import WebhookService
from services.monitoring_service import MonitoringService
from services.redis_service import RedisService
from middleware.audit_middleware import AuditLoggingMiddleware, HIPAAComplianceMiddleware
from middleware.error_handler import setup_error_handling
from routers import health
from exceptions import KiroException, kiro_exception_to_http_exception
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global monitoring service
monitoring_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with monitoring."""
    global monitoring_service
    
    # Startup
    logger.info("Starting Kiro-mini backend with enhanced error handling and monitoring...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Initialize monitoring service
    redis_service = RedisService()
    monitoring_service = MonitoringService(redis_service)
    await monitoring_service.start_monitoring()
    logger.info("Monitoring service started")
    
    # Initialize services
    app.state.study_service = StudyService()
    app.state.report_service = ReportService()
    app.state.billing_service = BillingService()
    app.state.ai_service = AIService()
    app.state.measurement_service = MeasurementService()
    app.state.workflow_service = WorkflowService()
    app.state.realtime_billing_service = RealtimeBillingService()
    app.state.monitoring_service = monitoring_service
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kiro-mini backend...")


# Create FastAPI application
app = FastAPI(
    title="Kiro-mini API",
    description="Medical Imaging and Billing Integration System with Error Handling and Monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://frontend:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up error handling middleware
enable_debug = os.getenv("DEBUG", "false").lower() == "true"
setup_error_handling(app, enable_debug=enable_debug, log_requests=True)

# Add audit logging middleware
app.add_middleware(AuditLoggingMiddleware)

# Add HIPAA compliance middleware
app.add_middleware(HIPAAComplianceMiddleware)


@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Middleware to collect metrics for monitoring."""
    import time
    
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics if monitoring service is available
    if hasattr(app.state, 'monitoring_service') and app.state.monitoring_service:
        try:
            endpoint = str(request.url.path)
            status_code = response.status_code
            
            app.state.monitoring_service.performance_monitor.record_request(
                duration=duration,
                status_code=status_code,
                endpoint=endpoint
            )
        except Exception as exc:
            logger.warning(f"Failed to record metrics: {exc}")
    
    return response


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Include health check router
app.include_router(health.router)


# Global exception handler for KiroException
@app.exception_handler(KiroException)
async def kiro_exception_handler(request: Request, exc: KiroException):
    """Global exception handler for KiroException."""
    http_exc = kiro_exception_to_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail,
        headers={"X-Request-ID": getattr(request.state, 'request_id', 'unknown')}
    )


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "Kiro-mini API is running with enhanced error handling and monitoring",
        "version": "1.0.0",
        "status": "healthy",
        "features": {
            "ai_assistance": True,
            "fhir_export": True,
            "x12_export": True,
            "webhooks": True,
            "monitoring": True,
            "error_handling": True,
            "audit_logging": True,
            "hipaa_compliance": True
        }
    }


@app.get("/version")
async def get_version():
    """Get application version information."""
    return {
        "version": "1.0.0",
        "build_date": "2024-01-15",
        "commit_hash": os.getenv("COMMIT_HASH", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "error_handling": True,
            "monitoring": True,
            "retry_logic": True,
            "circuit_breakers": True,
            "health_checks": True
        }
    }


# Study Management Endpoints with Error Handling
@app.post("/studies/{study_uid}/ingest")
async def ingest_study(
    study_uid: str,
    study_data: StudyIngest,
    background_tasks: BackgroundTasks,
    db: SessionLocal = Depends(get_db)
):
    """
    Process incoming study metadata from Orthanc webhook.
    Automatically enqueues AI processing job with error handling.
    """
    try:
        logger.info(f"Ingesting study: {study_uid}")
        
        # Create or update study record
        study_service = StudyService()
        study = await study_service.create_or_update_study(db, study_uid, study_data)
        
        # Enqueue AI processing job with retry logic
        ai_service = AIService()
        job_id = await ai_service.enqueue_processing_job(study_uid, study_data.exam_type)
        
        logger.info(f"Study {study_uid} ingested, AI job {job_id} enqueued")
        
        return {
            "status": "success",
            "study_uid": study_uid,
            "ai_job_id": job_id,
            "message": "Study ingested and AI processing started"
        }
        
    except Exception as e:
        logger.error(f"Error ingesting study {study_uid}: {str(e)}")
        raise KiroException(
            message=f"Failed to ingest study: {str(e)}",
            error_code="STUDY_INGESTION_ERROR",
            details={"study_uid": study_uid, "exam_type": study_data.exam_type}
        )


@app.get("/studies/{study_uid}", response_model=StudyResponse)
async def get_study(study_uid: str, db: SessionLocal = Depends(get_db)):
    """Retrieve study metadata and image URLs with error handling."""
    try:
        study_service = StudyService()
        study = await study_service.get_study_with_images(db, study_uid)
        
        if not study:
            raise KiroException(
                message=f"Study not found: {study_uid}",
                error_code="STUDY_NOT_FOUND",
                details={"study_uid": study_uid}
            )
        
        return study
        
    except KiroException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving study {study_uid}: {str(e)}")
        raise KiroException(
            message=f"Failed to retrieve study: {str(e)}",
            error_code="STUDY_RETRIEVAL_ERROR",
            details={"study_uid": study_uid}
        )


# Report Management Endpoints with Error Handling
@app.post("/reports", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: SessionLocal = Depends(get_db)
):
    """Create or update a structured report with AI assistance and error handling."""
    try:
        report_service = ReportService()
        
        # Create/update report
        report = await report_service.create_or_update_report(db, report_data)
        
        # If report is finalized, trigger billing generation
        if report_data.status == "final":
            billing_service = BillingService()
            background_tasks.add_task(
                billing_service.generate_superbill_async,
                db, report.report_id
            )
        
        return report
        
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        raise KiroException(
            message=f"Failed to create report: {str(e)}",
            error_code="REPORT_CREATION_ERROR",
            details={"study_uid": report_data.study_uid, "exam_type": report_data.exam_type}
        )


# Billing Endpoints with Error Handling
@app.post("/superbills", response_model=SuperbillResponse)
async def generate_superbill(
    superbill_data: SuperbillCreate,
    db: SessionLocal = Depends(get_db)
):
    """Generate superbill and 837P payload from report with error handling."""
    try:
        billing_service = BillingService()
        superbill = await billing_service.generate_superbill(db, superbill_data.report_id)
        
        return superbill
        
    except Exception as e:
        logger.error(f"Error generating superbill: {str(e)}")
        raise KiroException(
            message=f"Failed to generate superbill: {str(e)}",
            error_code="SUPERBILL_GENERATION_ERROR",
            details={"report_id": superbill_data.report_id}
        )


# AI Assistance Endpoints with Error Handling
@app.post("/ai/assist-report")
async def ai_assist_report(
    study_uid: str,
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Generate AI-assisted report draft with error handling and retry logic."""
    try:
        ai_service = AIService()
        draft_report = await ai_service.generate_report_draft(study_uid, exam_type)
        
        return draft_report
        
    except Exception as e:
        logger.error(f"Error generating AI report: {str(e)}")
        raise KiroException(
            message=f"AI service failed to generate report: {str(e)}",
            error_code="AI_REPORT_GENERATION_ERROR",
            details={"study_uid": study_uid, "exam_type": exam_type}
        )


if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    if workers > 1:
        # Use Gunicorn for production with multiple workers
        import subprocess
        
        cmd = [
            "gunicorn",
            "main_updated:app",
            "-w", str(workers),
            "-k", "uvicorn.workers.UvicornWorker",
            "-b", f"{host}:{port}",
            "--log-level", log_level,
            "--access-logfile", "-",
            "--error-logfile", "-"
        ]
        
        logger.info(f"Starting Gunicorn with {workers} workers")
        subprocess.run(cmd)
    else:
        # Use Uvicorn for development
        uvicorn.run(
            "main_updated:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=enable_debug
        )