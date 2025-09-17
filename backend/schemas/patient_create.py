"""
Patient creation schemas for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime, date
import re

class PatientCreateRequest(BaseModel):
    """Schema for creating a new patient."""
    
    # Required fields
    patient_id: str = Field(..., min_length=1, max_length=64, description="Unique patient identifier")
    first_name: str = Field(..., min_length=1, max_length=100, description="Patient's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Patient's last name")
    date_of_birth: date = Field(..., description="Patient's date of birth (YYYY-MM-DD)")
    gender: str = Field(..., pattern="^[MFO]$", description="Patient's gender (M/F/O)")
    
    # Optional personal information
    middle_name: Optional[str] = Field(None, max_length=100, description="Patient's middle name")
    
    # Optional contact information
    phone: Optional[str] = Field(None, max_length=20, description="Patient's phone number")
    email: Optional[str] = Field(None, max_length=255, description="Patient's email address")
    address: Optional[str] = Field(None, description="Patient's street address")
    city: Optional[str] = Field(None, max_length=100, description="Patient's city")
    state: Optional[str] = Field(None, max_length=50, description="Patient's state")
    zip_code: Optional[str] = Field(None, max_length=20, description="Patient's ZIP code")
    country: Optional[str] = Field("USA", max_length=100, description="Patient's country")
    
    # Optional medical information
    medical_record_number: Optional[str] = Field(None, max_length=50, description="Medical record number")
    insurance_info: Optional[Dict[str, Any]] = Field(None, description="Insurance information")
    emergency_contact: Optional[Dict[str, Any]] = Field(None, description="Emergency contact information")
    allergies: Optional[str] = Field(None, description="Patient allergies")
    medical_history: Optional[str] = Field(None, description="Patient medical history")
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^[\+]?[1-9][\d]{0,15}$', v.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v

class PatientCreateResponse(BaseModel):
    """Schema for patient creation response."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    patient_id: str = Field(..., description="Created patient ID")
    id: str = Field(..., description="Internal patient UUID")
    
    class Config:
        from_attributes = True