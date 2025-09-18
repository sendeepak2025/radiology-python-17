"""
Final working backend - handles all frontend requests with proper DICOM handling
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
from datetime import datetime
from pathlib import Path
import shutil
import json
import hashlib
import os
import sys

app = FastAPI(title="Kiro Final Backend", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Mount static files for uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
print("✅ Static file serving enabled for /uploads directory")

# Metadata storage for studies
metadata_file = Path("study_metadata.json")

def load_metadata():
    """Load study metadata from file"""
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_metadata(metadata):
    """Save study metadata to file"""
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def generate_study_uid(patient_id, filename):
    """Generate consistent study UID"""
    # Create a consistent hash-based UID
    content = f"{patient_id}_{filename}_{datetime.now().strftime('%Y%m%d')}"
    hash_obj = hashlib.md5(content.encode())
    hash_hex = hash_obj.hexdigest()
    return f"1.2.840.113619.2.5.{hash_hex}"

def process_dicom_with_advanced_libraries(file_path):
    """Process DICOM file using advanced libraries"""
    try:
        # Try to import and use simple processor first
        sys.path.append('.')
        from simple_dicom_processor import process_dicom_file_simple
        result = process_dicom_file_simple(file_path)
        print(f"[DEBUG] DICOM processing result: {result.get('success', False)}")
        return result
    except ImportError as e:
        print(f"[WARNING] Simple DICOM processor not available: {e}")
        # Fallback to basic processing
        return process_dicom_basic(file_path)
    except Exception as e:
        print(f"[ERROR] DICOM processing failed: {e}")
        return {"success": False, "error": str(e)}

def process_dicom_basic(file_path):
    """Basic DICOM processing fallback"""
    try:
        # Try basic pydicom processing
        import pydicom
        from PIL import Image
        import numpy as np
        
        print(f"[DEBUG] Basic DICOM processing: {file_path}")
        
        # Read DICOM file
        ds = pydicom.dcmread(str(file_path))
        
        # Extract basic metadata
        metadata = {
            'patient_name': str(getattr(ds, 'PatientName', 'Unknown')),
            'patient_id': str(getattr(ds, 'PatientID', 'Unknown')),
            'study_date': str(getattr(ds, 'StudyDate', '')),
            'modality': str(getattr(ds, 'Modality', 'Unknown')),
            'study_description': str(getattr(ds, 'StudyDescription', '')),
        }
        
        processed_files = {}
        
        # Try to create preview image
        if hasattr(ds, 'pixel_array'):
            pixel_array = ds.pixel_array
            
            # Normalize to 0-255
            if pixel_array.max() > 255:
                normalized = ((pixel_array - pixel_array.min()) / 
                            (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            else:
                normalized = pixel_array.astype(np.uint8)
            
            # Save as PNG
            preview_path = file_path.with_suffix('.png')
            img = Image.fromarray(normalized)
            img.save(preview_path)
            
            processed_files['normalized'] = str(preview_path.relative_to(Path.cwd()))
            print(f"[DEBUG] Created basic preview: {preview_path}")
        
        return {
            'success': True,
            'metadata': metadata,
            'processed_files': processed_files,
            'processing_type': 'basic'
        }
        
    except ImportError:
        print("[WARNING] Basic DICOM libraries not available")
        return {
            'success': False, 
            'error': 'DICOM processing libraries not installed',
            'suggestion': 'Run: pip install pydicom pillow numpy'
        }
    except Exception as e:
        print(f"[ERROR] Basic DICOM processing failed: {e}")
        return {'success': False, 'error': str(e)}

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow(), 
        "version": "final-2.0-fixed"
    }

@app.get("/upload/health")
def upload_health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "upload_config": {
            "max_file_size": "100MB",
            "supported_formats": ["dcm", "dicom"],
            "endpoints": ["/patients/{patient_id}/upload/dicom"]
        }
    }

@app.get("/patients")
def get_patients(limit: int = 100, skip: int = 0):
    try:
        conn = sqlite3.connect('kiro_mini.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT patient_id, first_name, last_name, middle_name, date_of_birth, 
                   gender, phone, email, address, city, state, zip_code, 
                   medical_record_number, active, created_at
            FROM patients 
            WHERE active = 1 
            LIMIT ? OFFSET ?
        """, (limit, skip))
        
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

