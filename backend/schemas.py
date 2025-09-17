"""
Pydantic schemas for request/response validation in Kiro-mini API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enums
class StudyStatusEnum(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    BILLED = "billed"
    ERROR = "error"

class ReportStatusEnum(str, Enum):
    DRAFT = "draft"
    FINAL = "final"
    BILLED = "billed"

class ExamTypeEnum(str, Enum):
    ECHO_COMPLETE = "echo_complete"
    VASCULAR_CAROTID = "vascular_carotid"
    CT_SCAN = "ct_scan"
    MRI_SCAN = "mri_scan"
    XRAY = "xray"
    UNKNOWN = "unknown"

# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }

# Study schemas
class StudyIngest(BaseSchema):
    """Schema for study ingestion from Orthanc webhook."""
    
    study_uid: str = Field(..., description="DICOM Study Instance UID")
    patient_id: str = Field(..., description="Patient ID")
    modality: str = Field(..., description="DICOM Modality")
    study_date: Optional[str] = Field(None, description="Study date (YYYYMMDD)")
    study_description: Optional[str] = Field(None, description="Study description")
    series_description: Optional[str] = Field(None, description="Series description")
    exam_type: str = Field(..., description="Determined exam type")
    orthanc_id: Optional[str] = Field(None, description="Orthanc instance ID")
    origin: Optional[str] = Field(None, description="Request origin")
    timestamp: Optional[str] = Field(None, description="Ingestion timestamp")

class StudyResponse(BaseSchema):
    """Schema for study information response."""
    
    id: uuid.UUID
    study_uid: str
    patient_id: str
    study_date: Optional[datetime]
    modality: str
    exam_type: str
    study_description: Optional[str]
    series_description: Optional[str]
    status: StudyStatusEnum
    orthanc_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Image URLs
    image_urls: Optional[List[str]] = Field(None, description="WADO-RS image URLs")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    
    # Related data
    reports: Optional[List[Dict[str, Any]]] = Field(None, description="Associated reports")

# Measurement schemas
class MeasurementValue(BaseSchema):
    """Schema for individual measurement values."""
    
    value: float = Field(..., description="Measurement value")
    unit: str = Field(..., description="Unit of measurement")
    normal_range: Optional[str] = Field(None, description="Normal range for this measurement")
    abnormal: Optional[bool] = Field(None, description="Whether value is abnormal")

class MeasurementSet(BaseSchema):
    """Schema for a set of measurements."""
    
    measurements: Dict[str, MeasurementValue] = Field(..., description="Dictionary of measurements")
    measurement_type: Optional[str] = Field(None, description="Type of measurement set")
    confidence: Optional[float] = Field(None, description="AI confidence in measurements")

# Report schemas
class ReportCreate(BaseSchema):
    """Schema for creating/updating reports."""
    
    study_uid: str = Field(..., description="Associated study UID")
    radiologist_id: Optional[str] = Field(None, description="Radiologist ID")
    exam_type: ExamTypeEnum = Field(..., description="Exam type")
    
    # Report content
    findings: Optional[str] = Field(None, description="Clinical findings")
    measurements: Optional[Dict[str, Any]] = Field(None, description="Structured measurements")
    impressions: Optional[str] = Field(None, description="Clinical impressions")
    recommendations: Optional[str] = Field(None, description="Recommendations")
    
    # Billing codes
    diagnosis_codes: Optional[List[str]] = Field(None, description="ICD-10 diagnosis codes")
    cpt_codes: Optional[List[str]] = Field(None, description="CPT procedure codes")
    
    # Status and AI
    status: ReportStatusEnum = Field(ReportStatusEnum.DRAFT, description="Report status")
    ai_generated: Optional[bool] = Field(False, description="Whether report was AI-generated")

class ReportResponse(BaseSchema):
    """Schema for report response."""
    
    id: uuid.UUID
    report_id: uuid.UUID
    study_uid: str
    radiologist_id: Optional[str]
    exam_type: str
    
    # Report content
    findings: Optional[str]
    measurements: Optional[Dict[str, Any]]
    impressions: Optional[str]
    recommendations: Optional[str]
    
    # Billing codes
    diagnosis_codes: Optional[List[str]]
    cpt_codes: Optional[List[str]]
    
    # Status and AI
    status: ReportStatusEnum
    ai_confidence: Optional[float]
    ai_generated: bool
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    finalized_at: Optional[datetime]

# Billing schemas
class ServiceLine(BaseSchema):
    """Schema for billing service line item."""
    
    cpt_code: str = Field(..., description="CPT procedure code")
    description: str = Field(..., description="Service description")
    units: int = Field(1, description="Number of units")
    charge: float = Field(..., description="Charge amount")
    modifiers: Optional[List[str]] = Field(None, description="CPT modifiers")

class DiagnosisCode(BaseSchema):
    """Schema for diagnosis code."""
    
    icd10_code: str = Field(..., description="ICD-10 diagnosis code")
    description: str = Field(..., description="Diagnosis description")
    primary: bool = Field(False, description="Whether this is the primary diagnosis")

class PatientInfo(BaseSchema):
    """Schema for patient billing information."""
    
    patient_id: str = Field(..., description="Patient ID")
    name: str = Field(..., description="Patient name")
    dob: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    gender: str = Field(..., description="Patient gender")
    address: Optional[str] = Field(None, description="Patient address")
    insurance: Optional[Dict[str, Any]] = Field(None, description="Insurance information")

class SuperbillCreate(BaseSchema):
    """Schema for creating superbills."""
    
    report_id: uuid.UUID = Field(..., description="Associated report ID")

class SuperbillResponse(BaseSchema):
    """Schema for superbill response."""
    
    id: uuid.UUID
    superbill_id: uuid.UUID
    report_id: uuid.UUID
    
    # Patient and billing info
    patient_info: PatientInfo
    services: List[ServiceLine]
    diagnoses: List[DiagnosisCode]
    total_charges: float
    
    # 837P data
    x12_837p_data: Optional[Dict[str, Any]]
    
    # Provider info
    provider_npi: str
    facility_name: str
    facility_address: Optional[str]
    
    # Status
    validated: bool
    validation_errors: Optional[List[str]]
    submitted: bool
    submission_date: Optional[datetime]
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]

# AI schemas
class AIReportDraft(BaseSchema):
    """Schema for AI-generated report draft."""
    
    study_uid: str
    exam_type: str
    
    # Generated content
    findings: str
    measurements: Dict[str, Any]
    impressions: str
    recommendations: str
    
    # Suggested codes
    suggested_diagnosis_codes: List[str]
    suggested_cpt_codes: List[str]
    
    # AI metadata
    confidence_score: float
    processing_time: float
    model_version: str

class CodeSuggestion(BaseSchema):
    """Schema for diagnosis code suggestions."""
    
    code: str = Field(..., description="ICD-10 or CPT code")
    description: str = Field(..., description="Code description")
    confidence: float = Field(..., description="Confidence score (0-1)")
    category: str = Field(..., description="Code category")
    primary_suggested: bool = Field(False, description="Whether suggested as primary")

class BillingValidation(BaseSchema):
    """Schema for billing code validation results."""
    
    valid: bool = Field(..., description="Whether combination is valid")
    errors: List[str] = Field([], description="Validation errors")
    warnings: List[str] = Field([], description="Validation warnings")
    suggestions: List[str] = Field([], description="Improvement suggestions")
    estimated_reimbursement: Optional[float] = Field(None, description="Estimated reimbursement")
    denial_risk_score: Optional[float] = Field(None, description="Risk of denial (0-1)")

# System schemas
class HealthResponse(BaseSchema):
    """Schema for health check response."""
    
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    services: Dict[str, str] = Field(..., description="Individual service statuses")

class ErrorResponse(BaseSchema):
    """Schema for error responses."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: str = Field(..., description="Request ID for tracking")

# Validators
@validator('study_uid', 'patient_id', pre=True, always=True)
def validate_required_strings(cls, v):
    """Validate required string fields."""
    if not v or not v.strip():
        raise ValueError('Field cannot be empty')
    return v.strip()

@validator('cpt_codes', 'diagnosis_codes', pre=True, always=True)
def validate_code_lists(cls, v):
    """Validate code lists."""
    if v is None:
        return []
    if not isinstance(v, list):
        raise ValueError('Must be a list')
    return [code.strip().upper() for code in v if code and code.strip()]