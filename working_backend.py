"""
Super simple working backend for patients with enhanced DICOM processing
"""

from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import sqlite3
from datetime import datetime
import os
import mimetypes
from typing import Optional
from pathlib import Path

# Import our enhanced DICOM processing modules
from dicom_processor import dicom_processor
from cache_manager import dicom_cache

app = FastAPI()

# Configure MIME types for DICOM files
mimetypes.add_type('application/dicom', '.dcm')
mimetypes.add_type('application/dicom', '.DCM')

# Custom static files handler for DICOM files
class DicomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.lower().endswith(('.dcm', '.DCM')):
            response.headers["content-type"] = "application/dicom"
        return response

# Mount static files for DICOM uploads with proper MIME type
if os.path.exists("uploads"):
    app.mount("/uploads", DicomStaticFiles(directory="uploads"), name="uploads")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow(), "version": "simple-1.0"}

@app.get("/patients")
def get_patients(limit: int = 100):
    try:
        conn = sqlite3.connect('kiro_mini.db')
        cursor = conn.cursor()
        
        # Get patients
        cursor.execute("""
            SELECT patient_id, first_name, last_name, middle_name, date_of_birth, 
                   gender, phone, email, address, city, state, zip_code, 
                   medical_record_number, active, created_at
            FROM patients 
            WHERE active = 1 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        patients = []
        for row in rows:
            patients.append({
                "patient_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "middle_name": row[3],
                "date_of_birth": row[4],
                "gender": row[5],
                "phone": row[6],
                "email": row[7],
                "address": row[8],
                "city": row[9],
                "state": row[10],
                "zip_code": row[11],
                "medical_record_number": row[12],
                "active": bool(row[13]),
                "created_at": row[14]
            })
        
        conn.close()
        
        return {
            "patients": patients,
            "total": len(patients),
            "page": 1,
            "per_page": limit,
            "total_pages": 1
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "patients": [],
            "total": 0,
            "page": 1,
            "per_page": limit,
            "total_pages": 0
        }

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    try:
        conn = sqlite3.connect('kiro_mini.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT patient_id, first_name, last_name, middle_name, date_of_birth, 
                   gender, phone, email, address, city, state, zip_code, 
                   medical_record_number, active, created_at
            FROM patients 
            WHERE patient_id = ? AND active = 1
        """, (patient_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "patient_id": row[0],
                "first_name": row[1],
                "last_name": row[2],
                "middle_name": row[3],
                "date_of_birth": row[4],
                "gender": row[5],
                "phone": row[6],
                "email": row[7],
                "address": row[8],
                "city": row[9],
                "state": row[10],
                "zip_code": row[11],
                "medical_record_number": row[12],
                "active": bool(row[13]),
                "created_at": row[14]
            }
        else:
            return {"error": "Patient not found"}
            
    except Exception as e:
        return {"error": str(e)}

@app.get("/patients/{patient_id}/studies")
def get_patient_studies(patient_id: str):
    """Get studies for a patient from uploaded DICOM files"""
    try:
        import os
        from pathlib import Path
        
        # Check uploads directory
        uploads_dir = Path("uploads") / patient_id
        studies = []
        
        if uploads_dir.exists():
            for file_path in uploads_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.dcm', '.dicom']:
                    stat = file_path.stat()
                    
                    # Generate DICOM-like study UID
                    timestamp = int(stat.st_mtime * 1000000)
                    study_uid = f"1.2.840.113619.2.5.{timestamp}.{len(file_path.name)}.{hash(file_path.name) % 1000000000}"
                    
                    study = {
                        "study_uid": study_uid,
                        "patient_id": patient_id,
                        "study_date": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
                        "study_time": datetime.fromtimestamp(stat.st_ctime).strftime("%H:%M:%S"),
                        "modality": "CT",
                        "study_description": f"Uploaded DICOM - {file_path.name}",
                        "status": "received",
                        "original_filename": file_path.name,
                        "file_size": stat.st_size,
                        "dicom_url": f"/uploads/{patient_id}/{file_path.name}",
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    }
                    studies.append(study)
        
        return {
            "patient_id": patient_id,
            "studies": studies,
            "total_studies": len(studies)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "patient_id": patient_id,
            "studies": [],
            "total_studies": 0
        }

@app.get("/studies")
def get_all_studies():
    """Get all studies from all patients"""
    try:
        import os
        from pathlib import Path
        
        uploads_dir = Path("uploads")
        all_studies = []
        
        if uploads_dir.exists():
            for patient_dir in uploads_dir.iterdir():
                if patient_dir.is_dir():
                    patient_id = patient_dir.name
                    
                    for file_path in patient_dir.iterdir():
                        if file_path.is_file() and file_path.suffix.lower() in ['.dcm', '.dicom']:
                            stat = file_path.stat()
                            
                            # Generate DICOM-like study UID
                            timestamp = int(stat.st_mtime * 1000000)
                            study_uid = f"1.2.840.113619.2.5.{timestamp}.{len(file_path.name)}.{hash(file_path.name) % 1000000000}"
                            
                            study = {
                                "study_uid": study_uid,
                                "patient_id": patient_id,
                                "study_date": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
                                "study_time": datetime.fromtimestamp(stat.st_ctime).strftime("%H:%M:%S"),
                                "modality": "CT",
                                "study_description": f"Uploaded DICOM - {file_path.name}",
                                "status": "received",
                                "original_filename": file_path.name,
                                "file_size": stat.st_size,
                                "dicom_url": f"/uploads/{patient_id}/{file_path.name}",
                                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                            }
                            all_studies.append(study)
        
        return {
            "studies": all_studies,
            "total": len(all_studies)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "studies": [],
            "total": 0
        }

@app.get("/studies/{study_uid:path}")
def get_study(study_uid: str):
    """Get specific study details"""
    try:
        import os
        from pathlib import Path
        
        uploads_dir = Path("uploads")
        
        if uploads_dir.exists():
            for patient_dir in uploads_dir.iterdir():
                if patient_dir.is_dir():
                    patient_id = patient_dir.name
                    
                    for file_path in patient_dir.iterdir():
                        if file_path.is_file() and file_path.suffix.lower() in ['.dcm', '.dicom']:
                            stat = file_path.stat()
                            
                            # Generate the same UID
                            timestamp = int(stat.st_mtime * 1000000)
                            expected_uid = f"1.2.840.113619.2.5.{timestamp}.{len(file_path.name)}.{hash(file_path.name) % 1000000000}"
                            
                            # Check if this matches the requested study
                            if (study_uid == expected_uid or 
                                study_uid in file_path.name or 
                                file_path.stem in study_uid):
                                
                                return {
                                    "study_uid": study_uid,
                                    "patient_id": patient_id,
                                    "study_date": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
                                    "study_time": datetime.fromtimestamp(stat.st_ctime).strftime("%H:%M:%S"),
                                    "modality": "CT",
                                    "study_description": f"Uploaded DICOM - {file_path.name}",
                                    "status": "received",
                                    "original_filename": file_path.name,
                                    "file_size": stat.st_size,
                                    "dicom_url": f"/uploads/{patient_id}/{file_path.name}",
                                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                    "images": [
                                        {
                                            "image_uid": f"{study_uid}_image_1",
                                            "image_number": 1,
                                            "image_url": f"/uploads/{patient_id}/{file_path.name}"
                                        }
                                    ]
                                }
        
        return {"error": "Study not found work"}
        
    except Exception as e:
        return {"error": str(e)}

# Enhanced DICOM Processing Endpoints

@app.get("/dicom/process/{patient_id}/{filename}")
def process_dicom_file(
    patient_id: str,
    filename: str,
    enhancement: Optional[str] = Query(None, description="Enhancement type: clahe, histogram_eq, gamma, adaptive_eq, unsharp_mask"),
    filter_type: Optional[str] = Query(None, description="Filter type: gaussian, median, bilateral, edge_enhance"),
    output_format: str = Query("PNG", description="Output format: PNG, JPEG, TIFF, BMP"),
    width: Optional[int] = Query(None, description="Target width for resizing"),
    height: Optional[int] = Query(None, description="Target height for resizing"),
    frame: Optional[int] = Query(None, description="Specific frame number for multi-frame DICOMs"),
    use_cache: bool = Query(True, description="Use caching for faster processing")
):
    """Process DICOM file with various enhancements and conversions"""
    try:
        file_path = Path("uploads") / patient_id / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="DICOM file not found")
        
        target_size = None
        if width and height:
            target_size = (width, height)
        
        # Handle frame parameter for multi-frame DICOMs
        processing_kwargs = {
            'enhancement': enhancement,
            'filter_type': filter_type,
            'output_format': output_format,
            'target_size': target_size,
            'use_cache': use_cache
        }
        
        # Add frame parameter if specified
        if frame is not None:
            processing_kwargs['frame'] = frame
        
        result = dicom_processor.process_dicom_file(
            str(file_path),
            **processing_kwargs
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/dicom/metadata/{patient_id}/{filename}")
def get_dicom_metadata(patient_id: str, filename: str):
    """Get DICOM metadata without processing the image"""
    try:
        file_path = Path("uploads") / patient_id / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="DICOM file not found")
        
        dicom_data = dicom_processor.load_dicom(str(file_path))
        if dicom_data is None:
            raise HTTPException(status_code=500, detail="Failed to load DICOM file")
        
        metadata = dicom_processor._extract_metadata(dicom_data)
        
        return JSONResponse(content={
            "success": True,
            "metadata": metadata,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dicom/thumbnail/{patient_id}/{filename}")
def get_dicom_thumbnail(
    patient_id: str,
    filename: str,
    size: int = Query(256, description="Thumbnail size (square)")
):
    """Get thumbnail of DICOM image"""
    try:
        file_path = Path("uploads") / patient_id / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="DICOM file not found")
        
        # Check cache first
        cache_key = f"thumbnail_{size}"
        cached_thumbnail = dicom_cache.get(str(file_path), cache_key)
        
        if cached_thumbnail:
            return JSONResponse(content={
                "success": True,
                "thumbnail": cached_thumbnail,
                "cached": True
            })
        
        # Process thumbnail
        dicom_data = dicom_processor.load_dicom(str(file_path))
        if dicom_data is None:
            raise HTTPException(status_code=500, detail="Failed to load DICOM file")
        
        pixel_array = dicom_processor.extract_pixel_array(dicom_data)
        if pixel_array is None:
            raise HTTPException(status_code=500, detail="Failed to extract pixel data")
        
        # Normalize and create thumbnail
        normalized = dicom_processor.normalize_image(pixel_array)
        thumbnail_bytes = dicom_processor.create_thumbnail(normalized, (size, size))
        
        if thumbnail_bytes is None:
            raise HTTPException(status_code=500, detail="Failed to create thumbnail")
        
        import base64
        thumbnail_b64 = base64.b64encode(thumbnail_bytes).decode('utf-8')
        
        # Cache the thumbnail
        dicom_cache.store(str(file_path), thumbnail_b64, cache_key)
        
        return JSONResponse(content={
            "success": True,
            "thumbnail": thumbnail_b64,
            "cached": False
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/stats")
def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = dicom_cache.get_cache_stats()
        return JSONResponse(content={
            "success": True,
            "cache_stats": stats
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache/clear")
def clear_cache(file_path: Optional[str] = Query(None, description="Specific file path to clear, or leave empty to clear all")):
    """Clear cache for specific file or all cache"""
    try:
        dicom_cache.clear_cache(file_path)
        return JSONResponse(content={
            "success": True,
            "message": f"Cache cleared for {file_path if file_path else 'all files'}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dicom/convert/{patient_id}/{filename}")
def convert_dicom_to_format(
    patient_id: str,
    filename: str,
    format: str = Query("PNG", description="Output format: PNG, JPEG, TIFF, BMP"),
    quality: int = Query(95, description="Quality for JPEG (1-100)"),
    enhancement: Optional[str] = Query(None, description="Apply enhancement before conversion")
):
    """Convert DICOM to standard image format"""
    try:
        file_path = Path("uploads") / patient_id / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="DICOM file not found")
        
        result = dicom_processor.process_dicom_file(
            str(file_path),
            enhancement=enhancement,
            output_format=format,
            use_cache=True
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Return the converted image data
        import base64
        image_bytes = base64.b64decode(result['image_data'])
        
        media_type = f"image/{format.lower()}"
        if format.upper() == "JPEG":
            media_type = "image/jpeg"
        
        return Response(
            content=image_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename.rsplit('.', 1)[0]}.{format.lower()}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))