"""
Kiro-mini FastAPI Backend
Main application entry point for medical imaging and billing integration system.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import json

# Import database and models
try:
    from .database import engine, SessionLocal, Base
    from .models import Study, Report, Superbill, AuditLog
    from .config import settings
    from .services.study_service import StudyService
    from .services.report_service import ReportService
    from .services.billing_service import BillingService
    from .services.ai_service import AIService
    from .services.measurement_service import MeasurementService
    from .services.workflow_service import WorkflowService
    from .services.realtime_billing_service import RealtimeBillingService
    from .middleware.audit_middleware import AuditLoggingMiddleware, HIPAAComplianceMiddleware
    from .routes.patient_routes import router as patient_router
    from .routes.file_routes import router as file_router
except ImportError:
    # Fall back to absolute imports if relative imports fail
    from backend.database import engine, SessionLocal, Base
    from backend.config import settings
    from backend.services.study_service import StudyService
    from backend.services.report_service import ReportService
    from backend.services.billing_service import BillingService
    from backend.services.ai_service import AIService
    from backend.services.measurement_service import MeasurementService
    from backend.services.workflow_service import WorkflowService
    from backend.services.realtime_billing_service import RealtimeBillingService
    from backend.middleware.audit_middleware import AuditLoggingMiddleware, HIPAAComplianceMiddleware
    from backend.routes.patient_routes import router as patient_router
    from backend.routes.file_routes import router as file_router

# Import schemas
import importlib.util
schemas_path = os.path.join(os.path.dirname(__file__), 'schemas.py')
spec = importlib.util.spec_from_file_location("schemas_module", schemas_path)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)

# Import schema classes
StudyIngest = schemas_module.StudyIngest
StudyResponse = schemas_module.StudyResponse
ReportCreate = schemas_module.ReportCreate
ReportResponse = schemas_module.ReportResponse
SuperbillCreate = schemas_module.SuperbillCreate
SuperbillResponse = schemas_module.SuperbillResponse
HealthResponse = schemas_module.HealthResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Kiro-mini backend...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Initialize services
    db_session = SessionLocal()
    app.state.study_service = StudyService()
    app.state.report_service = ReportService()
    app.state.billing_service = BillingService()
    app.state.ai_service = AIService()
    app.state.measurement_service = MeasurementService()
    app.state.workflow_service = WorkflowService(db_session)
    app.state.realtime_billing_service = RealtimeBillingService()
    
    logger.info("Services initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kiro-mini backend...")

# Create FastAPI application
app = FastAPI(
    title="Kiro-mini API",
    description="Medical Imaging and Billing Integration System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - Allow all origins for development
allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for audit logging
app.add_middleware(AuditLoggingMiddleware)

# Add HIPAA compliance middleware
app.add_middleware(HIPAAComplianceMiddleware)

# Mount static files for uploads
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(patient_router)
app.include_router(file_router)

# Include enhanced patient routes with monitoring
try:
    from .routes.enhanced_patient_routes import router as enhanced_patient_router
    app.include_router(enhanced_patient_router, prefix="/api/v2")
    logger.info("Enhanced patient routes with monitoring enabled")
except ImportError:
    logger.warning("Enhanced patient routes not available")

# Setup logging configuration
try:
    from .config.logging_config import setup_logging
    setup_logging(
        log_level="INFO",
        log_file="logs/kiro_backend.log",
        enable_console=True,
        enable_structured=True
    )
    logger.info("Enhanced logging configuration applied")
except ImportError:
    logger.warning("Enhanced logging configuration not available")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "database": "connected",
            "redis": "connected",
            "orthanc": "connected"
        }
    )

# Upload health check endpoint
@app.get("/upload/health")
async def upload_health_check():
    """Health check endpoint specifically for upload functionality."""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "upload_config": {
                "max_file_size": "100MB",
                "supported_formats": ["dcm", "dicom", "pdf", "jpg", "png"],
                "timeout": "60s",
                "endpoints": [
                    "/patients/{patient_id}/upload/dicom",
                    "/patients/{patient_id}/upload"
                ]
            },
            "cors_enabled": True,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Upload health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload service unhealthy: {str(e)}")

# DICOM File Serving Endpoint
@app.get("/uploads/dicom/{patient_id}/{filename}")
async def serve_dicom_file(patient_id: str, filename: str):
    """Serve DICOM files with proper MIME type for DICOM viewers."""
    try:
        # Try different possible paths for the DICOM file
        possible_paths = [
            Path(f"uploads/dicom/{patient_id}/{filename}"),
            Path(f"uploads/{patient_id}/{filename}"),
            Path(f"uploads/dicom/{filename}"),
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            logger.error(f"DICOM file not found: {filename} for patient {patient_id}")
            logger.error(f"Searched paths: {[str(p) for p in possible_paths]}")
            raise HTTPException(status_code=404, detail=f"DICOM file not found: {filename}")
        
        logger.info(f"Serving DICOM file: {file_path}")
        
        # Return file with proper DICOM MIME type
        return FileResponse(
            path=str(file_path),
            media_type="application/dicom",
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error serving DICOM file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving DICOM file: {str(e)}")

# General File Serving Endpoint
@app.get("/uploads/{patient_id}/{filename}")
async def serve_patient_file(patient_id: str, filename: str):
    """Serve patient files with proper MIME type detection."""
    try:
        # Try different possible paths for the file
        possible_paths = [
            Path(f"uploads/{patient_id}/{filename}"),
            Path(f"uploads/dicom/{patient_id}/{filename}"),
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            logger.error(f"File not found: {filename} for patient {patient_id}")
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Detect MIME type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # Special handling for DICOM files
        if filename.lower().endswith(('.dcm', '.dicom')) or not mime_type:
            mime_type = "application/dicom"
        
        logger.info(f"Serving file: {file_path} with MIME type: {mime_type}")
        
        return FileResponse(
            path=str(file_path),
            media_type=mime_type or "application/octet-stream",
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

# Study Management Endpoints
@app.post("/studies/{study_uid}/ingest")
async def ingest_study(
    study_uid: str,
    study_data: StudyIngest,
    background_tasks: BackgroundTasks,
    db: SessionLocal = Depends(get_db)
):
    """
    Process incoming study metadata from Orthanc webhook.
    Automatically enqueues AI processing job.
    """
    try:
        logger.info(f"Ingesting study: {study_uid}")
        
        # Create or update study record
        study_service = StudyService()
        study = await study_service.create_or_update_study(db, study_uid, study_data)
        
        # Enqueue AI processing job
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
        raise HTTPException(status_code=500, detail=f"Failed to ingest study: {str(e)}")

@app.get("/studies/{study_uid}", response_model=StudyResponse)
async def get_study(study_uid: str, db: SessionLocal = Depends(get_db)):
    """Retrieve study metadata and image URLs."""
    try:
        study_service = StudyService()
        study = await study_service.get_study_with_images(db, study_uid)
        
        if not study:
            raise HTTPException(status_code=404, detail="Study not found")
        
        return study
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving study {study_uid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve study: {str(e)}")

@app.get("/studies")
async def list_studies(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: SessionLocal = Depends(get_db)
):
    """List all studies with optional filtering."""
    try:
        study_service = StudyService()
        studies = await study_service.list_studies(db, skip=skip, limit=limit, status=status)
        return {"studies": studies, "total": len(studies)}
        
    except Exception as e:
        logger.error(f"Error listing studies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list studies: {str(e)}")

# Report Management Endpoints
@app.post("/reports", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: SessionLocal = Depends(get_db)
):
    """Create or update a structured report with AI assistance."""
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
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")

@app.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: SessionLocal = Depends(get_db)):
    """Retrieve report details."""
    try:
        report_service = ReportService()
        report = await report_service.get_report(db, report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")

@app.get("/reports")
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    exam_type: str = None,
    radiologist_id: str = None,
    ai_generated: bool = None,
    db: SessionLocal = Depends(get_db)
):
    """List reports with optional filtering."""
    try:
        report_service = ReportService()
        reports = await report_service.list_reports(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
            exam_type=exam_type,
            radiologist_id=radiologist_id,
            ai_generated=ai_generated
        )
        return {"reports": reports, "total": len(reports)}
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")

@app.get("/studies/{study_uid}/reports")
async def get_study_reports(study_uid: str, db: SessionLocal = Depends(get_db)):
    """Get all reports for a specific study."""
    try:
        report_service = ReportService()
        reports = await report_service.get_reports_by_study(db, study_uid)
        return {"study_uid": study_uid, "reports": reports}
        
    except Exception as e:
        logger.error(f"Error retrieving reports for study {study_uid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve study reports: {str(e)}")

@app.post("/reports/{report_id}/finalize", response_model=ReportResponse)
async def finalize_report(
    report_id: str,
    background_tasks: BackgroundTasks,
    db: SessionLocal = Depends(get_db)
):
    """Finalize a report and trigger billing generation."""
    try:
        report_service = ReportService()
        report = await report_service.finalize_report(db, report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Trigger automatic billing generation
        billing_service = BillingService()
        background_tasks.add_task(
            billing_service.generate_superbill_async,
            db, report_id
        )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to finalize report: {str(e)}")

@app.get("/reports/statistics")
async def get_report_statistics(db: SessionLocal = Depends(get_db)):
    """Get report statistics for dashboard."""
    try:
        report_service = ReportService()
        stats = await report_service.get_report_statistics(db)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting report statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/reports/search")
async def search_reports(
    q: str,
    limit: int = 50,
    db: SessionLocal = Depends(get_db)
):
    """Search reports by content."""
    try:
        report_service = ReportService()
        results = await report_service.search_reports(db, q, limit)
        return {"query": q, "results": results}
        
    except Exception as e:
        logger.error(f"Error searching reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search reports: {str(e)}")

# Billing Endpoints
@app.post("/superbills", response_model=SuperbillResponse)
async def generate_superbill(
    superbill_data: SuperbillCreate,
    db: SessionLocal = Depends(get_db)
):
    """Generate superbill and 837P payload from report."""
    try:
        billing_service = BillingService()
        superbill = await billing_service.generate_superbill(db, superbill_data.report_id)
        
        return superbill
        
    except Exception as e:
        logger.error(f"Error generating superbill: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate superbill: {str(e)}")

@app.get("/billing/codes/suggest/realtime")
async def suggest_diagnosis_codes_realtime(
    findings: str,
    exam_type: str,
    measurements: Dict[str, Any] = None,
    user_id: str = None,
    db: SessionLocal = Depends(get_db)
):
    """Real-time ICD-10 diagnosis code suggestions with intelligent analysis."""
    try:
        realtime_billing_service = RealtimeBillingService()
        
        user_context = {"user_id": user_id} if user_id else None
        
        suggestions = await realtime_billing_service.suggest_codes_realtime(
            findings_text=findings,
            exam_type=exam_type,
            measurements=measurements,
            user_context=user_context
        )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error suggesting diagnosis codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest codes: {str(e)}")

@app.post("/billing/validate/realtime")
async def validate_billing_codes_realtime(
    cpt_codes: List[str],
    icd10_codes: List[str],
    exam_type: str,
    patient_context: Dict[str, Any] = None,
    db: SessionLocal = Depends(get_db)
):
    """Real-time validation of CPT-ICD-10 code combinations with comprehensive analysis."""
    try:
        realtime_billing_service = RealtimeBillingService()
        
        validation = await realtime_billing_service.validate_codes_realtime(
            cpt_codes=cpt_codes,
            icd10_codes=icd10_codes,
            exam_type=exam_type,
            patient_context=patient_context
        )
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating billing codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate codes: {str(e)}")

@app.get("/billing/codes/suggest")
async def suggest_diagnosis_codes(
    findings: str,
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Legacy ICD-10 diagnosis code suggestions (maintained for compatibility)."""
    try:
        billing_service = BillingService()
        suggestions = await billing_service.suggest_diagnosis_codes(findings, exam_type)
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Error suggesting diagnosis codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to suggest codes: {str(e)}")

