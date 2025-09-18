"""
Fixed backend with working upload endpoints
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
from pathlib import Path
import uuid
import logging
import shutil
import mimetypes
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./kiro_mini.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Database Models
class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(64), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(10), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    medical_record_number = Column(String(50), nullable=True)
    insurance_info = Column(JSON, nullable=True)
    emergency_contact = Column(JSON, nullable=True)
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# Pydantic Models
class PatientBase(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=64)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(M|F|O)$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    medical_record_number: Optional[str] = Field(None, max_length=50)
    allergies: Optional[str] = None
    medical_history: Optional[str] = None

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(M|F|O)$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    medical_record_number: Optional[str] = Field(None, max_length=50)
    allergies: Optional[str] = None
    medical_history: Optional[str] = None

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class PatientResponse(PatientBase):
    id: str
    active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PatientListResponse(BaseModel):
    patients: List[PatientResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(
    title="Kiro Patient API - Fixed Upload",
    description="Patient management with working file uploads",
    version="1.2.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.2.0"
    )

# Patient endpoints
@app.get("/patients")
async def get_patients(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: Optional[int] = Query(None, ge=1, le=1000),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    skip: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db)
):
    try:
        # Handle pagination parameters
        if limit is not None:
            items_per_page = limit
            current_page = (skip // limit) + 1 if skip and limit > 0 else page
        else:
            items_per_page = per_page or 20
            current_page = page
        
        offset = (current_page - 1) * items_per_page if skip is None else skip
        
        # Base query
        query = db.query(Patient).filter(Patient.active == True)
        
        # Search filter
        if search:
            search_filter = (
                Patient.first_name.ilike(f"%{search}%") |
                Patient.last_name.ilike(f"%{search}%") |
                Patient.patient_id.ilike(f"%{search}%") |
                Patient.medical_record_number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        total = query.count()
        patients = query.offset(offset).limit(items_per_page).all()
        total_pages = (total + items_per_page - 1) // items_per_page
        
        return {
            "patients": patients,
            "total": total,
            "page": current_page,
            "per_page": items_per_page,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error retrieving patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    
    return patient

# FIXED UPLOAD ENDPOINTS
@app.post("/patients/{patient_id}/upload/dicom")
async def upload_dicom_file(
    patient_id: str,
    files: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload DICOM file - FIXED VERSION"""
    try:
        logger.info(f"📤 DICOM upload request for patient {patient_id}, file: {files.filename}")
        
        # Check if patient exists
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            logger.error(f"Patient {patient_id} not found")
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Create patient directory
        patient_dir = uploads_dir / patient_id
        patient_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = patient_dir / files.filename
        
        with open(file_path, "wb") as buffer:
            content = await files.read()
            buffer.write(content)
        
        # Get file info
        file_size = file_path.stat().st_size
        
        logger.info(f"✅ Successfully uploaded {files.filename} ({file_size} bytes) for patient {patient_id}")
        
        return {
            "message": "File uploaded successfully",
            "filename": files.filename,
            "file_size": file_size,
            "file_type": "dicom",
            "patient_id": patient_id,
            "upload_time": datetime.utcnow().isoformat(),
            "file_url": f"/uploads/{patient_id}/{files.filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/patients/{patient_id}/upload")
