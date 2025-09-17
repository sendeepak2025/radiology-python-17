"""
Report version history service for tracking changes and maintaining audit trails.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from models import Report, ReportVersion
from services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ReportVersionService:
    """Service for managing report version history and change tracking."""
    
    def __init__(self):
        self.audit_service = AuditService()
    
    async def create_version(
        self,
        db: Session,
        report: Report,
        user_id: str,
        change_summary: Optional[str] = None,
        previous_data: Optional[Dict[str, Any]] = None
    ) -> ReportVersion:
        """
        Create a new version of a report.
        """
        try:
            # Get the current version number
            version_number = await self.get_next_version_number(db, report.report_id)
            
            # Calculate changes if previous data is provided
            change_details = None
            if previous_data:
                change_details = self.calculate_changes(previous_data, report)
            
            # Create version record
            version = ReportVersion(
                report_id=report.report_id,
                version_number=version_number,
                findings=report.findings,
                measurements=report.measurements,
                impressions=report.impressions,
                recommendations=report.recommendations,
                diagnosis_codes=report.diagnosis_codes,
                cpt_codes=report.cpt_codes,
                status=report.status,
                ai_confidence={"score": report.ai_confidence} if report.ai_confidence else None,
                created_by=user_id,
                change_summary=change_summary or f"Version {version_number} created",
                change_details=change_details
            )
            
            db.add(version)
            db.commit()
            db.refresh(version)
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="REPORT_VERSION_CREATED",
                event_description=f"Report version {version_number} created",
                resource_type="ReportVersion",
                resource_id=str(version.version_id),
                report_id=str(report.report_id),
                study_uid=report.study_uid,
                user_id=user_id,
                metadata={
                    "version_number": version_number,
                    "change_summary": change_summary,
                    "has_changes": change_details is not None,
                    "change_count": len(change_details) if change_details else 0
                }
            )
            
            logger.info(f"Created version {version_number} for report {report.report_id}")
            return version
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating report version: {str(e)}")
            raise
    
    async def get_next_version_number(self, db: Session, report_id: uuid.UUID) -> str:
        """Get the next version number for a report."""
        try:
            # Get the latest version number
            latest_version = db.query(ReportVersion).filter(
                ReportVersion.report_id == report_id
            ).order_by(ReportVersion.created_at.desc()).first()
            
            if not latest_version:
                return "1.0"
            
            # Parse version number and increment
            try:
                major, minor = latest_version.version_number.split(".")
                return f"{major}.{int(minor) + 1}"
            except ValueError:
                # If version format is unexpected, start fresh
                return "1.0"
                
        except Exception as e:
            logger.error(f"Error getting next version number: {str(e)}")
            return "1.0"
    
    def calculate_changes(self, previous_data: Dict[str, Any], current_report: Report) -> Dict[str, Any]:
        """Calculate detailed changes between versions."""
        changes = {}
        
        # Fields to track
        fields_to_track = [
            "findings", "measurements", "impressions", 
            "recommendations", "diagnosis_codes", "cpt_codes", "status"
        ]
        
        for field in fields_to_track:
            old_value = previous_data.get(field)
            new_value = getattr(current_report, field)
            
            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value,
                    "changed_at": datetime.utcnow().isoformat()
                }
        
        return changes
    
    async def get_version_history(
        self,
        db: Session,
        report_id: uuid.UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get version history for a report."""
        try:
            versions = db.query(ReportVersion).filter(
                ReportVersion.report_id == report_id
            ).order_by(ReportVersion.created_at.desc()).limit(limit).all()
            
            result = []
            for version in versions:
                version_dict = {
                    "version_id": str(version.version_id),
                    "version_number": version.version_number,
                    "created_by": version.created_by,
                    "created_at": version.created_at.isoformat(),
                    "change_summary": version.change_summary,
                    "change_details": version.change_details,
                    "status": version.status,
                    "has_changes": bool(version.change_details)
                }
                result.append(version_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            raise
    
    async def get_version(
        self,
        db: Session,
        version_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Get a specific version of a report."""
        try:
            version = db.query(ReportVersion).filter(
                ReportVersion.version_id == version_id
            ).first()
            
            if not version:
                return None
            
            return {
                "version_id": str(version.version_id),
                "report_id": str(version.report_id),
                "version_number": version.version_number,
                "findings": version.findings,
                "measurements": version.measurements,
                "impressions": version.impressions,
                "recommendations": version.recommendations,
                "diagnosis_codes": version.diagnosis_codes,
                "cpt_codes": version.cpt_codes,
                "status": version.status,
                "ai_confidence": version.ai_confidence,
                "created_by": version.created_by,
                "created_at": version.created_at.isoformat(),
                "change_summary": version.change_summary,
                "change_details": version.change_details
            }
            
        except Exception as e:
            logger.error(f"Error getting version: {str(e)}")
            raise
    
    async def compare_versions(
        self,
        db: Session,
        version1_id: uuid.UUID,
        version2_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Compare two versions of a report."""
        try:
            version1 = await self.get_version(db, version1_id)
            version2 = await self.get_version(db, version2_id)
            
            if not version1 or not version2:
                raise ValueError("One or both versions not found")
            
            # Calculate differences
            differences = {}
            fields_to_compare = [
                "findings", "measurements", "impressions", 
                "recommendations", "diagnosis_codes", "cpt_codes", "status"
            ]
            
            for field in fields_to_compare:
                val1 = version1.get(field)
                val2 = version2.get(field)
                
                if val1 != val2:
                    differences[field] = {
                        f"version_{version1['version_number']}": val1,
                        f"version_{version2['version_number']}": val2
                    }
            
            return {
                "version1": {
                    "version_id": str(version1_id),
                    "version_number": version1["version_number"],
                    "created_at": version1["created_at"]
                },
                "version2": {
                    "version_id": str(version2_id),
                    "version_number": version2["version_number"],
                    "created_at": version2["created_at"]
                },
                "differences": differences,
                "total_differences": len(differences)
            }
            
        except Exception as e:
            logger.error(f"Error comparing versions: {str(e)}")
            raise
    
    async def restore_version(
        self,
        db: Session,
        report_id: uuid.UUID,
        version_id: uuid.UUID,
        user_id: str
    ) -> Report:
        """Restore a report to a previous version."""
        try:
            # Get the version to restore
            version_data = await self.get_version(db, version_id)
            if not version_data:
                raise ValueError("Version not found")
            
            # Get the current report
            current_report = db.query(Report).filter(
                Report.report_id == report_id
            ).first()
            
            if not current_report:
                raise ValueError("Report not found")
            
            # Store current state before restoration
            previous_data = {
                "findings": current_report.findings,
                "measurements": current_report.measurements,
                "impressions": current_report.impressions,
                "recommendations": current_report.recommendations,
                "diagnosis_codes": current_report.diagnosis_codes,
                "cpt_codes": current_report.cpt_codes,
                "status": current_report.status
            }
            
            # Restore the report to the previous version
            current_report.findings = version_data["findings"]
            current_report.measurements = version_data["measurements"]
            current_report.impressions = version_data["impressions"]
            current_report.recommendations = version_data["recommendations"]
            current_report.diagnosis_codes = version_data["diagnosis_codes"]
            current_report.cpt_codes = version_data["cpt_codes"]
            current_report.status = version_data["status"]
            current_report.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(current_report)
            
            # Create a new version for the restoration
            await self.create_version(
                db=db,
                report=current_report,
                user_id=user_id,
                change_summary=f"Restored to version {version_data['version_number']}",
                previous_data=previous_data
            )
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="REPORT_VERSION_RESTORED",
                event_description=f"Report restored to version {version_data['version_number']}",
                resource_type="Report",
                resource_id=str(report_id),
                report_id=str(report_id),
                study_uid=current_report.study_uid,
                user_id=user_id,
                metadata={
                    "restored_version_id": str(version_id),
                    "restored_version_number": version_data["version_number"]
                }
            )
            
            logger.info(f"Restored report {report_id} to version {version_data['version_number']}")
            return current_report
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error restoring version: {str(e)}")
            raise