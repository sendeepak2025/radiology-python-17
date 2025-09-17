"""
Audit service for HIPAA compliance and system tracking.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from models import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    """Service for managing audit logs and HIPAA compliance."""
    
    async def log_event(
        self,
        db: Session,
        event_type: str,
        event_description: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        study_uid: Optional[str] = None,
        report_id: Optional[str] = None,
        superbill_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log an audit event for HIPAA compliance.
        """
        try:
            audit_log = AuditLog(
                event_type=event_type,
                event_description=event_description,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id or "system",
                user_role=user_role or "system",
                ip_address=ip_address,
                user_agent=user_agent,
                study_uid=study_uid,
                report_id=uuid.UUID(report_id) if report_id else None,
                superbill_id=uuid.UUID(superbill_id) if superbill_id else None,
                metadata=metadata or {}
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(f"Audit event logged: {event_type} - {event_description}")
            return audit_log
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging audit event: {str(e)}")
            raise
    
    async def log_study_access(
        self,
        db: Session,
        study_uid: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        access_type: str = "VIEW"
    ) -> AuditLog:
        """
        Log study access for HIPAA compliance.
        """
        return await self.log_event(
            db=db,
            event_type=f"STUDY_{access_type}",
            event_description=f"Study {access_type.lower()} accessed",
            resource_type="Study",
            resource_id=study_uid,
            study_uid=study_uid,
            user_id=user_id,
            ip_address=ip_address,
            metadata={
                "access_type": access_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def log_report_action(
        self,
        db: Session,
        report_id: str,
        action: str,
        study_uid: Optional[str] = None,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log report-related actions.
        """
        return await self.log_event(
            db=db,
            event_type=f"REPORT_{action}",
            event_description=f"Report {action.lower()}",
            resource_type="Report",
            resource_id=report_id,
            report_id=report_id,
            study_uid=study_uid,
            user_id=user_id,
            metadata={
                "action": action,
                "changes": changes or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def log_billing_action(
        self,
        db: Session,
        superbill_id: str,
        action: str,
        report_id: Optional[str] = None,
        user_id: Optional[str] = None,
        billing_data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log billing-related actions.
        """
        return await self.log_event(
            db=db,
            event_type=f"BILLING_{action}",
            event_description=f"Billing {action.lower()}",
            resource_type="Superbill",
            resource_id=superbill_id,
            superbill_id=superbill_id,
            report_id=report_id,
            user_id=user_id,
            metadata={
                "action": action,
                "billing_data": billing_data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def log_ai_processing(
        self,
        db: Session,
        study_uid: str,
        job_id: str,
        status: str,
        processing_time: Optional[float] = None,
        confidence: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log AI processing events.
        """
        return await self.log_event(
            db=db,
            event_type=f"AI_{status}",
            event_description=f"AI processing {status.lower()}",
            resource_type="AIJob",
            resource_id=job_id,
            study_uid=study_uid,
            user_id="ai_system",
            user_role="ai_worker",
            metadata={
                "job_id": job_id,
                "status": status,
                "processing_time": processing_time,
                "confidence": confidence,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def get_audit_trail(
        self,
        db: Session,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        study_uid: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit trail with filtering options.
        """
        try:
            query = db.query(AuditLog)
            
            # Apply filters
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            if resource_id:
                query = query.filter(AuditLog.resource_id == resource_id)
            if study_uid:
                query = query.filter(AuditLog.study_uid == study_uid)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            # Order by timestamp (newest first)
            query = query.order_by(AuditLog.timestamp.desc())
            
            # Apply limit
            audit_logs = query.limit(limit).all()
            
            # Convert to response format
            result = []
            for log in audit_logs:
                log_dict = {
                    "id": str(log.id),
                    "event_type": log.event_type,
                    "event_description": log.event_description,
                    "user_id": log.user_id,
                    "user_role": log.user_role,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "study_uid": log.study_uid,
                    "report_id": str(log.report_id) if log.report_id else None,
                    "superbill_id": str(log.superbill_id) if log.superbill_id else None,
                    "ip_address": log.ip_address,
                    "timestamp": log.timestamp.isoformat(),
                    "metadata": log.metadata
                }
                result.append(log_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {str(e)}")
            raise
    
    async def get_user_activity_summary(
        self,
        db: Session,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get user activity summary for compliance reporting.
        """
        try:
            query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            logs = query.all()
            
            # Count by event type
            event_counts = {}
            resource_counts = {}
            study_accesses = set()
            
            for log in logs:
                # Count event types
                event_counts[log.event_type] = event_counts.get(log.event_type, 0) + 1
                
                # Count resource types
                if log.resource_type:
                    resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1
                
                # Track unique study accesses
                if log.study_uid and log.event_type.startswith("STUDY_"):
                    study_accesses.add(log.study_uid)
            
            return {
                "user_id": user_id,
                "total_events": len(logs),
                "event_type_counts": event_counts,
                "resource_type_counts": resource_counts,
                "unique_studies_accessed": len(study_accesses),
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating user activity summary: {str(e)}")
            raise