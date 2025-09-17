"""
Fixed backend for Kiro patient management system.
Works with existing kiro_mini.db database and handles both limit and per_page parameters.
"""

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, date
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup - using existing kiro_mini.db
DATABASE_URL = "sqlite:///./kiro_mini.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models - matching existing schema
class Patient(Base):
    """Patient model matching existing kiro_mini.db schema."""
    __tablename__ = "patients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(10), nullable=False)
    
    # Contact Information
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Medical Information
    medical_record_number = Column(String(50), nullable=True)
    insurance_info = Column(JSON, nullable=True)
    emergency_contact = Column(JSON, nullable=True)
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    
    # System fields
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# Pydantic Models
class PatientBase(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=64)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date
    gender: str = Field(..., pattern="^(M|F|O)$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    medical_record_number: Optional[str] = Field(None, max_length=50)
    allergies: Optional[str] = None
    medical_history: Optional[str] = None

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(M|F|O)$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    medical_record_number: Optional[str] = Field(None, max_length=50)
    allergies: Optional[str] = None
    medical_history: Optional[str] = None

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class PatientResponse(PatientBase):
    id: str
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

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(
    title="Kiro Patient API (Fixed)",
    description="Fixed patient data management system working with existing database",
    version="1.0.1"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.1"
    )

# Patient endpoints with flexible parameter handling
@app.get("/patients", response_model=PatientListResponse)
async def get_patients(
    search: Optional[str] = Query(None, description="Search by name, patient ID, or MRN"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: Optional[int] = Query(None, ge=1, le=1000, description="Items per page"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Items per page (alternative to per_page)"),
    skip: Optional[int] = Query(None, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db)
):
    """Get all patients with optional search and pagination. Supports both limit/skip and page/per_page formats."""
    try:
        logger.info(f"🔍 GET /patients called with search='{search}', page={page}, per_page={per_page}, limit={limit}, skip={skip}")
        
        # Handle different pagination parameter formats
        if limit is not None:
            # Frontend is using limit parameter
            items_per_page = limit
            if skip is not None:
                # Calculate page from skip
                current_page = (skip // limit) + 1 if limit > 0 else 1
            else:
                current_page = page
        else:
            # Use per_page parameter or default
            items_per_page = per_page or 20
            current_page = page
        
        # Calculate offset
        if skip is not None:
            offset = skip
        else:
            offset = (current_page - 1) * items_per_page
        
        logger.info(f"Calculated: page={current_page}, per_page={items_per_page}, offset={offset}")
        
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
        patients = query.offset(offset).limit(items_per_page).all()
        logger.info(f"✓ Retrieved {len(patients)} patients")
        
        # Calculate pagination info
        total_pages = (total + items_per_page - 1) // items_per_page
        
        return PatientListResponse(
            patients=patients,
            total=total,
            page=current_page,
            per_page=items_per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error retrieving patients: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get a specific patient by ID."""
    try:
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        return patient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient_data: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient."""
    try:
        # Check if patient ID already exists
        existing_patient = db.query(Patient).filter(
            Patient.patient_id == patient_data.patient_id
        ).first()
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
        
        logger.info(f"Created patient: {patient_data.patient_id}")
        return db_patient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing patient."""
    try:
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Check if MRN already exists for another patient (if updating MRN)
        if (patient_data.medical_record_number and 
            patient_data.medical_record_number != patient.medical_record_number):
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
        
        logger.info(f"Updated patient: {patient_id}")
        return patient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating patient: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """Soft delete a patient (mark as inactive)."""
    try:
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Soft delete by marking as inactive
        patient.active = False
        db.commit()
        
        logger.info(f"Deleted patient: {patient_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting patient: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Debug endpoint to check database connection
@app.get("/debug/patients/count")
async def debug_patient_count(db: Session = Depends(get_db)):
    """Debug endpoint to check patient count."""
    try:
        total_patients = db.query(Patient).count()
        active_patients = db.query(Patient).filter(Patient.active == True).count()
        
        return {
            "total_patients": total_patients,
            "active_patients": active_patients,
            "database_url": DATABASE_URL
        }
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")