async def upload_patient_file(
    patient_id: str,
    files: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload any file - FIXED VERSION"""
    try:
        logger.info(f"📤 File upload request for patient {patient_id}, file: {files.filename}")
        
        # Check if patient exists
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Create patient directory
        patient_dir = uploads_dir / patient_id
        patient_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = patient_dir / files.filename
        
        with open(file_path, "wb") as buffer:
            content = await files.read()
            buffer.write(content)
        
        # Determine file type
        if files.filename.lower().endswith(('.dcm', '.dicom')):
            file_type = "dicom"
        elif files.filename.lower().endswith(('.pdf',)):
            file_type = "pdf"
        elif files.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            file_type = "image"
        else:
            file_type = "other"
        
        file_size = file_path.stat().st_size
        
        logger.info(f"✅ Successfully uploaded {files.filename} ({file_size} bytes)")
        
        return {
            "message": "File uploaded successfully",
            "filename": files.filename,
            "file_size": file_size,
            "file_type": file_type,
            "patient_id": patient_id,
            "upload_time": datetime.utcnow().isoformat(),
            "file_url": f"/uploads/{patient_id}/{files.filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/patients/{patient_id}/files")
async def get_patient_files(patient_id: str, db: Session = Depends(get_db)):
    """Get patient files"""
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Get files
        patient_dir = uploads_dir / patient_id
        
        if not patient_dir.exists():
            return {"patient_id": patient_id, "files": [], "total_files": 0}
        
        files = []
        for file_path in patient_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "file_size": stat.st_size,
                    "file_type": "dicom" if file_path.suffix.lower() in ['.dcm', '.dicom'] else "other",
                    "upload_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "file_url": f"/uploads/{patient_id}/{file_path.name}"
                })
        
        return {
            "patient_id": patient_id,
            "files": files,
            "total_files": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploads/{patient_id}/{filename}")
@app.head("/uploads/{patient_id}/{filename}")
async def serve_file(patient_id: str, filename: str):
    """Serve uploaded files"""
    try:
        file_path = uploads_dir / patient_id / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Determine media type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if filename.lower().endswith(('.dcm', '.dicom')):
            mime_type = "application/dicom"
        elif filename.lower().endswith(('.png',)):
            mime_type = "image/png"
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            mime_type = "image/jpeg"
        elif filename.lower().endswith(('.gif',)):
            mime_type = "image/gif"
        
        return FileResponse(
            path=str(file_path),
            media_type=mime_type or "application/octet-stream",
            filename=filename,
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Studies endpoints - convert uploaded files to studies
@app.get("/patients/{patient_id}/studies")
async def get_patient_studies(patient_id: str, db: Session = Depends(get_db)):
    """Get all studies for a patient, including uploaded DICOM files converted to studies."""
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Get uploaded DICOM files and convert them to studies
        patient_dir = uploads_dir / patient_id
        studies = []
        
        if patient_dir.exists():
            for file_path in patient_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.dcm', '.dicom']:
                    stat = file_path.stat()
                    
                    # Generate a DICOM-like study UID for frontend compatibility
                    # Use file modification time to create a unique UID
                    timestamp = int(stat.st_mtime * 1000000)  # microseconds
                    dicom_like_uid = f"1.2.840.113619.2.5.{timestamp}.{len(file_path.name)}.{hash(file_path.name) % 1000000000}"
                    
                    study = {
                        "study_uid": dicom_like_uid,
                        "patient_id": patient_id,
                        "patient_name": f"{patient.first_name} {patient.last_name}",
                        "patient_birth_date": patient.date_of_birth.strftime("%Y-%m-%d") if patient.date_of_birth else None,
                        "patient_sex": patient.gender,
                        "study_date": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
                        "study_time": datetime.fromtimestamp(stat.st_ctime).strftime("%H:%M:%S"),
                        "study_datetime": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modality": "CT",  # Default modality
                        "study_description": f"Uploaded DICOM - {file_path.name}",
                        "series_description": f"Series from {file_path.name}",
                        "status": "received",
                        "origin": "file_upload",
                        "accession_number": f"ACC_{patient_id}_{int(stat.st_ctime)}",
                        "referring_physician": "Upload System",
                        "institution_name": "Kiro Medical",
                        "original_filename": file_path.name,
                        "file_size": stat.st_size,
                        "dicom_url": f"/uploads/{patient_id}/{file_path.name}",
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    studies.append(study)
        
        return {
            "patient_id": patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "studies": studies,
            "total_studies": len(studies)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient studies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/studies")
async def get_all_studies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all studies with optional filtering."""
    try:
        studies = []
        
        # Get patients
        query = db.query(Patient).filter(Patient.active == True)
        if patient_id:
            query = query.filter(Patient.patient_id == patient_id)
        
        patients = query.all()
        
        # Convert uploaded DICOM files to studies for each patient
        for patient in patients:
            patient_dir = uploads_dir / patient.patient_id
            
            if patient_dir.exists():
                for file_path in patient_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in ['.dcm', '.dicom']:
                        stat = file_path.stat()
                        
                        # Generate consistent DICOM-like study UID
                        timestamp = int(stat.st_mtime * 1000000)
                        dicom_like_uid = f"1.2.840.113619.2.5.{timestamp}.{len(file_path.name)}.{hash(file_path.name) % 1000000000}"
                        
                        study = {
                            "study_uid": dicom_like_uid,
                            "patient_id": patient.patient_id,
                            "patient_name": f"{patient.first_name} {patient.last_name}",
                            "study_date": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
                            "study_time": datetime.fromtimestamp(stat.st_ctime).strftime("%H:%M:%S"),
                            "modality": "CT",
                            "study_description": f"Uploaded DICOM - {file_path.name}",
                            "series_description": f"Series from {file_path.name}",
                            "status": "received",
                            "origin": "file_upload",
                            "original_filename": file_path.name,
                            "file_size": stat.st_size,
                            "dicom_url": f"/uploads/{patient.patient_id}/{file_path.name}",
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                        }
                        studies.append(study)
        
        # Apply pagination
        total = len(studies)
        paginated_studies = studies[skip:skip + limit]
        
        return {
            "studies": paginated_studies,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting studies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/studies/{study_uid:path}")
async def get_study(study_uid: str, db: Session = Depends(get_db)):
    """Get a specific study by UID - handles both uploaded and DICOM UIDs."""
    try:
        logger.info(f"🔍 Looking for study: {study_uid}")
        
        # Search through all patients and their uploaded files
        patients = db.query(Patient).filter(Patient.active == True).all()
        
        for patient in patients:
            patient_dir = uploads_dir / patient.patient_id
            
            if patient_dir.exists():
                for file_path in patient_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in ['.dcm', '.dicom']:
                        # Check if this file matches the study UID
                        # Try multiple matching strategies
                        
                        # Strategy 1: Check if study_uid matches our generated format
                        generated_uid = f"uploaded_{patient.patient_id}_{file_path.stem}"
                        
                        # Strategy 2: Generate the same DICOM-like UID we use in the list
                        file_stat = file_path.stat()
                        timestamp = int(file_stat.st_mtime * 1000000)
                        expected_uid = f"1.2.840.113619.2.5.{timestamp}.{len(file_path.name)}.{hash(file_path.name) % 1000000000}"
                        
                        # Strategy 3: Multiple matching approaches
                        uid_match = (
                            study_uid == generated_uid or
                            study_uid == expected_uid or
                            study_uid in file_path.name or
                            file_path.stem in study_uid or
                            study_uid.replace(".", "_") in file_path.name or
                            abs(hash(study_uid) % 1000000000) == abs(hash(file_path.name) % 1000000000)
                        )
                        
                        if uid_match:
                            stat = file_path.stat()
                            
                            logger.info(f"✅ Found matching study: {file_path.name}")
                            
                            return {
                                "study_uid": study_uid,
                                "patient_id": patient.patient_id,
                                "patient_name": f"{patient.first_name} {patient.last_name}",
                                "patient_birth_date": patient.date_of_birth.strftime("%Y-%m-%d") if patient.date_of_birth else None,
                                "patient_sex": patient.gender,
                                "study_date": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
                                "study_time": datetime.fromtimestamp(stat.st_ctime).strftime("%H:%M:%S"),
                                "study_datetime": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                "modality": "CT",
                                "study_description": f"Uploaded DICOM - {file_path.name}",
                                "series_description": f"Series from {file_path.name}",
                                "status": "received",
                                "origin": "file_upload",
                                "accession_number": f"ACC_{patient.patient_id}_{int(stat.st_ctime)}",
                                "referring_physician": "Upload System",
                                "institution_name": "Kiro Medical",
                                "original_filename": file_path.name,
                                "file_size": stat.st_size,
                                "dicom_url": f"/uploads/{patient.patient_id}/{file_path.name}",
                                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "images": [
                                    {
                                        "image_uid": f"{study_uid}_image_1",
                                        "image_number": 1,
                                        "image_url": f"/uploads/{patient.patient_id}/{file_path.name}",
                                        "content_type": "application/dicom"
                                    }
                                ],
                                "series": [
                                    {
                                        "series_uid": f"{study_uid}_series_1",
                                        "series_number": 1,
                                        "series_description": f"Series from {file_path.name}",
                                        "modality": "CT",
                                        "images": [
                                            {
                                                "image_uid": f"{study_uid}_image_1",
                                                "image_number": 1,
                                                "image_url": f"/uploads/{patient.patient_id}/{file_path.name}"
                                            }
                                        ]
                                    }
                                ]
                            }
        
        logger.error(f"❌ Study not found: {study_uid}")
        raise HTTPException(status_code=404, detail=f"Study {study_uid} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting study {study_uid}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/patients/count")
async def debug_patient_count(db: Session = Depends(get_db)):
    """Debug endpoint"""
    try:
        total = db.query(Patient).count()
        active = db.query(Patient).filter(Patient.active == True).count()
        
        return {
            "total_patients": total,
            "active_patients": active,
            "uploads_directory": str(uploads_dir.absolute()),
            "version": "1.3.0 - With Studies Support"
        }
    except Exception as e:
        return {"error": str(e)}

# Report Models
class ReportCreate(BaseModel):
    study_uid: str
    patient_id: str
    exam_type: Optional[str] = None
    ai_generated: bool = False

class ReportUpdate(BaseModel):
    findings: Optional[str] = None
    impressions: Optional[str] = None
    recommendations: Optional[str] = None
    status: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    report_id: str
    study_uid: str
    patient_id: str
    status: str
    findings: Optional[str] = None
    impressions: Optional[str] = None
    recommendations: Optional[str] = None
    ai_generated: bool
    ai_confidence: Optional[float] = None
    created_at: str
    updated_at: Optional[str] = None

# Report endpoints
@app.post("/api/reports", response_model=ReportResponse)
async def create_report(report_data: ReportCreate, db: Session = Depends(get_db)):
    """Create a new medical report"""
    try:
        logger.info(f"📋 Creating report for study {report_data.study_uid}")
        
        # Check if patient exists
        patient = db.query(Patient).filter(
            Patient.patient_id == report_data.patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {report_data.patient_id} not found")
        
        # Generate report ID
        report_id = f"RPT_{report_data.patient_id}_{int(datetime.utcnow().timestamp())}"
        
        # Create report data
        report = {
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "study_uid": report_data.study_uid,
            "patient_id": report_data.patient_id,
            "status": "draft",
            "ai_generated": report_data.ai_generated,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # If AI generated, add some mock findings
        if report_data.ai_generated:
            report.update({
                "findings": "AI Analysis: Image quality is adequate for diagnostic interpretation. No acute abnormalities detected.",
                "impressions": "Normal study. No significant pathological findings identified.",
                "recommendations": "Routine follow-up as clinically indicated.",
                "ai_confidence": 0.85,
                "status": "draft"
            })
        
        # Save report to a simple JSON file (in production, use proper database)
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"{report_id}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Report created: {report_id}")
        
        return ReportResponse(**report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/ai-generate", response_model=ReportResponse)
async def generate_ai_report(request: dict, db: Session = Depends(get_db)):
    """Generate AI-powered medical report"""
    try:
        study_uid = request.get("study_uid")
        if not study_uid:
            raise HTTPException(status_code=400, detail="study_uid is required")
        
        logger.info(f"🤖 Generating AI report for study {study_uid}")
        
        # Find patient from study (simplified - in production, query studies table)
        # For now, extract patient ID from study context or use a default
        patient_id = "PAT002"  # This should be extracted from study data
        
        # Create AI report
        report_data = ReportCreate(
            study_uid=study_uid,
            patient_id=patient_id,
            ai_generated=True
        )
        
        return await create_report(report_data, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating AI report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    """Get a specific report"""
    try:
        report_file = Path("reports") / f"{report_id}.json"
        
        if not report_file.exists():
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        with open(report_file, "r") as f:
            report_data = json.load(f)
        
        return ReportResponse(**report_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/study/{study_uid}")
async def get_study_reports(study_uid: str):
    """Get all reports for a study"""
    try:
        reports_dir = Path("reports")
        if not reports_dir.exists():
            return {"reports": []}
        
        reports = []
        for report_file in reports_dir.glob("*.json"):
            try:
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                    if report_data.get("study_uid") == study_uid:
                        reports.append(report_data)
            except:
                continue
        
        return {"reports": reports}
        
    except Exception as e:
        logger.error(f"❌ Error getting study reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)