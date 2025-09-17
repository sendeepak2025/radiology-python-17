"""
Study service for managing DICOM study ingestion and metadata.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Study, StudyStatus, AuditLog
# Import directly from schemas.py file
import importlib.util
import os
schemas_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas.py')
spec = importlib.util.spec_from_file_location("schemas_module", schemas_path)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)

StudyIngest = schemas_module.StudyIngest
StudyResponse = schemas_module.StudyResponse
from services.orthanc_service import OrthancService
from services.audit_service import AuditService
import uuid

logger = logging.getLogger(__name__)

class StudyService:
    """Service for managing study operations."""
    
    def __init__(self):
        self.orthanc_service = OrthancService()
        self.audit_service = AuditService()
    
    async def create_or_update_study(
        self, 
        db: Session, 
        study_uid: str, 
        study_data: StudyIngest
    ) -> Study:
        """
        Create or update study record from Orthanc webhook data.
        """
        try:
            # Check if study already exists
            existing_study = db.query(Study).filter(
                Study.study_uid == study_uid
            ).first()
            
            if existing_study:
                # Update existing study
                existing_study.status = StudyStatus.PROCESSING
                existing_study.updated_at = datetime.utcnow()
                
                # Update fields if provided
                if study_data.study_description:
                    existing_study.study_description = study_data.study_description
                if study_data.series_description:
                    existing_study.series_description = study_data.series_description
                if study_data.orthanc_id:
                    existing_study.orthanc_id = study_data.orthanc_id
                
                study = existing_study
                action = "UPDATE"
                
            else:
                # Parse study date
                study_date = None
                if study_data.study_date:
                    try:
                        study_date = datetime.strptime(study_data.study_date, "%Y%m%d")
                    except ValueError:
                        logger.warning(f"Invalid study date format: {study_data.study_date}")
                
                # Create new study
                study = Study(
                    study_uid=study_uid,
                    patient_id=study_data.patient_id,
                    study_date=study_date,
                    modality=study_data.modality,
                    exam_type=study_data.exam_type,
                    study_description=study_data.study_description,
                    series_description=study_data.series_description,
                    status=StudyStatus.PROCESSING,
                    orthanc_id=study_data.orthanc_id,
                    origin=study_data.origin
                )
                
                db.add(study)
                action = "CREATE"
            
            # Commit changes
            db.commit()
            db.refresh(study)
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type=f"STUDY_{action}",
                event_description=f"Study {action.lower()}d via Orthanc webhook",
                resource_type="Study",
                resource_id=study_uid,
                study_uid=study_uid,
                metadata={
                    "exam_type": study_data.exam_type,
                    "modality": study_data.modality,
                    "patient_id": study_data.patient_id,
                    "origin": study_data.origin
                }
            )
            
            logger.info(f"Study {action.lower()}d successfully: {study_uid}")
            return study
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating/updating study {study_uid}: {str(e)}")
            raise
    
    async def get_study_with_images(
        self, 
        db: Session, 
        study_uid: str
    ) -> Optional[StudyResponse]:
        """
        Retrieve study with associated image URLs from Orthanc.
        """
        try:
            # Get study from database
            study = db.query(Study).filter(
                Study.study_uid == study_uid
            ).first()
            
            if not study:
                return None
            
            # Get image URLs from Orthanc and local uploads
            image_urls = []
            thumbnail_url = None
            
            # First, try to get images from Orthanc
            if study.orthanc_id:
                try:
                    image_urls = await self.orthanc_service.get_study_image_urls(study_uid)
                    thumbnail_url = await self.orthanc_service.get_study_thumbnail_url(study_uid)
                except Exception as e:
                    logger.warning(f"Failed to get images from Orthanc for study {study_uid}: {str(e)}")
            
            # If no Orthanc images, check for locally uploaded DICOM files
            if not image_urls:
                try:
                    from models import PatientFile
                    # Get DICOM files for this patient that could be part of this study
                    dicom_files = db.query(PatientFile).filter(
                        PatientFile.patient_id == study.patient_id,
                        PatientFile.file_type == "dicom"
                    ).all()
                    
                    # Build image URLs for local DICOM files
                    for dicom_file in dicom_files:
                        # Create URL that matches our new serving endpoint
                        image_url = f"http://localhost:8000/uploads/{study.patient_id}/{dicom_file.original_filename}"
                        image_urls.append(image_url)
                        logger.info(f"Added local DICOM file URL: {image_url}")
                    
                    if image_urls:
                        logger.info(f"Found {len(image_urls)} local DICOM files for study {study_uid}")
                        
                except Exception as e:
                    logger.warning(f"Failed to get local DICOM files for study {study_uid}: {str(e)}")
            
            # Get associated reports
            reports = []
            for report in study.reports:
                reports.append({
                    "report_id": str(report.report_id),
                    "status": report.status,
                    "created_at": report.created_at.isoformat(),
                    "finalized_at": report.finalized_at.isoformat() if report.finalized_at else None,
                    "ai_generated": report.ai_generated
                })
            
            # Log access event
            await self.audit_service.log_event(
                db=db,
                event_type="STUDY_ACCESS",
                event_description=f"Study accessed for viewing",
                resource_type="Study",
                resource_id=study_uid,
                study_uid=study_uid
            )
            
            # Create response
            response = StudyResponse(
                id=study.id,
                study_uid=study.study_uid,
                patient_id=study.patient_id,
                study_date=study.study_date,
                modality=study.modality,
                exam_type=study.exam_type,
                study_description=study.study_description,
                series_description=study.series_description,
                status=study.status,
                orthanc_id=study.orthanc_id,
                created_at=study.created_at,
                updated_at=study.updated_at,
                image_urls=image_urls,
                thumbnail_url=thumbnail_url,
                reports=reports
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving study {study_uid}: {str(e)}")
            raise
    
    async def list_studies(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        patient_id: Optional[str] = None,
        exam_type: Optional[str] = None,
        modality: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List studies with optional filtering.
        """
        try:
            query = db.query(Study)
            
            # Apply filters
            if status:
                query = query.filter(Study.status == status)
            if patient_id:
                query = query.filter(Study.patient_id.ilike(f"%{patient_id}%"))
            if exam_type:
                query = query.filter(Study.exam_type == exam_type)
            if modality:
                query = query.filter(Study.modality == modality)
            
            # Order by creation date (newest first)
            query = query.order_by(Study.created_at.desc())
            
            # Apply pagination
            studies = query.offset(skip).limit(limit).all()
            
            # Convert to response format
            result = []
            for study in studies:
                # Get report count
                report_count = len(study.reports)
                latest_report = None
                if study.reports:
                    latest_report = max(study.reports, key=lambda r: r.created_at)
                
                study_dict = {
                    "id": str(study.id),
                    "study_uid": study.study_uid,
                    "patient_id": study.patient_id,
                    "study_date": study.study_date.isoformat() if study.study_date else None,
                    "modality": study.modality,
                    "exam_type": study.exam_type,
                    "study_description": study.study_description,
                    "status": study.status,
                    "created_at": study.created_at.isoformat(),
                    "report_count": report_count,
                    "latest_report_status": latest_report.status if latest_report else None,
                    "latest_report_date": latest_report.created_at.isoformat() if latest_report else None
                }
                result.append(study_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing studies: {str(e)}")
            raise
    
    async def update_study_status(
        self,
        db: Session,
        study_uid: str,
        status: StudyStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Study]:
        """
        Update study status and log the change.
        """
        try:
            study = db.query(Study).filter(
                Study.study_uid == study_uid
            ).first()
            
            if not study:
                return None
            
            old_status = study.status
            study.status = status
            study.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(study)
            
            # Log status change
            await self.audit_service.log_event(
                db=db,
                event_type="STUDY_STATUS_CHANGE",
                event_description=f"Study status changed from {old_status} to {status}",
                resource_type="Study",
                resource_id=study_uid,
                study_uid=study_uid,
                metadata={
                    "old_status": old_status,
                    "new_status": status,
                    **(metadata or {})
                }
            )
            
            logger.info(f"Study {study_uid} status updated to {status}")
            return study
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating study status {study_uid}: {str(e)}")
            raise
    
    async def get_study_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Get study statistics for dashboard.
        """
        try:
            total_studies = db.query(Study).count()
            
            # Count by status
            status_counts = {}
            for status in StudyStatus:
                count = db.query(Study).filter(Study.status == status.value).count()
                status_counts[status.value] = count
            
            # Count by exam type
            exam_type_counts = {}
            exam_types = db.query(Study.exam_type).distinct().all()
            for (exam_type,) in exam_types:
                count = db.query(Study).filter(Study.exam_type == exam_type).count()
                exam_type_counts[exam_type] = count
            
            # Recent studies (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_studies = db.query(Study).filter(
                Study.created_at >= yesterday
            ).count()
            
            return {
                "total_studies": total_studies,
                "status_counts": status_counts,
                "exam_type_counts": exam_type_counts,
                "recent_studies": recent_studies,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting study statistics: {str(e)}")
            raise
    
    async def search_studies(
        self,
        db: Session,
        search_term: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search studies by patient ID, study description, or study UID.
        """
        try:
            search_pattern = f"%{search_term}%"
            
            studies = db.query(Study).filter(
                or_(
                    Study.patient_id.ilike(search_pattern),
                    Study.study_uid.ilike(search_pattern),
                    Study.study_description.ilike(search_pattern),
                    Study.series_description.ilike(search_pattern)
                )
            ).order_by(Study.created_at.desc()).limit(limit).all()
            
            result = []
            for study in studies:
                study_dict = {
                    "study_uid": study.study_uid,
                    "patient_id": study.patient_id,
                    "study_description": study.study_description,
                    "exam_type": study.exam_type,
                    "modality": study.modality,
                    "status": study.status,
                    "created_at": study.created_at.isoformat()
                }
                result.append(study_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching studies: {str(e)}")
            raise