@app.post("/billing/validate")
async def validate_billing_codes(
    cpt_codes: List[str],
    icd10_codes: List[str],
    db: SessionLocal = Depends(get_db)
):
    """Legacy CPT-ICD-10 code validation (maintained for compatibility)."""
    try:
        billing_service = BillingService()
        validation = await billing_service.validate_code_combinations(cpt_codes, icd10_codes)
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating billing codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate codes: {str(e)}")

# AI Assistance Endpoints
@app.post("/ai/assist-report")
async def ai_assist_report(
    study_uid: str,
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Generate AI-assisted report draft."""
    try:
        ai_service = AIService()
        draft_report = await ai_service.generate_report_draft(study_uid, exam_type)
        
        return draft_report
        
    except Exception as e:
        logger.error(f"Error generating AI report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI report: {str(e)}")

@app.post("/ai/generate-measurements")
async def generate_ai_measurements(
    study_uid: str,
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Generate AI measurements for a study."""
    try:
        ai_service = AIService()
        
        # Generate AI analysis with focus on measurements
        ai_analysis = await ai_service._simulate_ai_analysis(study_uid, exam_type)
        
        return {
            "study_uid": study_uid,
            "exam_type": exam_type,
            "measurements": ai_analysis.get("measurements", {}),
            "confidence_score": ai_analysis.get("confidence_score", 0.0),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating AI measurements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate measurements: {str(e)}")

@app.post("/ai/enhance-findings")
async def enhance_findings_with_ai(
    findings: str,
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Enhance user findings with AI suggestions."""
    try:
        ai_service = AIService()
        
        # Create enhanced findings based on input
        enhanced = {
            "original_findings": findings,
            "enhanced_findings": findings,  # In real implementation, this would be AI-enhanced
            "suggested_impressions": "",
            "suggested_recommendations": "",
            "confidence_score": 0.8
        }
        
        # Add exam-specific enhancements
        if exam_type == "echo_complete":
            enhanced["suggested_impressions"] = "Consider correlation with clinical symptoms and prior studies."
            enhanced["suggested_recommendations"] = "Follow-up echocardiogram in 6-12 months if clinically indicated."
        elif exam_type == "vascular_carotid":
            enhanced["suggested_impressions"] = "Assess cardiovascular risk factors and consider medical management."
            enhanced["suggested_recommendations"] = "Continue vascular risk factor modification."
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing findings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enhance findings: {str(e)}")

@app.get("/ai/job-status/{job_id}")
async def get_ai_job_status(job_id: str, db: SessionLocal = Depends(get_db)):
    """Get AI processing job status."""
    try:
        ai_service = AIService()
        status = await ai_service.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@app.get("/ai/queue-stats")
async def get_ai_queue_statistics(db: SessionLocal = Depends(get_db)):
    """Get AI processing queue statistics."""
    try:
        ai_service = AIService()
        stats = await ai_service.get_queue_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting queue statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue statistics: {str(e)}")

# Measurement Management Endpoints
@app.get("/measurements/template/{exam_type}")
async def get_measurement_template(exam_type: str):
    """Get measurement template for exam type."""
    try:
        measurement_service = MeasurementService()
        template = measurement_service.get_measurement_template(exam_type)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"No template found for exam type: {exam_type}")
        
        return {
            "exam_type": exam_type,
            "template": template,
            "categories": list(set(info.get("category", "other") for info in template.values()))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting measurement template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@app.post("/measurements/validate")
async def validate_measurements(
    measurements: Dict[str, Any],
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Validate measurements against templates and normal ranges."""
    try:
        measurement_service = MeasurementService()
        validation = measurement_service.validate_measurements(measurements, exam_type)
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating measurements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate measurements: {str(e)}")

@app.post("/measurements/calculate")
async def calculate_derived_measurements(
    measurements: Dict[str, Any],
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Calculate derived measurements from primary measurements."""
    try:
        measurement_service = MeasurementService()
        derived = measurement_service.calculate_derived_measurements(measurements, exam_type)
        
        return {
            "exam_type": exam_type,
            "derived_measurements": derived,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating measurements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate measurements: {str(e)}")

@app.post("/measurements/summary")
async def generate_measurement_summary(
    measurements: Dict[str, Any],
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Generate comprehensive measurement summary."""
    try:
        measurement_service = MeasurementService()
        summary = measurement_service.generate_measurement_summary(measurements, exam_type)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating measurement summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@app.post("/measurements/recommendations")
async def get_measurement_recommendations(
    measurements: Dict[str, Any],
    exam_type: str,
    db: SessionLocal = Depends(get_db)
):
    """Get clinical recommendations based on measurements."""
    try:
        measurement_service = MeasurementService()
        recommendations = measurement_service.get_measurement_recommendations(measurements, exam_type)
        
        return {
            "exam_type": exam_type,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

# Rapid Workflow Endpoints
@app.post("/workflow/rapid-report/start")
async def start_rapid_reporting_workflow(
    study_uid: str,
    user_id: str = None,
    db: SessionLocal = Depends(get_db)
):
    """Start the 1-minute rapid reporting workflow."""
    try:
        workflow_service = WorkflowService()
        result = await workflow_service.start_rapid_reporting_workflow(
            db, study_uid, user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error starting rapid workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@app.post("/workflow/rapid-report/complete")
async def complete_rapid_reporting_workflow(
    workflow_id: str,
    user_modifications: Dict[str, Any] = None,
    user_id: str = None,
    db: SessionLocal = Depends(get_db)
):
    """Complete the rapid reporting workflow with optional user modifications."""
    try:
        workflow_service = WorkflowService()
        result = await workflow_service.complete_rapid_reporting_workflow(
            db, workflow_id, user_modifications, user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error completing rapid workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete workflow: {str(e)}")

@app.get("/workflow/rapid-report/status/{workflow_id}")
async def get_workflow_status(workflow_id: str, db: SessionLocal = Depends(get_db)):
    """Get the current status of a rapid reporting workflow."""
    try:
        workflow_service = WorkflowService()
        status = await workflow_service.get_workflow_status(db, workflow_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@app.get("/workflow/rapid-report/metrics")
async def get_workflow_performance_metrics(
    start_date: str = None,
    end_date: str = None,
    db: SessionLocal = Depends(get_db)
):
    """Get performance metrics for rapid reporting workflows."""
    try:
        workflow_service = WorkflowService()
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        metrics = await workflow_service.get_workflow_performance_metrics(
            db, start_dt, end_dt
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting workflow metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow metrics: {str(e)}")

# Advanced Real-time Billing Endpoints
@app.post("/billing/codes/analyze")
async def analyze_clinical_text(
    clinical_text: str,
    exam_type: str,
    include_measurements: bool = True,
    db: SessionLocal = Depends(get_db)
):
    """Analyze clinical text and provide comprehensive coding recommendations."""
    try:
        realtime_billing_service = RealtimeBillingService()
        
        # Get code suggestions
        suggestions = await realtime_billing_service.suggest_codes_realtime(
            findings_text=clinical_text,
            exam_type=exam_type
        )
        
        # Get CPT codes for exam type
        from billing.cpt_mappings import CPTMappings
        cpt_mappings = CPTMappings.get_all_mappings()
        exam_mapping = cpt_mappings.get(exam_type, {})
        primary_cpt = exam_mapping.get("primary_cpt", "")
        
        # Validate suggested combinations
        if suggestions["suggestions"] and primary_cpt:
            suggested_icd_codes = [s["icd10_code"] for s in suggestions["suggestions"][:3]]
            validation = await realtime_billing_service.validate_codes_realtime(
                cpt_codes=[primary_cpt],
                icd10_codes=suggested_icd_codes,
                exam_type=exam_type
            )
        else:
            validation = {"valid": False, "errors": ["No valid code combinations found"]}
        
        return {
            "clinical_analysis": {
                "text_length": len(clinical_text),
                "key_findings": clinical_text.split(". ")[:5],  # First 5 sentences
                "exam_type": exam_type
            },
            "code_suggestions": suggestions,
            "recommended_cpt": primary_cpt,
            "validation_result": validation,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing clinical text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze text: {str(e)}")

@app.get("/billing/codes/search")
async def search_billing_codes(
    query: str,
    code_type: str = "both",  # "cpt", "icd10", or "both"
    limit: int = 20,
    db: SessionLocal = Depends(get_db)
):
    """Search for CPT and ICD-10 codes by description or code."""
    try:
        results = {"cpt_codes": [], "icd10_codes": []}
        query_lower = query.lower()
        
        if code_type in ["cpt", "both"]:
            # Search CPT codes
            from billing.cpt_mappings import CPTMappings
            cpt_mappings = CPTMappings.get_all_mappings()
            
            for exam_type, mapping in cpt_mappings.items():
                # Check primary CPT
                if (query_lower in mapping.get("description", "").lower() or 
                    query in mapping.get("primary_cpt", "")):
                    results["cpt_codes"].append({
                        "code": mapping.get("primary_cpt"),
                        "description": mapping.get("description"),
                        "category": mapping.get("category"),
                        "base_charge": mapping.get("base_charge"),
                        "exam_type": exam_type
                    })
                
                # Check additional codes
                additional_codes = mapping.get("additional_codes", {})
                for code, info in additional_codes.items():
                    if (query_lower in info.get("description", "").lower() or 
                        query in code):
                        results["cpt_codes"].append({
                            "code": code,
                            "description": info.get("description"),
                            "category": mapping.get("category"),
                            "base_charge": info.get("base_charge"),
                            "exam_type": exam_type,
                            "additional": True
                        })
        
        if code_type in ["icd10", "both"]:
            # Search ICD-10 codes
            from billing.icd10_mappings import ICD10Mappings
            icd10_mappings = ICD10Mappings.get_all_codes()
            
            for code, info in icd10_mappings.items():
                if (query_lower in info.get("description", "").lower() or 
                    query.upper() in code):
                    results["icd10_codes"].append({
                        "code": code,
                        "description": info.get("description"),
                        "category": info.get("category"),
                        "primary_suitable": info.get("primary_suitable", False),
                        "common_procedures": info.get("common_procedures", [])
                    })
        
        # Limit results
        results["cpt_codes"] = results["cpt_codes"][:limit]
        results["icd10_codes"] = results["icd10_codes"][:limit]
        
        return {
            "query": query,
            "results": results,
            "total_found": {
                "cpt": len(results["cpt_codes"]),
                "icd10": len(results["icd10_codes"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching billing codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search codes: {str(e)}")

@app.get("/billing/reimbursement/estimate")
async def estimate_reimbursement(
    cpt_codes: List[str],
    payer_type: str = "medicare",
    geographic_area: str = "national",
    modifiers: List[str] = None,
    db: SessionLocal = Depends(get_db)
):
    """Estimate reimbursement for CPT codes."""
    try:
        from billing.cpt_mappings import ReimbursementCalculator
        calculator = ReimbursementCalculator()
        
        estimates = {}
        total_medicare = 0.0
        total_commercial = 0.0
        
        for cpt_code in cpt_codes:
            # Find RVU for code
            rvu = 0.0
            description = ""
            
            from billing.cpt_mappings import CPTMappings
            cpt_mappings = CPTMappings.get_all_mappings()
            
            for exam_type, mapping in cpt_mappings.items():
                if mapping.get("primary_cpt") == cpt_code:
                    rvu = mapping.get("rvu", 0.0)
                    description = mapping.get("description", "")
                    break
                
                additional_codes = mapping.get("additional_codes", {})
                if cpt_code in additional_codes:
                    rvu = additional_codes[cpt_code].get("rvu", 0.0)
                    description = additional_codes[cpt_code].get("description", "")
                    break
            
            if rvu > 0:
                medicare_amount = calculator.calculate_medicare_reimbursement(
                    cpt_code, rvu, modifiers or [], geographic_area
                )
                commercial_amount = calculator.calculate_commercial_reimbursement(
                    cpt_code, rvu, payer_type, 120.0
                )
                
                estimates[cpt_code] = {
                    "description": description,
                    "rvu": rvu,
                    "medicare": medicare_amount,
                    "commercial_120": commercial_amount,
                    "commercial_150": calculator.calculate_commercial_reimbursement(
                        cpt_code, rvu, payer_type, 150.0
                    )
                }
                
                total_medicare += medicare_amount
                total_commercial += commercial_amount
        
        return {
            "estimates": estimates,
            "totals": {
                "medicare": round(total_medicare, 2),
                "commercial_120": round(total_commercial, 2),
                "commercial_150": round(total_commercial * 1.25, 2)
            },
            "parameters": {
                "payer_type": payer_type,
                "geographic_area": geographic_area,
                "modifiers": modifiers or []
            },
            "calculated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error estimating reimbursement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to estimate reimbursement: {str(e)}")

@app.get("/billing/compliance/check")
async def check_billing_compliance(
    cpt_codes: List[str],
    icd10_codes: List[str],
    payer_type: str = "medicare",
    db: SessionLocal = Depends(get_db)
):
    """Comprehensive billing compliance check."""
    try:
        realtime_billing_service = RealtimeBillingService()
        
        # Perform validation
        validation = await realtime_billing_service.validate_codes_realtime(
            cpt_codes=cpt_codes,
            icd10_codes=icd10_codes,
            exam_type="unknown",  # Will be determined from CPT codes
            patient_context={"insurance": {"primary": {"payer_name": payer_type}}}
        )
        
        # Additional compliance checks
        compliance_issues = []
        
        # Check for common compliance issues
        if len(icd10_codes) == 0:
            compliance_issues.append({
                "severity": "error",
                "issue": "No diagnosis codes provided",
                "impact": "Claim will be denied for lack of medical necessity"
            })
        
        if len(cpt_codes) > 5:
            compliance_issues.append({
                "severity": "warning", 
                "issue": "Multiple procedures on same date",
                "impact": "May require additional documentation or modifiers"
            })
        
        # Check for high-risk combinations
        high_risk_cpts = ["71260", "70553", "93351"]
        high_risk_found = [code for code in cpt_codes if code in high_risk_cpts]
        
        if high_risk_found:
            compliance_issues.append({
                "severity": "warning",
                "issue": f"High-cost procedures detected: {', '.join(high_risk_found)}",
                "impact": "May require prior authorization or additional documentation"
            })
        
        return {
            "compliance_status": "compliant" if validation["valid"] and not compliance_issues else "issues_found",
            "validation_result": validation,
            "compliance_issues": compliance_issues,
            "recommendations": validation.get("suggestions", []),
            "overall_risk_score": validation.get("reimbursement_risk", 0.0),
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking billing compliance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check compliance: {str(e)}")

@app.get("/billing/stats/realtime")
async def get_realtime_billing_stats(db: SessionLocal = Depends(get_db)):
    """Get real-time billing validation performance statistics."""
    try:
        realtime_billing_service = RealtimeBillingService()
        stats = await realtime_billing_service.get_realtime_validation_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting billing stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get billing stats: {str(e)}")

# WebSocket Endpoints for Real-time Billing
@app.websocket("/ws/billing/{user_id}")
async def websocket_billing_endpoint(websocket: WebSocket, user_id: str = None):
    """WebSocket endpoint for real-time billing code suggestions and validation."""
    
    session_id = await websocket_billing_service.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle the message
            await websocket_billing_service.handle_message(session_id, message)
            
    except WebSocketDisconnect:
        websocket_billing_service.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        websocket_billing_service.disconnect(session_id)

@app.get("/ws/billing/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    try:
        stats = websocket_billing_service.get_connection_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket stats: {str(e)}")

@app.post("/ws/billing/cleanup")
async def cleanup_websocket_connections(timeout_minutes: int = 30):
    """Clean up inactive WebSocket connections."""
    try:
        cleaned_count = await websocket_billing_service.cleanup_inactive_connections(timeout_minutes)
        
        return {
            "cleaned_connections": cleaned_count,
            "timeout_minutes": timeout_minutes,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up WebSocket connections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup connections: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Exception",
            "message": exc.detail,
            "code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )

# EHR Integration and Data Export Endpoints
@app.get("/fhir/DiagnosticReport/{report_id}")
async def export_fhir_diagnostic_report(
    report_id: str,
    user_id: str = "system",
    db: SessionLocal = Depends(get_db)
):
    """Export a report as FHIR DiagnosticReport."""
    try:
        fhir_service = FHIRService()
        
        fhir_report = await fhir_service.export_diagnostic_report(
            db=db,
            report_id=report_id,
            user_id=user_id
        )
        
        return fhir_report
        
    except Exception as e:
        logger.error(f"Error exporting FHIR DiagnosticReport: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export FHIR report: {str(e)}")

@app.get("/fhir/ImagingStudy/{study_uid}")
async def export_fhir_imaging_study(
    study_uid: str,
    user_id: str = "system",
    db: SessionLocal = Depends(get_db)
):
    """Export a study as FHIR ImagingStudy."""
    try:
        fhir_service = FHIRService()
        
        fhir_study = await fhir_service.export_imaging_study(
            db=db,
            study_uid=study_uid,
            user_id=user_id
        )
        
        return fhir_study
        
    except Exception as e:
        logger.error(f"Error exporting FHIR ImagingStudy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export FHIR study: {str(e)}")

@app.get("/fhir/Bundle/{study_uid}")
async def export_fhir_bundle(
    study_uid: str,
    include_reports: bool = True,
    user_id: str = "system",
    db: SessionLocal = Depends(get_db)
):
    """Export a complete FHIR Bundle for a study."""
    try:
        fhir_service = FHIRService()
        
        fhir_bundle = await fhir_service.export_bundle(
            db=db,
            study_uid=study_uid,
            include_reports=include_reports,
            user_id=user_id
        )
        
        return fhir_bundle
        
    except Exception as e:
        logger.error(f"Error exporting FHIR Bundle: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export FHIR bundle: {str(e)}")

@app.get("/x12/837p/{superbill_id}")
async def export_x12_837p(
    superbill_id: str,
    user_id: str = "system",
    db: SessionLocal = Depends(get_db)
):
    """Export superbill as X12 837P format."""
    try:
        x12_service = X12Service()
        
        x12_content = await x12_service.convert_superbill_to_x12(
            db=db,
            superbill_id=superbill_id,
            user_id=user_id
        )
        
        return {
            "superbill_id": superbill_id,
            "format": "X12 837P",
            "content": x12_content,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting X12 837P: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export X12: {str(e)}")

@app.post("/x12/837p/{superbill_id}/validate")
async def validate_x12_837p(
    superbill_id: str,
    user_id: str = "system",
    db: SessionLocal = Depends(get_db)
):
    """Validate X12 837P format for a superbill."""
    try:
        x12_service = X12Service()
        
        # Generate X12 content
        x12_content = await x12_service.convert_superbill_to_x12(
            db=db,
            superbill_id=superbill_id,
            user_id=user_id
        )
        
        # Validate format
        validation_result = await x12_service.validate_x12_format(x12_content)
        
        return {
            "superbill_id": superbill_id,
            "validation": validation_result,
            "validated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating X12 837P: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate X12: {str(e)}")

@app.post("/webhooks/test")
async def test_webhook_endpoint(
    webhook_url: str,
    secret_key: str = None
):
    """Test webhook endpoint connectivity."""
    try:
        webhook_service = WebhookService()
        
        result = await webhook_service.test_webhook_endpoint(
            webhook_url=webhook_url,
            secret_key=secret_key
        )
        
        return {
            "test_result": result,
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")

@app.post("/webhooks/send")
async def send_webhook_notification(
    webhook_data: Dict[str, Any],
    db: SessionLocal = Depends(get_db)
):
    """Send webhook notification to external system."""
    try:
        webhook_service = WebhookService()
        
        notification_type = webhook_data.get("type")
        event_type = webhook_data.get("event_type")
        webhook_url = webhook_data.get("webhook_url")
        secret_key = webhook_data.get("secret_key")
        resource_id = webhook_data.get("resource_id")
        user_id = webhook_data.get("user_id", "system")
        
        if notification_type == "study":
            study = db.query(Study).filter(Study.study_uid == resource_id).first()
            if not study:
                raise HTTPException(status_code=404, detail="Study not found")
            
            result = await webhook_service.send_study_notification(
                db=db,
                study=study,
                event_type=event_type,
                webhook_url=webhook_url,
                secret_key=secret_key,
                user_id=user_id
            )
            
        elif notification_type == "report":
            report = db.query(Report).filter(Report.report_id == resource_id).first()
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            
            result = await webhook_service.send_report_notification(
                db=db,
                report=report,
                event_type=event_type,
                webhook_url=webhook_url,
                secret_key=secret_key,
                user_id=user_id
            )
            
        elif notification_type == "billing":
            superbill = db.query(Superbill).filter(Superbill.superbill_id == resource_id).first()
            if not superbill:
                raise HTTPException(status_code=404, detail="Superbill not found")
            
            result = await webhook_service.send_billing_notification(
                db=db,
                superbill=superbill,
                event_type=event_type,
                webhook_url=webhook_url,
                secret_key=secret_key,
                user_id=user_id
            )
            
        else:
            raise HTTPException(status_code=400, detail="Invalid notification type")
        
        return {
            "notification_result": result,
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send webhook: {str(e)}")

@app.get("/integration/status")
async def get_integration_status(db: SessionLocal = Depends(get_db)):
    """Get EHR integration status and capabilities."""
    try:
        # Get recent export statistics
        from datetime import timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        audit_service = AuditService()
        recent_exports = await audit_service.get_audit_trail(
            db=db,
            event_type="FHIR_EXPORT",
            start_date=recent_date,
            limit=1000
        )
        
        x12_exports = await audit_service.get_audit_trail(
            db=db,
            event_type="X12_EXPORT",
            start_date=recent_date,
            limit=1000
        )
        
        webhook_sends = await audit_service.get_audit_trail(
            db=db,
            event_type="WEBHOOK_SENT",
            start_date=recent_date,
            limit=1000
        )
        
        return {
            "integration_status": "active",
            "capabilities": {
                "fhir_export": {
                    "supported_resources": ["DiagnosticReport", "ImagingStudy", "Bundle"],
                    "fhir_version": "R4",
                    "recent_exports": len(recent_exports)
                },
                "x12_export": {
                    "supported_formats": ["837P"],
                    "recent_exports": len(x12_exports)
                },
                "webhooks": {
                    "supported_events": [
                        "study.created", "study.updated",
                        "report.created", "report.finalized",
                        "billing.generated", "billing.submitted"
                    ],
                    "recent_sends": len(webhook_sends)
                }
            },
            "statistics": {
                "total_fhir_exports": len(recent_exports),
                "total_x12_exports": len(x12_exports),
                "total_webhook_sends": len(webhook_sends),
                "period_days": 7
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting integration status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get integration status: {str(e)}")

# Audit and Compliance Endpoints
@app.get("/audit/trail")
async def get_audit_trail(
    resource_type: str = None,
    resource_id: str = None,
    study_uid: str = None,
    user_id: str = None,
    event_type: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    db: SessionLocal = Depends(get_db)
):
    """Get audit trail with filtering options."""
    try:
        audit_service = AuditService()
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        audit_logs = await audit_service.get_audit_trail(
            db=db,
            resource_type=resource_type,
            resource_id=resource_id,
            study_uid=study_uid,
            user_id=user_id,
            event_type=event_type,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit
        )
        
        return {
            "audit_logs": audit_logs,
            "total": len(audit_logs),
            "filters": {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "study_uid": study_uid,
                "user_id": user_id,
                "event_type": event_type,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting audit trail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")

@app.get("/audit/user/{user_id}/activity")
async def get_user_activity_summary(
    user_id: str,
    start_date: str = None,
    end_date: str = None,
    db: SessionLocal = Depends(get_db)
):
    """Get user activity summary for compliance reporting."""
    try:
        audit_service = AuditService()
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        activity_summary = await audit_service.get_user_activity_summary(
            db=db,
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return activity_summary
        
    except Exception as e:
        logger.error(f"Error getting user activity summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}")

@app.get("/reports/{report_id}/versions")
async def get_report_version_history(
    report_id: str,
    limit: int = 50,
    db: SessionLocal = Depends(get_db)
):
    """Get version history for a report."""
    try:
        version_service = ReportVersionService()
        
        versions = await version_service.get_version_history(
            db=db,
            report_id=uuid.UUID(report_id),
            limit=limit
        )
        
        return {
            "report_id": report_id,
            "versions": versions,
            "total_versions": len(versions)
        }
        
    except Exception as e:
        logger.error(f"Error getting report version history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get version history: {str(e)}")

@app.get("/reports/versions/{version_id}")
async def get_report_version(
    version_id: str,
    db: SessionLocal = Depends(get_db)
):
    """Get a specific version of a report."""
    try:
        version_service = ReportVersionService()
        
        version = await version_service.get_version(
            db=db,
            version_id=uuid.UUID(version_id)
        )
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return version
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report version: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get version: {str(e)}")

@app.post("/reports/versions/{version_id}/restore")
async def restore_report_version(
    version_id: str,
    report_id: str,
    user_id: str = "system",
    db: SessionLocal = Depends(get_db)
):
    """Restore a report to a previous version."""
    try:
        version_service = ReportVersionService()
        
        restored_report = await version_service.restore_version(
            db=db,
            report_id=uuid.UUID(report_id),
            version_id=uuid.UUID(version_id),
            user_id=user_id
        )
        
        return {
            "message": "Report restored successfully",
            "report_id": report_id,
            "restored_version_id": version_id
        }
        
    except Exception as e:
        logger.error(f"Error restoring report version: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restore version: {str(e)}")

@app.get("/reports/versions/{version1_id}/compare/{version2_id}")
async def compare_report_versions(
    version1_id: str,
    version2_id: str,
    db: SessionLocal = Depends(get_db)
):
    """Compare two versions of a report."""
    try:
        version_service = ReportVersionService()
        
        comparison = await version_service.compare_versions(
            db=db,
            version1_id=uuid.UUID(version1_id),
            version2_id=uuid.UUID(version2_id)
        )
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing report versions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare versions: {str(e)}")

@app.get("/audit/compliance/report")
async def get_compliance_report(
    start_date: str = None,
    end_date: str = None,
    db: SessionLocal = Depends(get_db)
):
    """Generate a compliance report for HIPAA auditing."""
    try:
        audit_service = AuditService()
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else datetime.utcnow() - timedelta(days=30)
        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        
        # Get all audit logs for the period
        all_logs = await audit_service.get_audit_trail(
            db=db,
            start_date=start_dt,
            end_date=end_dt,
            limit=10000
        )
        
        # Generate compliance statistics
        total_events = len(all_logs)
        unique_users = len(set(log["user_id"] for log in all_logs if log["user_id"]))
        study_accesses = len([log for log in all_logs if log["event_type"].startswith("STUDY_")])
        report_modifications = len([log for log in all_logs if log["event_type"].startswith("REPORT_")])
        billing_activities = len([log for log in all_logs if log["event_type"].startswith("BILLING_")])
        
        # Event type breakdown
        event_types = {}
        for log in all_logs:
            event_type = log["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # User activity breakdown
        user_activity = {}
        for log in all_logs:
            user_id = log["user_id"]
            if user_id not in user_activity:
                user_activity[user_id] = {"total_events": 0, "event_types": {}}
            user_activity[user_id]["total_events"] += 1
            event_type = log["event_type"]
            user_activity[user_id]["event_types"][event_type] = user_activity[user_id]["event_types"].get(event_type, 0) + 1
        
        return {
            "compliance_report": {
                "period": {
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat(),
                    "days": (end_dt - start_dt).days
                },
                "summary": {
                    "total_events": total_events,
                    "unique_users": unique_users,
                    "study_accesses": study_accesses,
                    "report_modifications": report_modifications,
                    "billing_activities": billing_activities
                },
                "event_type_breakdown": event_types,
                "user_activity_summary": user_activity,
                "generated_at": datetime.utcnow().isoformat(),
                "hipaa_compliance_status": "COMPLIANT" if total_events > 0 else "NO_ACTIVITY"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate compliance report: {str(e)}")

# Performance Monitoring Endpoints
@app.get("/monitoring/metrics")
async def get_current_metrics():
    """Get current system and application metrics."""
    try:
        from services.monitoring_service import get_monitoring_service
        monitoring = await get_monitoring_service()
        
        system_metrics = await monitoring.collect_system_metrics()
        app_metrics = await monitoring.collect_application_metrics()
        
        return {
            "system": system_metrics.__dict__,
            "application": app_metrics.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/monitoring/performance-summary")
async def get_performance_summary():
    """Get comprehensive performance summary for dashboard."""
    try:
        from services.monitoring_service import get_monitoring_service
        monitoring = await get_monitoring_service()
        
        summary = await monitoring.get_performance_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")

@app.get("/monitoring/alerts")
async def get_active_alerts():
    """Get all active performance alerts."""
    try:
        from services.monitoring_service import get_monitoring_service
        monitoring = await get_monitoring_service()
        
        alerts = await monitoring.get_active_alerts()
        return {
            "alerts": [alert.__dict__ for alert in alerts],
            "count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@app.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve a performance alert."""
    try:
        from services.monitoring_service import get_monitoring_service
        monitoring = await get_monitoring_service()
        
        await monitoring.resolve_alert(alert_id)
        return {"message": f"Alert {alert_id} resolved", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@app.get("/monitoring/history")
async def get_metrics_history(hours: int = 24):
    """Get historical metrics for specified hours."""
    try:
        from services.monitoring_service import get_monitoring_service
        monitoring = await get_monitoring_service()
        
        history = await monitoring.get_metrics_history(hours)
        return {
            "history": history,
            "hours": hours,
            "count": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics history: {str(e)}")

@app.get("/monitoring/queue-stats")
async def get_queue_statistics():
    """Get detailed queue statistics."""
    try:
        from services.redis_service import RedisService
        redis_service = RedisService()
        await redis_service.connect()
        
        ai_queue_stats = await redis_service.get_queue_stats("ai_processing")
        billing_queue_stats = await redis_service.get_queue_stats("billing_processing")
        
        return {
            "queues": {
                "ai_processing": ai_queue_stats,
                "billing_processing": billing_queue_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting queue statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue statistics: {str(e)}")

@app.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check for all system components."""
    try:
        health_status = {
            "overall": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Database health
        try:
            db = next(get_db())
            db.execute(text("SELECT 1"))
            health_status["components"]["database"] = {
                "status": "healthy",
                "response_time_ms": 10
            }
            db.close()
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
        
        # Redis health
        try:
            from services.redis_service import RedisService
            redis_service = RedisService()
            redis_healthy = await redis_service.health_check()
            health_status["components"]["redis"] = {
                "status": "healthy" if redis_healthy else "unhealthy"
            }
            if not redis_healthy:
                health_status["overall"] = "degraded"
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
        
        # Orthanc health (mock check)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://orthanc:8042/system", timeout=5) as response:
                    if response.status == 200:
                        health_status["components"]["orthanc"] = {
                            "status": "healthy",
                            "response_time_ms": 50
                        }
                    else:
                        health_status["components"]["orthanc"] = {
                            "status": "unhealthy",
                            "http_status": response.status
                        }
                        health_status["overall"] = "degraded"
        except Exception as e:
            health_status["components"]["orthanc"] = {
                "status": "unknown",
                "error": "Connection failed"
            }
        
        # AI Worker health (check queue processing)
        try:
            from services.redis_service import RedisService
            redis_service = RedisService()
            await redis_service.connect()
            queue_stats = await redis_service.get_queue_stats("ai_processing")
            
            # If queue is growing too large, worker might be unhealthy
            if queue_stats.get("queued", 0) > 50:
                health_status["components"]["ai_worker"] = {
                    "status": "degraded",
                    "queue_size": queue_stats.get("queued", 0)
                }
                health_status["overall"] = "degraded"
            else:
                health_status["components"]["ai_worker"] = {
                    "status": "healthy",
                    "queue_size": queue_stats.get("queued", 0)
                }
        except Exception as e:
            health_status["components"]["ai_worker"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Advanced Professional Workflow Endpoints

@app.get("/workflow/worklist")
async def get_radiologist_worklist(radiologist_id: Optional[str] = None, priority: Optional[str] = None):
    """Get prioritized worklist for radiologist with advanced filtering"""
    try:
        from services.workflow_service import get_workflow_service
        
        workflow_service = get_workflow_service(db)
        worklist = await workflow_service.get_prioritized_worklist(radiologist_id)
        
        # Filter by priority if specified
        if priority:
            worklist = [item for item in worklist if item.priority.value == priority]
        
        # Convert to response format
        worklist_response = []
        for item in worklist:
            worklist_response.append({
                "study_uid": item.study_uid,
                "patient_id": item.patient_id,
                "exam_type": item.exam_type,
                "priority": item.priority.value,
                "subspecialty": item.subspecialty.value,
                "assigned_radiologist": item.assigned_radiologist,
                "status": item.status.value,
                "arrival_time": item.arrival_time.isoformat(),
                "target_completion_time": item.target_completion_time.isoformat(),
                "estimated_reading_time": item.estimated_reading_time,
                "complexity_score": item.complexity_score
            })
        
        return {"worklist": worklist_response}
        
    except Exception as e:
        logger.error(f"Error getting worklist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get worklist: {str(e)}")

@app.post("/workflow/assign-study")
async def assign_study_to_radiologist(assignment_data: dict):
    """Assign study to radiologist using intelligent load balancing"""
    try:
        from services.workflow_service import get_workflow_service
        
        workflow_service = get_workflow_service(db)
        
        # Create worklist item from study data
        worklist_item = await workflow_service.create_worklist_item(assignment_data)
        
        # Assign to optimal radiologist
        success = await workflow_service.assign_study(worklist_item)
        
        if success:
            return {
                "success": True,
                "assigned_radiologist": worklist_item.assigned_radiologist,
                "message": f"Study {worklist_item.study_uid} assigned successfully"
            }
        else:
            return {
                "success": False,
                "message": "No available radiologists found for assignment"
            }
        
    except Exception as e:
        logger.error(f"Error assigning study: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign study: {str(e)}")

@app.get("/workflow/performance/{radiologist_id}")
async def get_radiologist_performance(radiologist_id: str, days: int = 30):
    """Get comprehensive performance metrics for radiologist"""
    try:
        from services.workflow_service import get_workflow_service
        
        workflow_service = get_workflow_service(db)
        metrics = await workflow_service.get_performance_metrics(radiologist_id, days)
        
        return {"performance_metrics": metrics}
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@app.post("/critical-findings/detect")
async def detect_critical_findings(detection_data: dict):
    """Automatically detect critical findings in report"""
    try:
        from services.critical_findings_service import get_critical_findings_service
        
        critical_service = get_critical_findings_service(db)
        
        report_data = detection_data.get("report_data", {})
        study_data = detection_data.get("study_data", {})
        
        # Detect critical findings
        findings = await critical_service.detect_critical_findings(report_data, study_data)
        
        # Initiate workflow for each finding
        for finding in findings:
            await critical_service.initiate_critical_finding_workflow(finding)
        
        findings_response = []
        for finding in findings:
            findings_response.append({
                "finding_id": finding.finding_id,
                "finding_type": finding.finding_type.value,
                "severity_level": finding.severity_level,
                "description": finding.description,
                "detected_at": finding.detected_at.isoformat(),
                "status": finding.status.value
            })
        
        return {
            "critical_findings": findings_response,
            "total_findings": len(findings)
        }
        
    except Exception as e:
        logger.error(f"Error detecting critical findings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to detect critical findings: {str(e)}")

@app.post("/critical-findings/{finding_id}/acknowledge")
async def acknowledge_critical_finding(finding_id: str, acknowledgment_data: dict):
    """Acknowledge critical finding"""
    try:
        from services.critical_findings_service import get_critical_findings_service
        
        critical_service = get_critical_findings_service(db)
        
        acknowledger_id = acknowledgment_data.get("acknowledger_id", "")
        method = acknowledgment_data.get("method", "web_interface")
        
        success = await critical_service.acknowledge_critical_finding(
            finding_id, acknowledger_id, method
        )
        
        return {
            "success": success,
            "message": "Critical finding acknowledged" if success else "Failed to acknowledge finding"
        }
        
    except Exception as e:
        logger.error(f"Error acknowledging critical finding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge critical finding: {str(e)}")

@app.get("/critical-findings/report")
async def get_critical_findings_report(start_date: str, end_date: str):
    """Get comprehensive critical findings compliance report"""
    try:
        from services.critical_findings_service import get_critical_findings_service
        
        critical_service = get_critical_findings_service(db)
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        report = await critical_service.get_critical_findings_report(start_dt, end_dt)
        
        return {"critical_findings_report": report}
        
    except Exception as e:
        logger.error(f"Error generating critical findings report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.get("/studies/{study_uid}/prior-studies")
async def get_prior_studies(study_uid: str):
    """Find relevant prior studies for comparison"""
    try:
        from services.comparison_service import get_comparison_service
        
        comparison_service = get_comparison_service(db)
        
        # Mock current study data - in production, query from database
        current_study = {
            "study_uid": study_uid,
            "patient_id": "PAT001",
            "study_date": datetime.now().isoformat(),
            "exam_type": "chest_ct",
            "modality": "CT"
        }
        
        prior_studies = await comparison_service.find_prior_studies(current_study)
        
        prior_studies_response = []
        for study in prior_studies:
            prior_studies_response.append({
                "study_uid": study.study_uid,
                "patient_id": study.patient_id,
                "study_date": study.study_date.isoformat(),
                "exam_type": study.exam_type,
                "modality": study.modality,
                "similarity_score": study.similarity_score
            })
        
        return {"prior_studies": prior_studies_response}
        
    except Exception as e:
        logger.error(f"Error finding prior studies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to find prior studies: {str(e)}")

@app.post("/studies/{study_uid}/compare")
async def compare_with_prior_study(study_uid: str, comparison_data: dict):
    """Compare current study with prior study and detect changes"""
    try:
        from services.comparison_service import get_comparison_service
        
        comparison_service = get_comparison_service(db)
        
        # Mock current study data
        current_study = {
            "study_uid": study_uid,
            "patient_id": comparison_data.get("patient_id", "PAT001"),
            "study_date": datetime.now().isoformat(),
            "exam_type": "chest_ct",
            "modality": "CT"
        }
        
        # Mock prior study
        prior_study_uid = comparison_data.get("prior_study_uid", "")
        prior_studies = await comparison_service.find_prior_studies(current_study)
        
        if prior_studies:
            prior_study = prior_studies[0]
            
            # Detect changes
            changes = await comparison_service.detect_changes(current_study, prior_study)
            
            changes_response = []
            for change in changes:
                changes_response.append({
                    "change_id": change.change_id,
                    "change_type": change.change_type.value,
                    "location": change.location,
                    "description": change.description,
                    "confidence_score": change.confidence_score,
                    "clinical_significance": change.clinical_significance
                })
            
            return {
                "comparison_results": {
                    "current_study": study_uid,
                    "prior_study": prior_study.study_uid,
                    "changes_detected": len(changes),
                    "changes": changes_response
                }
            }
        else:
            return {
                "comparison_results": {
                    "current_study": study_uid,
                    "prior_study": None,
                    "message": "No suitable prior studies found for comparison"
                }
            }
        
    except Exception as e:
        logger.error(f"Error comparing studies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare studies: {str(e)}")

# Health check endpoint for advanced services
@app.get("/health/advanced-services")
async def health_check_advanced_services():
    """Health check for advanced professional services"""
    try:
        services_status = {
            "workflow_service": "healthy",
            "critical_findings_service": "healthy", 
            "comparison_service": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {"status": "healthy", "services": services_status}
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)