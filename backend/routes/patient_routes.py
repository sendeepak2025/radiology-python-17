"""Patient API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID
import logging

from database import get_db
from models import Patient, PatientFile
from schemas.patient_schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientWithFiles,
    PatientListResponse,
    PatientFileResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("", response_model=PatientListResponse)
async def get_patients(
    search: Optional[str] = Query(None, description="Search by name, patient ID, or MRN"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=1000, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all patients with optional search and pagination."""
    try:
        logger.info(f"🔍 GET /patients endpoint called with search='{search}', page={page}, per_page={per_page}")
        
        # Base query for active patients
        query = db.query(Patient).filter(Patient.active == True)
        logger.info("✓ Base query created")
        
        # Apply search filter if provided
        if search:
            logger.info(f"Applying search filter: {search}")
            search_filter = (
                Patient.first_name.ilike(f"%{search}%") |
                Patient.last_name.ilike(f"%{search}%") |
                Patient.patient_id.ilike(f"%{search}%") |
                Patient.medical_record_number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count
        total = query.count()
        logger.info(f"✓ Total patients found: {total}")
        
        # Apply pagination
        offset = (page - 1) * per_page
        patients = query.offset(offset).limit(per_page).all()
        logger.info(f"✓ Retrieved {len(patients)} patients for page {page}")
        
        # Convert to response models
        logger.info(f"Converting {len(patients)} patients to response models")
        patient_responses = []
        for i, patient in enumerate(patients):
            try:
                logger.info(f"Converting patient {i+1}/{len(patients)}: {patient.patient_id}")
                patient_response = PatientResponse.model_validate(patient)
                patient_responses.append(patient_response)
                logger.info(f"✓ Successfully converted patient {patient.patient_id}")
            except Exception as e:
                logger.error(f"❌ Error converting patient {patient.patient_id}: {e}")
                logger.error(f"Patient data: {patient.__dict__}")
                logger.error(f"Error type: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        logger.info(f"✓ Successfully converted {len(patient_responses)} patients")
        
        # Calculate pagination info
        total_pages = (total + per_page - 1) // per_page
        logger.info(f"✓ Calculated pagination: total_pages={total_pages}")
        
        try:
            response = PatientListResponse(
                patients=patient_responses,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
            logger.info("✓ PatientListResponse created successfully")
            return response
        except Exception as e:
            logger.error(f"❌ Error creating PatientListResponse: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
    except HTTPException:
        logger.error("❌ HTTPException occurred in get_patients")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_patients: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get a specific patient by ID."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    return patient

@router.get("/{patient_id}/with-files", response_model=PatientWithFiles)
async def get_patient_with_files(patient_id: str, db: Session = Depends(get_db)):
    """Get a patient with all associated files."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    return patient

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient."""
    # Check if patient ID already exists
    existing_patient = db.query(Patient).filter(Patient.patient_id == patient_data.patient_id).first()
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with ID {patient_data.patient_id} already exists"
        )
    
    # Check if MRN already exists (if provided)
    if patient_data.medical_record_number:
        existing_mrn = db.query(Patient).filter(
            Patient.medical_record_number == patient_data.medical_record_number
        ).first()
        if existing_mrn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patient with MRN {patient_data.medical_record_number} already exists"
            )
    
    # Create new patient
    db_patient = Patient(**patient_data.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    return db_patient

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing patient."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Check if MRN already exists for another patient (if updating MRN)
    if patient_data.medical_record_number and patient_data.medical_record_number != patient.medical_record_number:
        existing_mrn = db.query(Patient).filter(
            Patient.medical_record_number == patient_data.medical_record_number,
            Patient.patient_id != patient_id
        ).first()
        if existing_mrn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patient with MRN {patient_data.medical_record_number} already exists"
            )
    
    # Update patient fields
    update_data = patient_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """Soft delete a patient (mark as inactive)."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Soft delete by marking as inactive
    patient.active = False
    db.commit()
    
    return None

@router.post("/{patient_id}/activate", response_model=PatientResponse)
async def activate_patient(patient_id: str, db: Session = Depends(get_db)):
    """Reactivate a patient."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    patient.active = True
    db.commit()
    db.refresh(patient)
    
    return patient

@router.get("/{patient_id}/files", response_model=List[PatientFileResponse])
async def get_patient_files(patient_id: str, db: Session = Depends(get_db)):
    """Get all files for a specific patient."""
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    files = db.query(PatientFile).filter(PatientFile.patient_id == patient_id).all()
    return files

@router.post("/{patient_id}/upload/dicom")
async def upload_dicom_files(
    patient_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload DICOM files for a specific patient."""
    from services.file_upload_service import file_upload_service
    
    # Validate DICOM files
    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must have a filename"
            )
        
        filename_lower = file.filename.lower()
        is_dicom_file = (
            filename_lower.endswith(('.dcm', '.dicom')) or
            'dicom' in filename_lower or
            filename_lower.startswith('mr') or
            filename_lower.startswith('ct') or
            filename_lower.endswith('.ima') or
            '.' not in filename_lower
        )
        
        if not is_dicom_file:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File {file.filename} does not appear to be a DICOM file"
            )
    
    return await file_upload_service.upload_files(
        patient_id=patient_id,
        files=files,
        db=db,
        file_category="dicom",
        description="DICOM file upload",
        tags=["dicom", "medical_imaging"]
    )
            
    return await file_upload_service.upload_files(
        patient_id=patient_id,
        files=files,
        db=db,
        file_category="dicom",
        description="DICOM file upload",
        tags=["dicom", "medical_imaging"]
    )

@router.post("/{patient_id}/upload/reports")
async def upload_report_files(
    patient_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload report files for a specific patient."""
    from services.file_upload_service import file_upload_service
    
    # Validate report files
    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must have a filename"
            )
        
        filename_lower = file.filename.lower()
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
        
        if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.filename}. Allowed types: {', '.join(allowed_extensions)}"
            )
    
    return await file_upload_service.upload_files(
        patient_id=patient_id,
        files=files,
        db=db,
        file_category="reports",
        description="Report file upload",
        tags=["report", "document"]
    )

