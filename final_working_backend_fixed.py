"""
Final working backend - handles all frontend requests with proper DICOM handling
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
from datetime import datetime
from pathlib import Path
import shutil
import json
import hashlib
import os

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
        
        # Fallback: search by partial match
        for stored_uid, study_data in metadata.items():
            if study_uid in stored_uid or stored_uid in study_uid:
                print(f"[DEBUG] Found study by partial match: {stored_uid}")
                return study_data
        
        print(f"[DEBUG] Study UID not found in metadata")
        return {"error": "Study not found", "requested_uid": study_uid}
        
    except Exception as e:
        print(f"[ERROR] Error in get_study: {str(e)}")
        return {"error": str(e)}

@app.post("/patients/{patient_id}/upload/dicom")
def upload_dicom(patient_id: str, files: UploadFile = File(...)):
    """Upload DICOM files with proper metadata storage"""
    try:
        # Create patient directory in uploads
        patient_dir = uploads_dir / patient_id
        patient_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = patient_dir / files.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(files.file, buffer)
        
        file_size = file_path.stat().st_size
        created_time = datetime.now()
        
        # Generate study UID
        study_uid = generate_study_uid(patient_id, files.filename)
        
        # Create study metadata
        study_data = {
            "study_uid": study_uid,
            "patient_id": patient_id,
            "patient_name": f"Patient {patient_id}",
            "study_date": created_time.strftime("%Y-%m-%d"),
            "study_time": created_time.strftime("%H:%M:%S"),
            "modality": "CT",
            "study_description": f"Uploaded DICOM - {files.filename}",
            "status": "received",
            "original_filename": files.filename,
            "file_size": file_size,
            "dicom_url": f"/uploads/{patient_id}/{files.filename}",
            "created_at": created_time.isoformat(),
            "images": [
                {
                    "image_uid": f"{study_uid}_image_1",
                    "image_number": 1,
                    "image_url": f"/uploads/{patient_id}/{files.filename}"
                }
            ]
        }
        
        # Save metadata
        metadata = load_metadata()
        metadata[study_uid] = study_data
        save_metadata(metadata)
        
        print(f"[DEBUG] Saved study with UID: {study_uid}")
        
        return {
            "message": "File uploaded successfully",
            "filename": files.filename,
            "file_size": file_size,
            "file_type": "dicom",
            "patient_id": patient_id,
            "study_uid": study_uid,
            "upload_time": created_time.isoformat(),
            "file_url": f"/uploads/{patient_id}/{files.filename}"
        }
        
    except Exception as e:
        print(f"[ERROR] Upload error: {str(e)}")
        return {"error": str(e)}

@app.get("/uploads/{patient_id}/{filename}")
def serve_file(patient_id: str, filename: str):
    """Serve uploaded files"""
    try:
        file_path = uploads_dir / patient_id / filename
        
        if file_path.exists():
            return FileResponse(
                path=str(file_path),
                media_type="application/dicom",
                filename=filename
            )
        else:
            return {"error": "File not found"}
            
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)