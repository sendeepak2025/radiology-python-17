"""File management API routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os
import shutil
from pathlib import Path
import mimetypes
from datetime import datetime

from database import get_db
from models import Patient, PatientFile
from schemas.patient_schemas import PatientFileCreate, PatientFileResponse
from config import settings

router = APIRouter(prefix="/files", tags=["files"])

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

@router.post("/upload/{patient_id}")
async def upload_files_batch(
    patient_id: str,
    files: List[UploadFile] = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    study_uid: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload multiple files for a patient (batch upload)."""
    from services.file_upload_service import file_upload_service
    
    # Parse tags if provided
    parsed_tags = ["batch_upload"]
    if tags:
        try:
            import json
            parsed_tags.extend(json.loads(tags))
        except json.JSONDecodeError:
            parsed_tags.extend([tag.strip() for tag in tags.split(",") if tag.strip()])
    
    return await file_upload_service.upload_files(
        patient_id=patient_id,
        files=files,
        db=db,
        file_category="batch",
        description=description or "Batch file upload",
        tags=parsed_tags,
        study_uid=study_uid,
        uploaded_by=uploaded_by
    )

@router.post("/upload/{patient_id}/single", response_model=PatientFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    patient_id: str,
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of tags
    study_uid: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a single file for a patient."""
    from services.file_upload_service import file_upload_service
    
    # Parse tags if provided
    parsed_tags = ["single_upload"]
    if tags:
        try:
            import json
            parsed_tags.extend(json.loads(tags))
        except json.JSONDecodeError:
            parsed_tags.extend([tag.strip() for tag in tags.split(",") if tag.strip()])
    
    result = await file_upload_service.upload_files(
        patient_id=patient_id,
        files=[file],
        db=db,
        file_category="single",
        description=description or "Single file upload",
        tags=parsed_tags,
        study_uid=study_uid,
        uploaded_by=uploaded_by
    )
    
    # Return the first (and only) uploaded file in the expected format
    if result and "uploaded_files" in result and result["uploaded_files"]:
        uploaded_file = result["uploaded_files"][0]
        return PatientFileResponse(
            file_id=uploaded_file["file_id"],
            patient_id=patient_id,
            filename=uploaded_file["filename"],
            original_filename=uploaded_file["original_filename"],
            file_path=uploaded_file["file_path"],
            file_size=uploaded_file["file_size"],
            file_type=uploaded_file["file_type"],
            mime_type=uploaded_file["mime_type"],
            description=uploaded_file["description"],
            tags=uploaded_file["tags"],
            uploaded_by=uploaded_file["uploaded_by"],
            created_at=uploaded_file["created_at"]
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )

@router.get("/patient/{patient_id}", response_model=List[PatientFileResponse])
async def get_patient_files(
    patient_id: str,
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    db: Session = Depends(get_db)
):
    """Get all files for a specific patient."""
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    query = db.query(PatientFile).filter(PatientFile.patient_id == patient_id)
    
    # Filter by file type
    if file_type:
        query = query.filter(PatientFile.file_type == file_type)
    
    # Filter by tags
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        for tag in tag_list:
            query = query.filter(PatientFile.tags.contains([tag]))
    
    files = query.order_by(PatientFile.created_at.desc()).all()
    return files

@router.get("/{file_id}", response_model=PatientFileResponse)
async def get_file_info(file_id: UUID, db: Session = Depends(get_db)):
    """Get file information by file ID."""
    file_record = db.query(PatientFile).filter(PatientFile.file_id == file_id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    return file_record

@router.get("/{file_id}/download")
async def download_file(file_id: UUID, db: Session = Depends(get_db)):
    """Download a file by file ID."""
    file_record = db.query(PatientFile).filter(PatientFile.file_id == file_id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=file_record.original_filename,
        media_type=file_record.mime_type
    )

@router.put("/{file_id}", response_model=PatientFileResponse)
async def update_file_metadata(
    file_id: UUID,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    study_uid: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update file metadata."""
    file_record = db.query(PatientFile).filter(PatientFile.file_id == file_id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    # Update fields if provided
    if description is not None:
        file_record.description = description
    if tags is not None:
        file_record.tags = tags
    if study_uid is not None:
        file_record.study_uid = study_uid
    
    db.commit()
    db.refresh(file_record)
    
    return file_record

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: UUID, db: Session = Depends(get_db)):
    """Delete a file and its database record."""
    file_record = db.query(PatientFile).filter(PatientFile.file_id == file_id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    # Delete file from disk
    file_path = Path(file_record.file_path)
    if file_path.exists():
        try:
            os.remove(file_path)
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting file from disk: {str(e)}"
            )
    
    # Delete database record
    db.delete(file_record)
    db.commit()
    
    return None

@router.get("/search/", response_model=List[PatientFileResponse])
async def search_files(
    query: str = Query(..., description="Search query"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """Search files by filename, description, or tags."""
    db_query = db.query(PatientFile)
    
    # Search in filename, original_filename, and description
    search_term = f"%{query}%"
    db_query = db_query.filter(
        (PatientFile.filename.ilike(search_term)) |
        (PatientFile.original_filename.ilike(search_term)) |
        (PatientFile.description.ilike(search_term))
    )
    
    # Apply filters
    if file_type:
        db_query = db_query.filter(PatientFile.file_type == file_type)
    
    if patient_id:
        db_query = db_query.filter(PatientFile.patient_id == patient_id)
    
    # Order by creation date and limit results
    files = db_query.order_by(PatientFile.created_at.desc()).limit(limit).all()
    
    return files

@router.get("/stats/summary")
async def get_file_statistics(db: Session = Depends(get_db)):
    """Get file storage statistics."""
    from sqlalchemy import func
    
    # Total files and size
    total_files = db.query(func.count(PatientFile.id)).scalar()
    total_size = db.query(func.sum(PatientFile.file_size)).scalar() or 0
    
    # Files by type
    files_by_type = db.query(
        PatientFile.file_type,
        func.count(PatientFile.id).label('count'),
        func.sum(PatientFile.file_size).label('total_size')
    ).group_by(PatientFile.file_type).all()
    
    # Recent uploads (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = db.query(func.count(PatientFile.id)).filter(
        PatientFile.created_at >= week_ago
    ).scalar()
    
    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "files_by_type": [
            {
                "file_type": item.file_type,
                "count": item.count,
                "size_bytes": item.total_size or 0,
                "size_mb": round((item.total_size or 0) / (1024 * 1024), 2)
            }
            for item in files_by_type
        ],
        "recent_uploads_7_days": recent_uploads
    }