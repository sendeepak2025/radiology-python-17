#!/usr/bin/env python3
"""
Add file upload functionality to the fixed backend
"""

def add_upload_endpoints():
    """Add upload endpoints to the backend"""
    
    upload_code = '''

# File upload dependencies
from fastapi import UploadFile, File, Form
from pathlib import Path
import shutil
import mimetypes

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# File upload models
class FileUploadResponse(BaseModel):
    message: str
    filename: str
    file_size: int
    file_type: str
    file_path: str
    patient_id: str
    upload_time: datetime

# File upload endpoints
@app.post("/patients/{patient_id}/upload", response_model=FileUploadResponse)
async def upload_patient_file(
    patient_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a file for a specific patient."""
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Create patient directory
        patient_dir = uploads_dir / patient_id
        patient_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{file.filename}"
        file_path = patient_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_size = file_path.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # Determine file type
        if file.filename.lower().endswith(('.dcm', '.dicom')):
            file_type = "dicom"
        elif file.filename.lower().endswith(('.pdf',)):
            file_type = "pdf"
        elif file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            file_type = "image"
        else:
            file_type = "other"
        
        logger.info(f"Uploaded file {file.filename} for patient {patient_id}")
        
        return FileUploadResponse(
            message="File uploaded successfully",
            filename=unique_filename,
            file_size=file_size,
            file_type=file_type,
            file_path=str(file_path),
            patient_id=patient_id,
            upload_time=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.post("/patients/{patient_id}/upload/dicom", response_model=FileUploadResponse)
async def upload_dicom_file(
    patient_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a DICOM file for a specific patient."""
    try:
        # Validate DICOM file
        if not file.filename.lower().endswith(('.dcm', '.dicom')):
            if 'dicom' not in file.filename.lower() and not file.filename.lower().endswith('.ima'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be a DICOM file (.dcm, .dicom, or .ima)"
                )
        
        # Use the general upload function
        return await upload_patient_file(patient_id, file, description, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading DICOM file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload DICOM file: {str(e)}")

@app.get("/patients/{patient_id}/files")
async def get_patient_files(patient_id: str, db: Session = Depends(get_db)):
    """Get all uploaded files for a patient."""
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Get patient files directory
        patient_dir = uploads_dir / patient_id
        
        if not patient_dir.exists():
            return {"patient_id": patient_id, "files": [], "total_files": 0}
        
        files = []
        for file_path in patient_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                mime_type, _ = mimetypes.guess_type(str(file_path))
                
                files.append({
                    "filename": file_path.name,
                    "file_size": stat.st_size,
                    "file_type": "dicom" if file_path.suffix.lower() in ['.dcm', '.dicom'] else "other",
                    "mime_type": mime_type,
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
        logger.error(f"Error getting patient files: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# File serving endpoint
from fastapi.responses import FileResponse

@app.get("/uploads/{patient_id}/{filename}")
async def serve_patient_file(patient_id: str, filename: str):
    """Serve uploaded patient files."""
    try:
        file_path = uploads_dir / patient_id / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found for patient {patient_id}"
            )
        
        # Determine media type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if filename.lower().endswith(('.dcm', '.dicom')):
            mime_type = "application/dicom"
        
        return FileResponse(
            path=str(file_path),
            media_type=mime_type or "application/octet-stream",
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
'''
    
    # Read current backend
    with open('fixed_backend.py', 'r') as f:
        content = f.read()
    
    # Find the end of the file (before if __name__ == "__main__")
    if 'if __name__ == "__main__":' in content:
        parts = content.split('if __name__ == "__main__":')
        new_content = parts[0] + upload_code + '\n\nif __name__ == "__main__":' + parts[1]
    else:
        new_content = content + upload_code
    
    # Write updated backend
    with open('fixed_backend.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Added upload endpoints to fixed_backend.py")

if __name__ == "__main__":
    add_upload_endpoints()