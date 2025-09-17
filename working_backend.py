"""
Super simple working backend for patients
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime

app = FastAPI()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)