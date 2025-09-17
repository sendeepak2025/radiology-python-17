"""
Report service for managing structured radiology reports.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Report, Study, ReportStatus, AuditLog
# Import directly from schemas.py file
import importlib.util
import os
schemas_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas.py')
spec = importlib.util.spec_from_file_location("schemas_module", schemas_path)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)

ReportCreate = schemas_module.ReportCreate
ReportResponse = schemas_module.ReportResponse
from services.audit_service import AuditService
import uuid

logger = logging.getLogger(__name__)

class ReportService:
    """Service for managing report operations."""
    
    def __init__(self):
        self.audit_service = AuditService()
    
    async def create_or_update_report(
        self, 
        db: Session, 
        report_data: ReportCreate,
        user_id: Optional[str] = None
    ) -> ReportResponse:
        """
        Create or update a structured report.
        """
        try:
            # Check if report already exists for this study
            existing_report = db.query(Report).filter(
                Report.study_uid == report_data.study_uid,
                Report.status != ReportStatus.BILLED  # Don't update billed reports
            ).first()
            
            if existing_report:
                # Update existing report
                old_data = {
                    "findings": existing_report.findings,
                    "measurements": existing_report.measurements,
                    "impressions": existing_report.impressions,
                    "status": existing_report.status
                }
                
                # Update fields
                existing_report.findings = report_data.findings
                existing_report.measurements = report_data.measurements
                existing_report.impressions = report_data.impressions
                existing_report.recommendations = report_data.recommendations
                existing_report.diagnosis_codes = report_data.diagnosis_codes
                existing_report.cpt_codes = report_data.cpt_codes
                existing_report.status = report_data.status
                existing_report.updated_at = datetime.utcnow()
                
                if report_data.radiologist_id:
                    existing_report.radiologist_id = report_data.radiologist_id
                
                # Set finalized timestamp if status is final
                if report_data.status == ReportStatus.FINAL and not existing_report.finalized_at:
                    existing_report.finalized_at = datetime.utcnow()
                
                report = existing_report
                action = "UPDATE"
                
            else:
                # Create new report
                report = Report(
                    study_uid=report_data.study_uid,
                    radiologist_id=report_data.radiologist_id or user_id,
                    exam_type=report_data.exam_type,
                    findings=report_data.findings,
                    measurements=report_data.measurements,
                    impressions=report_data.impressions,
                    recommendations=report_data.recommendations,
                    diagnosis_codes=report_data.diagnosis_codes,
                    cpt_codes=report_data.cpt_codes,
                    status=report_data.status,
                    ai_generated=report_data.ai_generated or False
                )
                
                # Set finalized timestamp if status is final
                if report_data.status == ReportStatus.FINAL:
                    report.finalized_at = datetime.utcnow()
                
                db.add(report)
                action = "CREATE"
                old_data = {}
            
            # Commit changes
            db.commit()
            db.refresh(report)
            
            # Log audit event
            changes = {
                "action": action,
                "old_data": old_data,
                "new_data": {
                    "findings": report_data.findings,
                    "measurements": report_data.measurements,
                    "impressions": report_data.impressions,
                    "status": report_data.status
                }
            }
            
            await self.audit_service.log_report_action(
                db=db,
                report_id=str(report.report_id),
                action=action,
                study_uid=report_data.study_uid,
                user_id=user_id or "system",
                changes=changes
            )
            
            logger.info(f"Report {action.lower()}d successfully: {report.report_id}")
            
            # Convert to response format
            return self._convert_to_response(report)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating/updating report: {str(e)}")
            raise
    
    async def get_report(
        self, 
        db: Session, 
        report_id: str,
        user_id: Optional[str] = None
    ) -> Optional[ReportResponse]:
        """
        Retrieve report by ID.
        """
        try:
            report = db.query(Report).filter(
                Report.report_id == report_id
            ).first()
            
            if not report:
                return None
            
            # Log access event
            await self.audit_service.log_report_action(
                db=db,
                report_id=report_id,
                action="READ",
                study_uid=report.study_uid,
                user_id=user_id or "system"
            )
            
            return self._convert_to_response(report)
            
        except Exception as e:
            logger.error(f"Error retrieving report {report_id}: {str(e)}")
            raise
    
    async def get_reports_by_study(
        self, 
        db: Session, 
        study_uid: str,
        user_id: Optional[str] = None
    ) -> List[ReportResponse]:
        """
        Get all reports for a study.
        """
        try:
            reports = db.query(Report).filter(
                Report.study_uid == study_uid
            ).order_by(Report.created_at.desc()).all()
            
            # Log access event
            await self.audit_service.log_study_access(
                db=db,
                study_uid=study_uid,
                user_id=user_id,
                access_type="REPORT_VIEW"
            )
            
            return [self._convert_to_response(report) for report in reports]
            
        except Exception as e:
            logger.error(f"Error retrieving reports for study {study_uid}: {str(e)}")
            raise
    
    async def finalize_report(
        self, 
        db: Session, 
        report_id: str,
        user_id: Optional[str] = None
    ) -> Optional[ReportResponse]:
        """
        Finalize a report (change status to FINAL).
        """
        try:
            report = db.query(Report).filter(
                Report.report_id == report_id
            ).first()
            
            if not report:
                return None
            
            if report.status == ReportStatus.FINAL:
                logger.warning(f"Report {report_id} is already finalized")
                return self._convert_to_response(report)
            
            # Update status and finalization timestamp
            old_status = report.status
            report.status = ReportStatus.FINAL
            report.finalized_at = datetime.utcnow()
            report.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(report)
            
            # Log finalization
            await self.audit_service.log_report_action(
                db=db,
                report_id=report_id,
                action="FINALIZED",
                study_uid=report.study_uid,
                user_id=user_id or "system",
                changes={
                    "old_status": old_status,
                    "new_status": ReportStatus.FINAL,
                    "finalized_at": report.finalized_at.isoformat()
                }
            )
            
            logger.info(f"Report {report_id} finalized successfully")
            return self._convert_to_response(report)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error finalizing report {report_id}: {str(e)}")
            raise
    
    async def list_reports(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        exam_type: Optional[str] = None,
        radiologist_id: Optional[str] = None,
        ai_generated: Optional[bool] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List reports with optional filtering.
        """
        try:
            query = db.query(Report)
            
            # Apply filters
            if status:
                query = query.filter(Report.status == status)
            if exam_type:
                query = query.filter(Report.exam_type == exam_type)
            if radiologist_id:
                query = query.filter(Report.radiologist_id == radiologist_id)
            if ai_generated is not None:
                query = query.filter(Report.ai_generated == ai_generated)
            
            # Order by creation date (newest first)
            query = query.order_by(Report.created_at.desc())
            
            # Apply pagination
            reports = query.offset(skip).limit(limit).all()
            
            # Convert to response format
            result = []
            for report in reports:
                report_dict = {
                    "report_id": str(report.report_id),
                    "study_uid": report.study_uid,
                    "exam_type": report.exam_type,
                    "status": report.status,
                    "radiologist_id": report.radiologist_id,
                    "ai_generated": report.ai_generated,
                    "ai_confidence": report.ai_confidence,
                    "created_at": report.created_at.isoformat(),
                    "finalized_at": report.finalized_at.isoformat() if report.finalized_at else None,
                    "has_findings": bool(report.findings),
                    "has_measurements": bool(report.measurements),
                    "diagnosis_code_count": len(report.diagnosis_codes or []),
                    "cpt_code_count": len(report.cpt_codes or [])
                }
                result.append(report_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing reports: {str(e)}")
            raise
    
    async def get_report_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Get report statistics for dashboard.
        """
        try:
            total_reports = db.query(Report).count()
            
            # Count by status
            status_counts = {}
            for status in ReportStatus:
                count = db.query(Report).filter(Report.status == status.value).count()
                status_counts[status.value] = count
            
            # Count AI vs manual reports
            ai_reports = db.query(Report).filter(Report.ai_generated == True).count()
            manual_reports = db.query(Report).filter(Report.ai_generated == False).count()
            
            # Average AI confidence
            ai_reports_with_confidence = db.query(Report).filter(
                Report.ai_generated == True,
                Report.ai_confidence.isnot(None)
            ).all()
            
            avg_ai_confidence = 0.0
            if ai_reports_with_confidence:
                total_confidence = sum(r.ai_confidence for r in ai_reports_with_confidence)
                avg_ai_confidence = total_confidence / len(ai_reports_with_confidence)
            
            # Recent reports (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_reports = db.query(Report).filter(
                Report.created_at >= yesterday
            ).count()
            
            # Finalization rate
            finalized_reports = db.query(Report).filter(
                Report.status == ReportStatus.FINAL
            ).count()
            finalization_rate = (finalized_reports / total_reports * 100) if total_reports > 0 else 0
            
            return {
                "total_reports": total_reports,
                "status_counts": status_counts,
                "ai_reports": ai_reports,
                "manual_reports": manual_reports,
                "ai_percentage": (ai_reports / total_reports * 100) if total_reports > 0 else 0,
                "average_ai_confidence": avg_ai_confidence,
                "recent_reports": recent_reports,
                "finalization_rate": finalization_rate,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting report statistics: {str(e)}")
            raise
    
    async def search_reports(
        self,
        db: Session,
        search_term: str,
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search reports by findings, impressions, or study UID.
        """
        try:
            search_pattern = f"%{search_term}%"
            
            reports = db.query(Report).filter(
                or_(
                    Report.study_uid.ilike(search_pattern),
                    Report.findings.ilike(search_pattern),
                    Report.impressions.ilike(search_pattern),
                    Report.recommendations.ilike(search_pattern)
                )
            ).order_by(Report.created_at.desc()).limit(limit).all()
            
            result = []
            for report in reports:
                report_dict = {
                    "report_id": str(report.report_id),
                    "study_uid": report.study_uid,
                    "exam_type": report.exam_type,
                    "status": report.status,
                    "findings_preview": (report.findings or "")[:200] + "..." if len(report.findings or "") > 200 else report.findings,
                    "impressions_preview": (report.impressions or "")[:200] + "..." if len(report.impressions or "") > 200 else report.impressions,
                    "created_at": report.created_at.isoformat(),
                    "ai_generated": report.ai_generated
                }
                result.append(report_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching reports: {str(e)}")
            raise
    
    def _convert_to_response(self, report: Report) -> ReportResponse:
        """Convert Report model to ReportResponse schema."""
        return ReportResponse(
            id=report.id,
            report_id=report.report_id,
            study_uid=report.study_uid,
            radiologist_id=report.radiologist_id,
            exam_type=report.exam_type,
            findings=report.findings,
            measurements=report.measurements,
            impressions=report.impressions,
            recommendations=report.recommendations,
            diagnosis_codes=report.diagnosis_codes,
            cpt_codes=report.cpt_codes,
            status=report.status,
            ai_confidence=report.ai_confidence,
            ai_generated=report.ai_generated,
            created_at=report.created_at,
            updated_at=report.updated_at,
            finalized_at=report.finalized_at
        )