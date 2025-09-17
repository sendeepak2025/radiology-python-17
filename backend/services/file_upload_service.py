"""Unified file upload service for all patient file uploads."""

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import os
import shutil
import mimetypes
import uuid
import logging
import httpx

from models import Patient, PatientFile
from config import settings

logger = logging.getLogger(__name__)

class FileUploadService:
    """Centralized service for handling all patient file uploads."""
    
    def __init__(self):
        self.uploads_dir = Path("uploads")
        self.uploads_dir.mkdir(exist_ok=True)
    
    async def upload_files(
        self,
        patient_id: str,
        files: List[UploadFile],
        db: Session,
        file_category: str = "general",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        study_uid: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload multiple files for a patient with unified handling."""
        
        # Validate patient exists
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            logger.error(f"Patient {patient_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        logger.info(f"Uploading {len(files)} files for patient {patient_id} in category {file_category}")
        
        # Create category-specific directory
        patient_dir = self.uploads_dir / file_category / patient_id
        patient_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        db_files = []
        
        try:
            for file in files:
                # Validate file
                if not file.filename:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="File must have a filename"
                    )
                
                # Read file content
                content = await file.read()
                if not content:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"File {file.filename} is empty"
                    )
                
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = Path(file.filename).suffix
                unique_filename = f"{timestamp}_{file.filename}"
                file_path = patient_dir / unique_filename
                
                # Save file to disk
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                
                # Determine file type and MIME type
                file_size = len(content)
                mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
                
                # Categorize file type
                file_type = self._determine_file_type(file.filename, mime_type, file_category)
                
                # Generate study UID if not provided
                if not study_uid and file_category == "dicom":
                    study_uid = f"1.2.3.4.5.6.7.8.9.{abs(hash(file.filename)) % 10000}"
                
                # Create database record
                db_file = PatientFile(
                    patient_id=patient_id,
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=str(file_path),
                    file_size=file_size,
                    file_type=file_type,
                    mime_type=mime_type,
                    description=description or f"Uploaded {file_category} file: {file.filename}",
                    tags=tags or [file_category, "uploaded"],
                    study_uid=study_uid,
                    uploaded_by=uploaded_by or "system"
                )
                
                db.add(db_file)
                db_files.append(db_file)
                
                # Send DICOM files to Orthanc server
                if file_type == "dicom":
                    try:
                        await self._send_dicom_to_orthanc(file_path, content)
                        logger.info(f"DICOM file sent to Orthanc: {file.filename}")
                    except Exception as orthanc_error:
                        logger.error(f"Failed to send DICOM to Orthanc: {str(orthanc_error)}")
                        # Continue with upload even if Orthanc fails
                
                uploaded_files.append({
                    "filename": file.filename,
                    "size": file_size,
                    "file_type": file_type,
                    "study_uid": study_uid,
                    "upload_time": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Processed file: {file.filename} ({file_size} bytes)")
            
            # Commit all files at once
            db.commit()
            
            return {
                "message": f"Successfully uploaded {len(uploaded_files)} file(s) for patient {patient_id}",
                "patient_id": patient_id,
                "category": file_category,
                "uploaded_files": uploaded_files,
                "total_files": len(uploaded_files)
            }
            
        except Exception as e:
            # Clean up files if database operation fails
            for file_info in uploaded_files:
                file_path = patient_dir / file_info["filename"]
                if file_path.exists():
                    os.remove(file_path)
            db.rollback()
            logger.error(f"Upload failed for patient {patient_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {str(e)}"
            )
    
    def _determine_file_type(self, filename: str, mime_type: str, category: str) -> str:
        """Determine file type based on filename, MIME type, and category."""
        filename_lower = filename.lower()
        
        # DICOM files
        if category == "dicom" or filename_lower.endswith(('.dcm', '.dicom')) or 'dicom' in filename_lower:
            return "dicom"
        
        # Based on MIME type
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type == "application/pdf":
            return "pdf"
        elif mime_type.startswith("text/"):
            return "text"
        
        # Based on file extension
        if filename_lower.endswith(('.pdf',)):
            return "pdf"
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            return "image"
        elif filename_lower.endswith(('.doc', '.docx', '.txt')):
            return "document"
        elif filename_lower.endswith(('.dcm', '.dicom')):
            return "dicom"
        
        return "other"
    
    async def _send_dicom_to_orthanc(self, file_path: Path, content: bytes):
        """Send DICOM file to Orthanc server for processing."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Upload DICOM file to Orthanc
                response = await client.post(
                    f"{settings.orthanc_url}/instances",
                    content=content,
                    headers={"Content-Type": "application/dicom"}
                )
                
                if response.status_code == 200:
                    orthanc_response = response.json()
                    logger.info(f"DICOM uploaded to Orthanc: {orthanc_response.get('ID', 'unknown')}")
                    return orthanc_response
                else:
                    logger.error(f"Orthanc upload failed: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload DICOM to Orthanc: {response.status_code}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(f"Network error sending DICOM to Orthanc: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Network error connecting to Orthanc: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error sending DICOM to Orthanc: {str(e)}")
            raise

# Global instance
file_upload_service = FileUploadService()