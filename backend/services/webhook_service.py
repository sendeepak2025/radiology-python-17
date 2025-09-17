"""
Webhook service for external system integration and notifications.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import httpx
import json
import hashlib
import hmac

from models import Study, Report, Superbill
from services.audit_service import AuditService
from config import settings

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for sending webhook notifications to external systems."""
    
    def __init__(self):
        self.audit_service = AuditService()
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 5.0
    
    async def send_study_notification(
        self,
        db: Session,
        study: Study,
        event_type: str,
        webhook_url: str,
        secret_key: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send study-related webhook notification.
        """
        try:
            payload = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "study_uid": study.study_uid,
                    "patient_id": study.patient_id,
                    "study_date": study.study_date.isoformat() if study.study_date else None,
                    "modality": study.modality,
                    "exam_type": study.exam_type,
                    "study_description": study.study_description,
                    "status": study.status,
                    "created_at": study.created_at.isoformat(),
                    "updated_at": study.updated_at.isoformat() if study.updated_at else None
                },
                "source": {
                    "system": "kiro-mini",
                    "version": "1.0.0",
                    "environment": settings.log_level.lower()
                }
            }
            
            result = await self._send_webhook(
                webhook_url=webhook_url,
                payload=payload,
                secret_key=secret_key,
                event_type=event_type
            )
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="WEBHOOK_SENT",
                event_description=f"Webhook sent for study {event_type}",
                resource_type="Study",
                resource_id=study.study_uid,
                study_uid=study.study_uid,
                user_id=user_id or "system",
                metadata={
                    "webhook_url": webhook_url,
                    "event_type": event_type,
                    "success": result["success"],
                    "status_code": result.get("status_code"),
                    "response_time_ms": result.get("response_time_ms")
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending study webhook: {str(e)}")
            raise
    
    async def send_report_notification(
        self,
        db: Session,
        report: Report,
        event_type: str,
        webhook_url: str,
        secret_key: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send report-related webhook notification.
        """
        try:
            payload = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "report_id": str(report.report_id),
                    "study_uid": report.study_uid,
                    "radiologist_id": report.radiologist_id,
                    "exam_type": report.exam_type,
                    "status": report.status,
                    "ai_generated": report.ai_generated,
                    "ai_confidence": report.ai_confidence,
                    "diagnosis_codes": report.diagnosis_codes,
                    "cpt_codes": report.cpt_codes,
                    "created_at": report.created_at.isoformat(),
                    "updated_at": report.updated_at.isoformat() if report.updated_at else None,
                    "finalized_at": report.finalized_at.isoformat() if report.finalized_at else None
                },
                "source": {
                    "system": "kiro-mini",
                    "version": "1.0.0",
                    "environment": settings.log_level.lower()
                }
            }
            
            # Include report content for finalized reports
            if event_type == "report.finalized" and report.status == "final":
                payload["data"]["content"] = {
                    "findings": report.findings,
                    "impressions": report.impressions,
                    "recommendations": report.recommendations,
                    "measurements": report.measurements
                }
            
            result = await self._send_webhook(
                webhook_url=webhook_url,
                payload=payload,
                secret_key=secret_key,
                event_type=event_type
            )
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="WEBHOOK_SENT",
                event_description=f"Webhook sent for report {event_type}",
                resource_type="Report",
                resource_id=str(report.report_id),
                report_id=str(report.report_id),
                study_uid=report.study_uid,
                user_id=user_id or "system",
                metadata={
                    "webhook_url": webhook_url,
                    "event_type": event_type,
                    "success": result["success"],
                    "status_code": result.get("status_code"),
                    "response_time_ms": result.get("response_time_ms")
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending report webhook: {str(e)}")
            raise
    
    async def send_billing_notification(
        self,
        db: Session,
        superbill: Superbill,
        event_type: str,
        webhook_url: str,
        secret_key: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send billing-related webhook notification.
        """
        try:
            payload = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "superbill_id": str(superbill.superbill_id),
                    "report_id": str(superbill.report_id),
                    "patient_info": superbill.patient_info,
                    "services": superbill.services,
                    "diagnoses": superbill.diagnoses,
                    "total_charges": float(superbill.total_charges),
                    "provider_npi": superbill.provider_npi,
                    "facility_name": superbill.facility_name,
                    "validated": superbill.validated,
                    "submitted": superbill.submitted,
                    "created_at": superbill.created_at.isoformat(),
                    "submission_date": superbill.submission_date.isoformat() if superbill.submission_date else None
                },
                "source": {
                    "system": "kiro-mini",
                    "version": "1.0.0",
                    "environment": settings.log_level.lower()
                }
            }
            
            # Include 837P data for submission events
            if event_type == "billing.submitted" and superbill.x12_837p_data:
                payload["data"]["x12_837p_ready"] = True
            
            result = await self._send_webhook(
                webhook_url=webhook_url,
                payload=payload,
                secret_key=secret_key,
                event_type=event_type
            )
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="WEBHOOK_SENT",
                event_description=f"Webhook sent for billing {event_type}",
                resource_type="Superbill",
                resource_id=str(superbill.superbill_id),
                superbill_id=str(superbill.superbill_id),
                report_id=str(superbill.report_id),
                user_id=user_id or "system",
                metadata={
                    "webhook_url": webhook_url,
                    "event_type": event_type,
                    "success": result["success"],
                    "status_code": result.get("status_code"),
                    "response_time_ms": result.get("response_time_ms"),
                    "total_charges": float(superbill.total_charges)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending billing webhook: {str(e)}")
            raise
    
    async def _send_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        secret_key: Optional[str] = None,
        event_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Send webhook with retry logic and signature verification.
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Kiro-Mini-Webhook/1.0",
            "X-Kiro-Event": event_type,
            "X-Kiro-Timestamp": str(int(datetime.utcnow().timestamp()))
        }
        
        # Add signature if secret key provided
        if secret_key:
            signature = self._generate_signature(payload, secret_key)
            headers["X-Kiro-Signature"] = signature
        
        for attempt in range(self.max_retries):
            try:
                start_time = datetime.utcnow()
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers=headers
                    )
                
                end_time = datetime.utcnow()
                response_time_ms = (end_time - start_time).total_seconds() * 1000
                
                result = {
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "attempt": attempt + 1,
                    "response_headers": dict(response.headers),
                    "webhook_url": webhook_url
                }
                
                if response.status_code < 400:
                    logger.info(f"Webhook sent successfully to {webhook_url} (attempt {attempt + 1})")
                    try:
                        result["response_body"] = response.json()
                    except:
                        result["response_body"] = response.text
                    return result
                else:
                    logger.warning(f"Webhook failed with status {response.status_code} (attempt {attempt + 1})")
                    result["error"] = f"HTTP {response.status_code}: {response.text}"
                    
                    if attempt == self.max_retries - 1:
                        return result
                
            except httpx.TimeoutException:
                error_msg = f"Webhook timeout after {self.timeout}s (attempt {attempt + 1})"
                logger.warning(error_msg)
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": error_msg,
                        "attempt": attempt + 1,
                        "webhook_url": webhook_url
                    }
            
            except Exception as e:
                error_msg = f"Webhook error: {str(e)} (attempt {attempt + 1})"
                logger.error(error_msg)
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": error_msg,
                        "attempt": attempt + 1,
                        "webhook_url": webhook_url
                    }
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "attempt": self.max_retries,
            "webhook_url": webhook_url
        }
    
    def _generate_signature(self, payload: Dict[str, Any], secret_key: str) -> str:
        """
        Generate HMAC signature for webhook payload.
        """
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(self, payload: str, signature: str, secret_key: str) -> bool:
        """
        Verify webhook signature.
        """
        try:
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def send_batch_notifications(
        self,
        db: Session,
        notifications: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Send multiple webhook notifications concurrently.
        """
        try:
            tasks = []
            
            for notification in notifications:
                if notification["type"] == "study":
                    task = self.send_study_notification(
                        db=db,
                        study=notification["data"],
                        event_type=notification["event_type"],
                        webhook_url=notification["webhook_url"],
                        secret_key=notification.get("secret_key"),
                        user_id=user_id
                    )
                elif notification["type"] == "report":
                    task = self.send_report_notification(
                        db=db,
                        report=notification["data"],
                        event_type=notification["event_type"],
                        webhook_url=notification["webhook_url"],
                        secret_key=notification.get("secret_key"),
                        user_id=user_id
                    )
                elif notification["type"] == "billing":
                    task = self.send_billing_notification(
                        db=db,
                        superbill=notification["data"],
                        event_type=notification["event_type"],
                        webhook_url=notification["webhook_url"],
                        secret_key=notification.get("secret_key"),
                        user_id=user_id
                    )
                else:
                    continue
                
                tasks.append(task)
            
            # Execute all webhooks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "success": False,
                        "error": str(result),
                        "notification_index": i
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error sending batch notifications: {str(e)}")
            raise
    
    async def test_webhook_endpoint(
        self,
        webhook_url: str,
        secret_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test webhook endpoint connectivity and response.
        """
        try:
            test_payload = {
                "event_type": "test.ping",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "message": "Test webhook from Kiro-mini",
                    "test_id": str(datetime.utcnow().timestamp())
                },
                "source": {
                    "system": "kiro-mini",
                    "version": "1.0.0",
                    "test": True
                }
            }
            
            result = await self._send_webhook(
                webhook_url=webhook_url,
                payload=test_payload,
                secret_key=secret_key,
                event_type="test.ping"
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "webhook_url": webhook_url
            }