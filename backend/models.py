"""
SQLAlchemy models for Kiro-mini database schema.
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from datetime import datetime
from enum import Enum

class StudyStatus(str, Enum):
    """Study processing status enumeration."""
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    BILLED = "billed"
    ERROR = "error"

class ReportStatus(str, Enum):
    """Report status enumeration."""
    DRAFT = "draft"
    FINAL = "final"
    BILLED = "billed"

class Patient(Base):
    """Patient model for storing patient information."""
    
    __tablename__ = "patients"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(10), nullable=False)  # M, F, O
    
    # Contact Information
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True, default="USA")
    
    # Medical Information
    medical_record_number = Column(String(50), nullable=True)
    insurance_info = Column(JSON, nullable=True)  # Insurance details
    emergency_contact = Column(JSON, nullable=True)  # Emergency contact info
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    
    # System fields
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    studies = relationship("Study", back_populates="patient", cascade="all, delete-orphan")
    files = relationship("PatientFile", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient(patient_id='{self.patient_id}', name='{self.first_name} {self.last_name}')>"

class PatientFile(Base):
    """Patient file model for storing file information."""
    __tablename__ = "patient_files"
    __table_args__ = {'extend_existing': True}
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # File identification
    file_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # e.g., 'dicom', 'pdf', 'image'
    mime_type = Column(String(100), nullable=False)
    
    # Metadata
    description = Column(Text)
    tags = Column(JSON)  # Array of tags for categorization
    study_uid = Column(String(64), index=True)  # Link to study if applicable
    
    # Upload information
    uploaded_by = Column(String(64))  # User who uploaded the file
    
    # System fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="files")

class Study(Base):
    """Study model for DICOM study metadata."""
    
    __tablename__ = "studies"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    study_uid = Column(String(64), unique=True, nullable=False, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    study_date = Column(DateTime, nullable=True)
    modality = Column(String(16), nullable=False)
    exam_type = Column(String(64), nullable=False)
    study_description = Column(Text, nullable=True)
    series_description = Column(Text, nullable=True)
    status = Column(String(20), default=StudyStatus.RECEIVED, nullable=False)
    orthanc_id = Column(String(64), nullable=True)
    origin = Column(String(64), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="studies")
    reports = relationship("Report", back_populates="study", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="study", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Study(study_uid='{self.study_uid}', patient_id='{self.patient_id}', status='{self.status}')>"

class Report(Base):
    """Report model for structured radiology reports."""
    
    __tablename__ = "reports"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    study_uid = Column(String(64), ForeignKey("studies.study_uid"), nullable=False)
    radiologist_id = Column(String(64), nullable=True)
    exam_type = Column(String(64), nullable=False)
    
    # Report content
    findings = Column(Text, nullable=True)
    measurements = Column(JSON, nullable=True)  # Structured measurements data
    impressions = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    
    # Billing codes
    diagnosis_codes = Column(JSON, nullable=True)  # ICD-10 codes array
    cpt_codes = Column(JSON, nullable=True)  # CPT codes array
    
    # AI and workflow
    status = Column(String(20), default=ReportStatus.DRAFT, nullable=False)
    ai_confidence = Column(Float, nullable=True)
    ai_generated = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    study = relationship("Study", back_populates="reports")
    superbills = relationship("Superbill", back_populates="report", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="report", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Report(report_id='{self.report_id}', study_uid='{self.study_uid}', status='{self.status}')>"

class Superbill(Base):
    """Superbill model for billing information."""
    
    __tablename__ = "superbills"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    superbill_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    report_id = Column(String(36), ForeignKey("reports.report_id"), nullable=False)
    
    # Patient information
    patient_info = Column(JSON, nullable=False)  # Patient demographics and insurance
    
    # Billing information
    services = Column(JSON, nullable=False)  # Array of service line items
    diagnoses = Column(JSON, nullable=False)  # Array of diagnosis codes
    total_charges = Column(Float, nullable=False, default=0.0)
    
    # 837P data
    x12_837p_data = Column(JSON, nullable=True)  # Complete 837P transaction data
    
    # Provider information
    provider_npi = Column(String(10), nullable=False)
    facility_name = Column(String(255), nullable=False)
    facility_address = Column(Text, nullable=True)
    
    # Status and validation
    validated = Column(Boolean, default=False)
    validation_errors = Column(JSON, nullable=True)
    submitted = Column(Boolean, default=False)
    submission_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    report = relationship("Report", back_populates="superbills")
    audit_logs = relationship("AuditLog", back_populates="superbill", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Superbill(superbill_id='{self.superbill_id}', report_id='{self.report_id}', total_charges={self.total_charges})>"

class BillingCode(Base):
    """Billing code mappings and rules."""
    
    __tablename__ = "billing_codes"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code_type = Column(String(10), nullable=False)  # CPT, ICD10, HCPCS
    code = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    
    # Mapping rules
    exam_types = Column(JSON, nullable=True)  # Array of applicable exam types
    modifiers = Column(JSON, nullable=True)  # Array of applicable modifiers
    
    # Billing information
    base_charge = Column(Float, nullable=True)
    relative_value_units = Column(Float, nullable=True)
    
    # Validation rules
    requires_modifier = Column(Boolean, default=False)
    bilateral_applicable = Column(Boolean, default=False)
    age_restrictions = Column(JSON, nullable=True)
    gender_restrictions = Column(String(1), nullable=True)
    
    # Status
    active = Column(Boolean, default=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BillingCode(code='{self.code}', type='{self.code_type}', description='{self.description[:50]}...')>"

class AuditLog(Base):
    """Audit log for HIPAA compliance and system tracking."""
    
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event information
    event_type = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE, LOGIN, etc.
    event_description = Column(Text, nullable=False)
    
    # User information
    user_id = Column(String(64), nullable=True)
    user_role = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Resource information
    resource_type = Column(String(50), nullable=True)  # Study, Report, Superbill
    resource_id = Column(String(64), nullable=True)
    
    # Related entities
    study_uid = Column(String(64), ForeignKey("studies.study_uid"), nullable=True)
    report_id = Column(String(36), ForeignKey("reports.report_id"), nullable=True)
    superbill_id = Column(String(36), ForeignKey("superbills.superbill_id"), nullable=True)
    
    # Additional data
    event_metadata = Column(JSON, nullable=True)  # Additional event-specific data
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    study = relationship("Study", back_populates="audit_logs")
    report = relationship("Report", back_populates="audit_logs")
    superbill = relationship("Superbill", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(event_type='{self.event_type}', resource_type='{self.resource_type}', timestamp='{self.timestamp}')>"

class AIJob(Base):
    """AI processing job tracking."""
    
    __tablename__ = "ai_jobs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    study_uid = Column(String(64), nullable=False)
    exam_type = Column(String(64), nullable=False)
    
    # Job status
    status = Column(String(20), default="queued", nullable=False)  # queued, processing, completed, failed
    progress = Column(Float, default=0.0)
    
    # Results
    result_data = Column(JSON, nullable=True)  # AI analysis results
    confidence_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)  # Processing time in seconds
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<AIJob(job_id='{self.job_id}', study_uid='{self.study_uid}', status='{self.status}')>"


class ReportVersion(Base):
    """Model for storing report version history."""
    
    __tablename__ = "report_versions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    report_id = Column(String(36), ForeignKey("reports.report_id"), nullable=False)
    version_number = Column(String(20), nullable=False)
    
    # Snapshot of report data at this version
    findings = Column(Text, nullable=True)
    measurements = Column(JSON, nullable=True)
    impressions = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    diagnosis_codes = Column(JSON, nullable=True)
    cpt_codes = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False)
    ai_confidence = Column(JSON, nullable=True)
    
    # Version metadata
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    change_summary = Column(Text, nullable=True)
    change_details = Column(JSON, nullable=True)  # Detailed diff of changes
    
    def __repr__(self):
        return f"<ReportVersion(version_id='{self.version_id}', report_id='{self.report_id}', version='{self.version_number}')>"