"""
Minimal working backend to test patient data
"""

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Database setup
DATABASE_URL = "sqlite:///./kiro_mini.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
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
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# Pydantic Models
class PatientResponse(BaseModel):
    id: str
    patient_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str]
    date_of_birth: datetime
    gender: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    medical_record_number: Optional[str]
    allergies: Optional[str]
    medical_history: Optional[str]
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

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(title="Minimal Patient API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow(), "version": "1.0.0"}

@app.get("/patients")
async def get_patients(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    per_page: Optional[int] = Query(None, ge=1, le=1000),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    try:
        # Handle pagination
        items_per_page = limit or per_page or 20
        offset = (page - 1) * items_per_page
        
        # Get patients
        query = db.query(Patient).filter(Patient.active == True)
        total = query.count()
        patients = query.offset(offset).limit(items_per_page).all()
        
        total_pages = (total + items_per_page - 1) // items_per_page
        
        return {
            "patients": patients,
            "total": total,
            "page": page,
            "per_page": items_per_page,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"error": str(e), "patients": [], "total": 0, "page": 1, "per_page": 20, "total_pages": 0}

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()
    
    if not patient:
        return {"error": "Patient not found"}
    
    return patient

@app.get("/debug/patients/count")
async def debug_patient_count(db: Session = Depends(get_db)):
    try:
        total = db.query(Patient).count()
        active = db.query(Patient).filter(Patient.active == True).count()
        
        return {
            "total_patients": total,
            "active_patients": active,
            "version": "minimal-1.0.0"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)