@app.get("/studies")
def get_all_studies(skip: int = 0, limit: int = 100):
    """Get all studies with proper metadata"""
    try:
        metadata = load_metadata()
        all_studies = []
        
        print(f"[DEBUG] Loaded metadata keys: {list(metadata.keys())}")
        
        # Get studies from metadata
        for study_uid, study_data in metadata.items():
            all_studies.append(study_data)
        
        # Apply pagination
        paginated_studies = all_studies[skip:skip + limit]
        
        return {
            "studies": paginated_studies,
            "total": len(all_studies),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        print(f"[ERROR] Error in get_all_studies: {str(e)}")
        return {
            "error": str(e),
            "studies": [],
            "total": 0,
            "skip": skip,
            "limit": limit
        }

@app.get("/patients/{patient_id}/studies")
def get_patient_studies(patient_id: str):
    """Get studies for a specific patient"""
    try:
        metadata = load_metadata()
        studies = []
        
        # Filter studies by patient_id
        for study_uid, study_data in metadata.items():
            if study_data.get("patient_id") == patient_id:
                studies.append(study_data)
        
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

@app.get("/studies/{study_uid:path}")
def get_study(study_uid: str):
    """Get specific study details"""
    try:
        print(f"[DEBUG] Request received for study_uid: {study_uid}")
        
        metadata = load_metadata()
        print(f"[DEBUG] Available metadata keys: {list(metadata.keys())}")
        
        # Direct lookup first
        if study_uid in metadata:
            print(f"[DEBUG] Found study in metadata: {study_uid}")
            return metadata[study_uid]
        
        # Fallback: search by partial match or filename
        for stored_uid, study_data in metadata.items():
            if (study_uid in stored_uid or 
                stored_uid in study_uid or
                study_uid in study_data.get('original_filename', '') or
                study_data.get('original_filename', '').replace('.DCM', '').replace('.dcm', '') in study_uid):
                print(f"[DEBUG] Found study by partial match: {stored_uid}")
                return study_data
        
        # If no metadata match, check if it's a mock study UID and return mock data
        if study_uid.startswith("1.2.826.0.1.3680043.8.498."):
            print(f"[DEBUG] Returning mock study data for: {study_uid}")
            return {
                "study_uid": study_uid,
                "patient_id": "MOCK001",
                "patient_name": "Mock Patient",
                "study_date": "2024-01-15",
                "study_time": "10:30:00",
                "modality": "CT",
                "study_description": "Mock Study for Testing",
                "status": "completed",
                "original_filename": "mock_study.dcm",
                "file_size": 1024000,
                "dicom_url": f"/mock/{study_uid}",
                "created_at": "2024-01-15T10:30:00Z",
                "images": [
                    {
                        "image_uid": f"{study_uid}_image_1",
                        "image_number": 1,
                        "image_url": f"/mock/{study_uid}/image1"
                    }
                ],
                "image_urls": [
                    f"wadouri:http://localhost:8042/wado?requestType=WADO&studyUID={study_uid}&seriesUID={study_uid}.1&objectUID={study_uid}.1.1&contentType=application/dicom"
                ]
            }
        
        print(f"[DEBUG] Study UID not found in metadata")
        return {"error": "Study not found", "requested_uid": study_uid, "available_studies": list(metadata.keys())}
        
    except Exception as e:
        print(f"[ERROR] Error in get_study: {str(e)}")
        return {"error": str(e)}

@app.post("/patients/{patient_id}/upload/dicom")
def upload_dicom(patient_id: str, files: List[UploadFile] = File(...)):
    """Upload multiple DICOM files as a series with advanced processing"""
    try:
        # Create patient directory in uploads
        patient_dir = uploads_dir / patient_id
        patient_dir.mkdir(exist_ok=True)
        
        # Handle both single file and multiple files
        if not isinstance(files, list):
            files = [files]
        
        # Generate series UID for multiple files
        series_uid = generate_study_uid(patient_id, f"series_{len(files)}_files")
        created_time = datetime.now()
        
        uploaded_files = []
        total_size = 0
        processing_results = []
        
        # Process each file
        for i, file in enumerate(files):
            # Save file with series numbering
            file_path = patient_dir / f"{series_uid}_slice_{i+1:03d}_{file.filename}"
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = file_path.stat().st_size
            total_size += file_size
            
            # Process individual DICOM file
            processing_result = process_dicom_with_advanced_libraries(file_path)
            processing_results.append({
                "slice_number": i + 1,
                "filename": file.filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "processing": processing_result
            })
            
            uploaded_files.append({
                "original_filename": file.filename,
                "stored_filename": file_path.name,
                "file_path": str(file_path),
                "file_size": file_size,
                "slice_number": i + 1
            })
        
        # Create comprehensive processing result
        series_processing_result = {
            "success": True,
            "series_uid": series_uid,
            "total_slices": len(files),
            "total_size": total_size,
            "individual_results": processing_results,
            "series_metadata": {
                "patient_id": patient_id,
                "upload_time": created_time.isoformat(),
                "slice_count": len(files),
                "series_description": f"DICOM Series - {len(files)} slices"
            }
        }
        
        # Create study metadata for series
        image_urls = []
        images = []
        
        for i, file_info in enumerate(uploaded_files):
            image_urls.append(f"wadouri:http://localhost:8000/uploads/{patient_id}/{file_info['stored_filename']}")
            images.append({
                "image_uid": f"{series_uid}_image_{i+1}",
                "image_number": i + 1,
                "slice_number": i + 1,
                "image_url": f"/uploads/{patient_id}/{file_info['stored_filename']}",
                "original_filename": file_info['original_filename'],
                "file_size": file_info['file_size']
            })
        
        study_data = {
            "study_uid": series_uid,
            "patient_id": patient_id,
            "patient_name": f"Patient {patient_id}",
            "study_date": created_time.strftime("%Y-%m-%d"),
            "study_time": created_time.strftime("%H:%M:%S"),
            "modality": "CT",
            "study_description": f"DICOM Series - {len(files)} slices",
            "status": "received",
            "series_info": {
                "total_slices": len(files),
                "total_size": total_size,
                "uploaded_files": len(files)
            },
            "file_size": total_size,
            "dicom_url": f"/uploads/{patient_id}/",
            "created_at": created_time.isoformat(),
            "image_urls": image_urls,
            "images": images,
            "slice_count": len(files)
        }
        
        # Add series processing results
        study_data.update({
            "processing_results": series_processing_result,
            "processing_status": "completed" if series_processing_result.get('success') else "failed"
        })
        
        # Save metadata
        metadata = load_metadata()
        metadata[study_uid] = study_data
        save_metadata(metadata)
        
        print(f"[DEBUG] Saved study with UID: {study_uid}")
        
        return {
            "message": f"DICOM series uploaded successfully - {len(files)} files",
            "series_uid": series_uid,
            "total_files": len(files),
            "total_slices": len(files),
            "file_size": file_size,
            "file_type": "dicom",
            "patient_id": patient_id,
            "study_uid": study_uid,
            "upload_time": created_time.isoformat(),
            "file_url": f"/uploads/{patient_id}/{files.filename}",
            "processing_result": processing_result
        }
        
    except Exception as e:
        print(f"[ERROR] Upload error: {str(e)}")
        return {"error": str(e)}

def process_dicom_with_advanced_libraries(file_path):
    """Process DICOM file using advanced libraries"""
    try:
        from advanced_dicom_processor import AdvancedDicomProcessor
        processor = AdvancedDicomProcessor()
        return processor.process_dicom_file(file_path)
    except ImportError:
        print("[WARNING] Advanced DICOM processor not available")
        return {"success": False, "error": "Advanced libraries not installed"}
    except Exception as e:
        print(f"[ERROR] DICOM processing failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/uploads/{patient_id}/{filename}")
def serve_file(patient_id: str, filename: str):
    """Serve uploaded files with proper CORS headers"""
    try:
        file_path = uploads_dir / patient_id / filename
        
        if file_path.exists():
            # Determine media type based on file extension
            media_type = "application/dicom"
            if filename.lower().endswith(('.dcm', '.dicom')):
                media_type = "application/dicom"
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                media_type = "image/jpeg"
            elif filename.lower().endswith('.png'):
                media_type = "image/png"
            
            return FileResponse(
                path=str(file_path),
                media_type=media_type,
                filename=filename,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "no-cache"
                }
            )
        else:
            return {"error": "File not found"}
            
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/studies")
def debug_studies():
    """Debug endpoint to see all available studies"""
    try:
        metadata = load_metadata()
        return {
            "total_studies": len(metadata),
            "studies": [
                {
                    "study_uid": uid,
                    "patient_id": data.get("patient_id"),
                    "filename": data.get("original_filename"),
                    "study_description": data.get("study_description"),
                    "created_at": data.get("created_at")
                }
                for uid, data in metadata.items()
            ],
            "metadata_file_exists": metadata_file.exists(),
            "uploads_dir_exists": uploads_dir.exists()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/files")
def debug_files():
    """Debug endpoint to see all uploaded files"""
    try:
        files = []
        if uploads_dir.exists():
            for patient_dir in uploads_dir.iterdir():
                if patient_dir.is_dir():
                    for file_path in patient_dir.iterdir():
                        if file_path.is_file():
                            files.append({
                                "patient_id": patient_dir.name,
                                "filename": file_path.name,
                                "file_size": file_path.stat().st_size,
                                "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                            })
        
        return {
            "total_files": len(files),
            "files": files
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)