@router.get("/{patient_id}/uploads")
async def get_patient_uploads(patient_id: str, db: Session = Depends(get_db)):
    """Get list of uploaded files for a patient."""
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Get all files for the patient
    files = db.query(PatientFile).filter(PatientFile.patient_id == patient_id).order_by(PatientFile.created_at.desc()).all()
    
    # Group files by type
    uploads = {
        "dicom_files": [],
        "report_files": [],
        "other_files": []
    }
    
    for file in files:
        file_info = {
            "file_id": str(file.file_id),
            "filename": file.original_filename,
            "size": file.file_size,
            "file_type": file.file_type,
            "mime_type": file.mime_type,
            "description": file.description,
            "tags": file.tags,
            "study_uid": file.study_uid,
            "upload_time": file.created_at.isoformat(),
            "uploaded_by": file.uploaded_by
        }
        
        if file.file_type == "dicom":
            uploads["dicom_files"].append(file_info)
        elif file.file_type in ["pdf", "report", "text", "image"]:
            uploads["report_files"].append(file_info)
        else:
            uploads["other_files"].append(file_info)
    
    return {
        "patient_id": patient_id,
        "uploads": uploads,
        "total_files": len(files)
    }

@router.post("/{patient_id}/files/upload")
async def upload_patient_file(
    patient_id: str,
    files: List[UploadFile] = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Production-ready file upload endpoint for patient files.
    Handles any file type with proper validation and error handling.
    """
    from services.file_upload_service import file_upload_service
    
    # Basic file validation
    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must have a filename"
            )
    
    return await file_upload_service.upload_files(
        patient_id=patient_id,
        files=files,
        db=db,
        file_category="general",
        description=description or "General file upload",
        tags=["general", "uploaded"]
    )

@router.get("/{patient_id}/studies")
async def get_patient_studies(patient_id: str, db: Session = Depends(get_db)):
    """Get all studies for a patient, including uploaded DICOM files converted to studies."""
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Get all DICOM files for this patient
    dicom_files = db.query(PatientFile).filter(
        PatientFile.patient_id == patient_id,
        PatientFile.file_type == "dicom"
    ).all()
    
    studies = []
    for file in dicom_files:
        study = {
            "study_uid": file.study_uid or f"uploaded_{patient_id}_{file.original_filename}",
            "patient_id": patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "study_date": file.created_at.strftime("%Y-%m-%d"),
            "modality": "CT",  # Default modality, can be enhanced later
            "study_description": file.description or f"Uploaded DICOM - {file.original_filename}",
            "status": "received",
            "upload_source": "file_upload",
            "original_filename": file.original_filename,
            "file_id": str(file.file_id),
            "dicom_url": f"http://localhost:8000/uploads/dicom/{patient_id}/{file.original_filename}",
            "created_at": file.created_at.isoformat()
        }
        studies.append(study)
    
    return {
        "patient_id": patient_id,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "studies": studies,
        "total_studies": len(studies)
    }

@router.get("/search/advanced")
async def advanced_patient_search(
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    date_of_birth: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    phone: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    medical_record_number: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Advanced patient search with multiple criteria."""
    query = db.query(Patient).filter(Patient.active == True)
    
    if first_name:
        query = query.filter(Patient.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Patient.last_name.ilike(f"%{last_name}%"))
    if date_of_birth:
        try:
            from datetime import datetime
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
            query = query.filter(Patient.date_of_birth == dob.date())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    if gender:
        query = query.filter(Patient.gender == gender.upper())
    if phone:
        query = query.filter(Patient.phone.ilike(f"%{phone}%"))
    if email:
        query = query.filter(Patient.email.ilike(f"%{email}%"))
    if medical_record_number:
        query = query.filter(Patient.medical_record_number.ilike(f"%{medical_record_number}%"))
    
    total = query.count()
    patients = query.offset(skip).limit(limit).all()
    
    total_pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1
    
    return PatientListResponse(
        patients=patients,
        total=total,
        page=current_page,
        per_page=limit,
        total_pages=total_pages
    )