#!/usr/bin/env python3
"""
Clean Upload Backend - Working DICOM Upload System
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
import json
import time
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Optional

# Initialize FastAPI app
app = FastAPI(
    title="Kiro Clean Upload Backend",
    description="Clean backend with working DICOM upload functionality",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
DB_FILE = "clean_upload.db"

# Database setup
def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create studies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_uid TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_time TEXT NOT NULL,
            description TEXT,
            processing_result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    print("🚀 Clean Upload Backend started successfully!")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0-clean",
        "upload_dir": str(UPLOAD_DIR),
        "database": "connected" if os.path.exists(DB_FILE) else "not_found"
    }

# Upload health check
@app.get("/upload/health")
async def upload_health():
    return {
        "status": "ready",
        "upload_directory": str(UPLOAD_DIR),
        "upload_directory_exists": UPLOAD_DIR.exists(),
        "upload_directory_writable": os.access(UPLOAD_DIR, os.W_OK)
    }

def process_dicom_file(file_path: str):
    """Simple DICOM processing"""
    try:
        # Try to import pydicom
        try:
            import pydicom
            ds = pydicom.dcmread(file_path, force=True)
            
            # Extract basic metadata safely
            metadata = {
                "patient_name": str(getattr(ds, 'PatientName', 'Unknown')),
                "patient_id": str(getattr(ds, 'PatientID', 'Unknown')),
                "study_date": str(getattr(ds, 'StudyDate', '')),
                "modality": str(getattr(ds, 'Modality', 'Unknown')),
                "study_description": str(getattr(ds, 'StudyDescription', '')),
                "file_type": "DICOM"
            }
            
            return {
                "success": True,
                "metadata": metadata,
                "processing_method": "pydicom"
            }
            
        except ImportError:
            # Fallback if pydicom not available
            return {
                "success": True,
                "metadata": {
                    "patient_name": "Unknown",
                    "patient_id": "Unknown",
                    "study_date": "",
                    "modality": "Unknown",
                    "study_description": "DICOM file (pydicom not available)",
                    "file_type": "DICOM"
                },
                "processing_method": "fallback"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processing_method": "failed"
        }

# Main upload endpoint
@app.post("/patients/{patient_id}/upload/dicom")
async def upload_dicom(
    patient_id: str,
    files: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """Upload DICOM files with processing"""
    try:
        print(f"📤 Upload request: patient={patient_id}, file={files.filename}")
        
        # Validate file
        if not files.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Create patient directory
        patient_dir = UPLOAD_DIR / patient_id
        patient_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = patient_dir / files.filename
        
        # Read and save file content
        content = await files.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"💾 File saved: {file_path}")
        
        # Process DICOM file
        processing_result = process_dicom_file(str(file_path))
        print(f"🔬 Processing result: {processing_result}")
        
        # Generate study UID
        study_uid = f"study_{patient_id}_{int(time.time())}"
        
        # Store in database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Insert or update patient
        cursor.execute("""
            INSERT OR IGNORE INTO patients (id, name) 
            VALUES (?, ?)
        """, (patient_id, f"Patient {patient_id}"))
        
        # Insert study
        cursor.execute("""
            INSERT INTO studies (
                study_uid, patient_id, filename, file_path, 
                file_size, upload_time, description, processing_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            study_uid, patient_id, files.filename, str(file_path),
            len(content), datetime.now().isoformat(), 
            description or "DICOM upload", json.dumps(processing_result)
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Study created: {study_uid}")
        
        return {
            "success": True,
            "message": "DICOM file uploaded successfully",
            "study_uid": study_uid,
            "filename": files.filename,
            "file_size": len(content),
            "patient_id": patient_id,
            "upload_time": datetime.now().isoformat(),
            "file_url": f"/uploads/{patient_id}/{files.filename}",
            "processing_result": processing_result
        }
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Get patient studies
@app.get("/patients/{patient_id}/studies")
async def get_patient_studies(patient_id: str):
    """Get all studies for a patient"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT study_uid, filename, file_size, upload_time, 
                   description, processing_result
            FROM studies 
            WHERE patient_id = ?
            ORDER BY upload_time DESC
        """, (patient_id,))
        
        studies = []
        for row in cursor.fetchall():
            study_uid, filename, file_size, upload_time, description, processing_result = row
            studies.append({
                "study_uid": study_uid,
                "filename": filename,
                "file_size": file_size,
                "upload_time": upload_time,
                "description": description,
                "processing_result": json.loads(processing_result) if processing_result else None
            })
        
        conn.close()
        
        return {
            "patient_id": patient_id,
            "studies": studies,
            "total": len(studies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get studies: {str(e)}")

# Get all studies
@app.get("/studies")
async def get_studies(skip: int = 0, limit: int = 100):
    """Get all studies with pagination"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT study_uid, patient_id, filename, file_size, 
                   upload_time, description, processing_result
            FROM studies 
            ORDER BY upload_time DESC
            LIMIT ? OFFSET ?
        """, (limit, skip))
        
        studies = []
        for row in cursor.fetchall():
            study_uid, patient_id, filename, file_size, upload_time, description, processing_result = row
            studies.append({
                "study_uid": study_uid,
                "patient_id": patient_id,
                "filename": filename,
                "file_size": file_size,
                "upload_time": upload_time,
                "description": description,
                "processing_result": json.loads(processing_result) if processing_result else None
            })
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM studies")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "studies": studies,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get studies: {str(e)}")

# Get patients
@app.get("/patients")
async def get_patients():
    """Get all patients"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.name, COUNT(s.id) as study_count
            FROM patients p
            LEFT JOIN studies s ON p.id = s.patient_id
            GROUP BY p.id, p.name
            ORDER BY p.id
        """)
        
        patients = []
        for row in cursor.fetchall():
            patient_id, name, study_count = row
            patients.append({
                "id": patient_id,
                "name": name,
                "study_count": study_count
            })
        
        conn.close()
        
        return patients
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patients: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🏥 Starting Clean Upload Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8002)