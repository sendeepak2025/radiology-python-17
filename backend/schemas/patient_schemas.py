"""Pydantic schemas for Patient API."""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class PatientBase(BaseModel):
    """Base patient schema."""
    patient_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: datetime
    gender: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "USA"
    medical_record_number: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    active: bool = True

    @validator('gender')
    def validate_gender(cls, v):
        if v not in ['M', 'F', 'O']:
            raise ValueError('Gender must be M, F, or O')
        return v

class PatientCreate(PatientBase):
    """Schema for creating a patient."""
    pass

class PatientUpdate(BaseModel):
    """Schema for updating a patient."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    medical_record_number: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    active: Optional[bool] = None

    @validator('gender')
    def validate_gender(cls, v):
        if v is not None and v not in ['M', 'F', 'O']:
            raise ValueError('Gender must be M, F, or O')
        return v

class PatientResponse(PatientBase):
    """Schema for patient response."""
    id: str  # Changed from UUID to str to match the model
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientFileBase(BaseModel):
    """Base patient file schema."""
    filename: str
    original_filename: str
    file_type: str
    mime_type: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    study_uid: Optional[str] = None

class PatientFileCreate(PatientFileBase):
    """Schema for creating a patient file."""
    patient_id: str
    file_path: str
    file_size: int
    uploaded_by: Optional[str] = None

class PatientFileResponse(PatientFileBase):
    """Schema for patient file response."""
    id: str  # Changed from UUID to str to match the model
    file_id: str  # Changed from UUID to str to match the model
    patient_id: str
    file_path: str
    file_size: int
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientWithFiles(PatientResponse):
    """Schema for patient with files."""
    files: List[PatientFileResponse] = []

class PatientListResponse(BaseModel):
    """Schema for patient list response."""
    patients: List[PatientResponse]
    total: int
    page: int
    per_page: int
    total_pages: int