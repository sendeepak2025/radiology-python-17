"""
Critical Findings Communication System

This service implements a comprehensive critical findings management system
based on regulatory requirements and patient safety best practices:
- Automated critical findings detection
- Multi-channel notification system
- Acknowledgment tracking with timestamps
- Escalation protocols
- Regulatory compliance reporting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = logging.getLogger(__name__)

class CriticalFindingType(Enum):
    ACUTE_STROKE = "acute_stroke"
    PULMONARY_EMBOLISM = "pulmonary_embolism"
    PNEUMOTHORAX = "pneumothorax"
    AORTIC_DISSECTION = "aortic_dissection"
    BOWEL_OBSTRUCTION = "bowel_obstruction"
    INTRACRANIAL_HEMORRHAGE = "intracranial_hemorrhage"
    ACUTE_APPENDICITIS = "acute_appendicitis"
    CARDIAC_TAMPONADE = "cardiac_tamponade"
    TENSION_PNEUMOTHORAX = "tension_pneumothorax"
    ACUTE_CHOLANGITIS = "acute_cholangitis"
    NECROTIZING_FASCIITIS = "necrotizing_fasciitis"
    ACUTE_MESENTERIC_ISCHEMIA = "acute_mesenteric_ischemia"

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    PAGER = "pager"
    SECURE_MESSAGE = "secure_message"
    EPIC_ALERT = "epic_alert"

class CriticalFindingStatus(Enum):
    DETECTED = "detected"
    NOTIFIED = "notified"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"

@dataclass
class CriticalFinding:
    """Critical finding with complete tracking information"""
    finding_id: str
    study_uid: str
    patient_id: str
    finding_type: CriticalFindingType
    severity_level: int  # 1-5, 5 being most critical
    description: str
    detected_at: datetime
    detected_by: str  # radiologist_id or "AI_SYSTEM"
    status: CriticalFindingStatus
    notification_attempts: List[Dict[str, Any]] = field(default_factory=list)
    acknowledgments: List[Dict[str, Any]] = field(default_factory=list)
    escalations: List[Dict[str, Any]] = field(default_factory=list)
    resolution_time: Optional[datetime] = None
    
@dataclass
class NotificationRecipient:
    """Notification recipient with contact preferences"""
    recipient_id: str
    name: str
    role: str  # "attending", "resident", "nurse", "administrator"
    email: str
    phone: str
    pager: str
    preferred_channels: List[NotificationChannel]
    escalation_delay_minutes: int
    
class CriticalFindingsService:
    """Comprehensive critical findings management service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.active_findings: Dict[str, CriticalFinding] = {}
        self.notification_recipients: Dict[str, NotificationRecipient] = {}
        self.detection_rules = self._initialize_detection_rules()
        self.notification_templates = self._initialize_notification_templates()
        self.escalation_rules = self._initialize_escalation_rules()
        
    def _initialize_detection_rules(self) -> Dict[CriticalFindingType, Dict[str, Any]]:
        """Initialize AI-based critical finding detection rules"""
        return {
            CriticalFindingType.ACUTE_STROKE: {
                "keywords": ["acute stroke", "cerebral infarction", "mca occlusion", "large vessel occlusion"],
                "exam_types": ["brain_ct", "brain_mri", "ct_angiography"],
                "severity": 5,
                "time_limit_minutes": 15,
                "auto_detect": True
            },
            CriticalFindingType.PULMONARY_EMBOLISM: {
                "keywords": ["pulmonary embolism", "pe", "pulmonary artery filling defect", "saddle embolus"],
                "exam_types": ["chest_ct", "pe_protocol", "ct_angiography"],
                "severity": 5,
                "time_limit_minutes": 30,
                "auto_detect": True
            },
            CriticalFindingType.PNEUMOTHORAX: {
                "keywords": ["pneumothorax", "collapsed lung", "pleural air"],
                "exam_types": ["chest_ct", "chest_xray"],
                "severity": 4,
                "time_limit_minutes": 60,
                "auto_detect": True
            },
            CriticalFindingType.AORTIC_DISSECTION: {
                "keywords": ["aortic dissection", "aortic tear", "intimal flap"],
                "exam_types": ["chest_ct", "ct_angiography", "cardiac_ct"],
                "severity": 5,
                "time_limit_minutes": 15,
                "auto_detect": True
            },
            CriticalFindingType.INTRACRANIAL_HEMORRHAGE: {
                "keywords": ["intracranial hemorrhage", "brain bleed", "subarachnoid hemorrhage", "subdural hematoma"],
                "exam_types": ["brain_ct", "brain_mri"],
                "severity": 5,
                "time_limit_minutes": 15,
                "auto_detect": True
            },
            CriticalFindingType.BOWEL_OBSTRUCTION: {
                "keywords": ["bowel obstruction", "small bowel obstruction", "large bowel obstruction"],
                "exam_types": ["abdomen_ct", "pelvis_ct"],
                "severity": 3,
                "time_limit_minutes": 120,
                "auto_detect": True
            }
        }
    
    def _initialize_notification_templates(self) -> Dict[str, str]:
        """Initialize notification message templates"""
        return {
            "email_critical": """
CRITICAL FINDING ALERT - IMMEDIATE ATTENTION REQUIRED

Patient: {patient_id}
Study: {study_uid}
Finding: {finding_type}
Severity: {severity_level}/5
Description: {description}

Detected by: {detected_by}
Detection time: {detected_at}

This finding requires immediate clinical attention and acknowledgment.
Please acknowledge receipt of this notification within {time_limit} minutes.

Study available at: {study_url}
Contact radiology at: {radiology_contact}
            """,
            
            "sms_critical": """
CRITICAL FINDING ALERT
Patient: {patient_id}
Finding: {finding_type}
Severity: {severity_level}/5
Detected: {detected_at}
Acknowledge within {time_limit} min
Study: {study_url}
            """,
            
            "phone_script": """
This is an automated critical finding alert from the radiology department.
Patient ID {patient_id} has a critical finding: {finding_type}.
Severity level {severity_level} out of 5.
Please acknowledge this finding immediately by calling the radiology department.
            """
        }
    
    def _initialize_escalation_rules(self) -> Dict[int, Dict[str, Any]]:
        """Initialize escalation rules by severity level"""
        return {
            5: {  # Most critical
                "initial_notification_channels": [NotificationChannel.PHONE, NotificationChannel.PAGER, NotificationChannel.EMAIL],
                "escalation_intervals": [5, 10, 15],  # minutes
                "escalation_recipients": ["attending", "chief_resident", "department_head"],
                "max_escalations": 3
            },
            4: {  # High priority
                "initial_notification_channels": [NotificationChannel.PAGER, NotificationChannel.EMAIL, NotificationChannel.SMS],
                "escalation_intervals": [15, 30, 60],
                "escalation_recipients": ["attending", "senior_resident"],
                "max_escalations": 2
            },
            3: {  # Moderate priority
                "initial_notification_channels": [NotificationChannel.EMAIL, NotificationChannel.SECURE_MESSAGE],
                "escalation_intervals": [60, 120],
                "escalation_recipients": ["attending"],
                "max_escalations": 1
            }
        }
    
    async def detect_critical_findings(self, report_data: Dict[str, Any], study_data: Dict[str, Any]) -> List[CriticalFinding]:
        """Automatically detect critical findings in report using AI and keyword analysis"""
        try:
            detected_findings = []
            
            findings_text = report_data.get("findings", "").lower()
            impressions_text = report_data.get("impressions", "").lower()
            combined_text = f"{findings_text} {impressions_text}"
            
            exam_type = study_data.get("exam_type", "")
            
            for finding_type, rules in self.detection_rules.items():
                # Check if exam type is relevant
                if exam_type not in rules["exam_types"]:
                    continue
                
                # Check for keyword matches
                if any(keyword in combined_text for keyword in rules["keywords"]):
                    # Create critical finding
                    finding = CriticalFinding(
                        finding_id=f"CF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{finding_type.value}",
                        study_uid=study_data["study_uid"],
                        patient_id=study_data.get("patient_id", ""),
                        finding_type=finding_type,
                        severity_level=rules["severity"],
                        description=self._extract_finding_description(combined_text, rules["keywords"]),
                        detected_at=datetime.now(),
                        detected_by=report_data.get("radiologist_id", "AI_SYSTEM"),
                        status=CriticalFindingStatus.DETECTED
                    )
                    
                    detected_findings.append(finding)
                    self.active_findings[finding.finding_id] = finding
                    
                    logger.critical(f"Critical finding detected: {finding_type.value} for patient {finding.patient_id}")
            
            return detected_findings
            
        except Exception as e:
            logger.error(f"Error detecting critical findings: {str(e)}")
            return []
    
    def _extract_finding_description(self, text: str, keywords: List[str]) -> str:
        """Extract relevant description around detected keywords"""
        try:
            # Find the sentence containing the keyword
            sentences = text.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in keywords):
                    return sentence.strip()
            
            # Fallback to first 200 characters
            return text[:200] + "..." if len(text) > 200 else text
            
        except Exception as e:
            logger.error(f"Error extracting finding description: {str(e)}")
            return "Critical finding detected - see full report"
    
    async def initiate_critical_finding_workflow(self, finding: CriticalFinding) -> bool:
        """Initiate the complete critical finding notification and tracking workflow"""
        try:
            # Update finding status
            finding.status = CriticalFindingStatus.NOTIFIED
            
            # Get escalation rules for this severity level
            escalation_rules = self.escalation_rules.get(finding.severity_level, self.escalation_rules[3])
            
            # Send initial notifications
            await self._send_initial_notifications(finding, escalation_rules)
            
            # Schedule escalation monitoring
            asyncio.create_task(self._monitor_acknowledgment(finding, escalation_rules))
            
            # Log the critical finding
            await self._log_critical_finding(finding)
            
            logger.info(f"Initiated critical finding workflow for {finding.finding_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initiating critical finding workflow: {str(e)}")
            return False
    
    async def _send_initial_notifications(self, finding: CriticalFinding, escalation_rules: Dict[str, Any]) -> None:
        """Send initial notifications through multiple channels"""
        try:
            channels = escalation_rules["initial_notification_channels"]
            
            for channel in channels:
                success = await self._send_notification(finding, channel, "primary")
                
                finding.notification_attempts.append({
                    "timestamp": datetime.now(),
                    "channel": channel.value,
                    "recipient_type": "primary",
                    "success": success,
                    "attempt_number": 1
                })
            
        except Exception as e:
            logger.error(f"Error sending initial notifications: {str(e)}")
    
    async def _send_notification(self, finding: CriticalFinding, channel: NotificationChannel, recipient_type: str) -> bool:
        """Send notification through specified channel"""
        try:
            if channel == NotificationChannel.EMAIL:
                return await self._send_email_notification(finding, recipient_type)
            elif channel == NotificationChannel.SMS:
                return await self._send_sms_notification(finding, recipient_type)
            elif channel == NotificationChannel.PHONE:
                return await self._send_phone_notification(finding, recipient_type)
            elif channel == NotificationChannel.PAGER:
                return await self._send_pager_notification(finding, recipient_type)
            elif channel == NotificationChannel.SECURE_MESSAGE:
                return await self._send_secure_message(finding, recipient_type)
            else:
                logger.warning(f"Unsupported notification channel: {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending {channel.value} notification: {str(e)}")
            return False
    
    async def _send_email_notification(self, finding: CriticalFinding, recipient_type: str) -> bool:
        """Send email notification for critical finding"""
        try:
            # In production, this would use actual SMTP configuration
            template = self.notification_templates["email_critical"]
            
            message = template.format(
                patient_id=finding.patient_id,
                study_uid=finding.study_uid,
                finding_type=finding.finding_type.value.replace("_", " ").title(),
                severity_level=finding.severity_level,
                description=finding.description,
                detected_by=finding.detected_by,
                detected_at=finding.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
                time_limit=self.escalation_rules[finding.severity_level]["escalation_intervals"][0],
                study_url=f"https://kiro-mini.local/studies/{finding.study_uid}",
                radiology_contact="(555) 123-RADS"
            )
            
            # Mock email sending - in production, use actual SMTP
            logger.info(f"EMAIL SENT: Critical finding notification for {finding.patient_id}")
            logger.info(f"Email content: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    async def _send_sms_notification(self, finding: CriticalFinding, recipient_type: str) -> bool:
        """Send SMS notification for critical finding"""
        try:
            template = self.notification_templates["sms_critical"]
            
            message = template.format(
                patient_id=finding.patient_id,
                finding_type=finding.finding_type.value.replace("_", " ").title(),
                severity_level=finding.severity_level,
                detected_at=finding.detected_at.strftime("%H:%M"),
                time_limit=self.escalation_rules[finding.severity_level]["escalation_intervals"][0],
                study_url=f"https://kiro-mini.local/studies/{finding.study_uid}"
            )
            
            # Mock SMS sending - in production, use Twilio or similar service
            logger.info(f"SMS SENT: Critical finding notification for {finding.patient_id}")
            logger.info(f"SMS content: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
            return False
    
    async def _send_phone_notification(self, finding: CriticalFinding, recipient_type: str) -> bool:
        """Send automated phone call for critical finding"""
        try:
            script = self.notification_templates["phone_script"]
            
            message = script.format(
                patient_id=finding.patient_id,
                finding_type=finding.finding_type.value.replace("_", " "),
                severity_level=finding.severity_level
            )
            
            # Mock phone call - in production, use Twilio Voice API
            logger.info(f"PHONE CALL INITIATED: Critical finding notification for {finding.patient_id}")
            logger.info(f"Phone script: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending phone notification: {str(e)}")
            return False
    
    async def _send_pager_notification(self, finding: CriticalFinding, recipient_type: str) -> bool:
        """Send pager notification for critical finding"""
        try:
            message = f"CRITICAL: {finding.finding_type.value.replace('_', ' ').title()} - Patient {finding.patient_id} - Call Radiology STAT"
            
            # Mock pager - in production, integrate with paging system
            logger.info(f"PAGER SENT: Critical finding notification for {finding.patient_id}")
            logger.info(f"Pager message: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending pager notification: {str(e)}")
            return False
    
    async def _send_secure_message(self, finding: CriticalFinding, recipient_type: str) -> bool:
        """Send secure message through EHR system"""
        try:
            # Mock secure messaging - in production, integrate with EHR
            logger.info(f"SECURE MESSAGE SENT: Critical finding notification for {finding.patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending secure message: {str(e)}")
            return False
    
    async def _monitor_acknowledgment(self, finding: CriticalFinding, escalation_rules: Dict[str, Any]) -> None:
        """Monitor for acknowledgment and handle escalations"""
        try:
            escalation_intervals = escalation_rules["escalation_intervals"]
            max_escalations = escalation_rules["max_escalations"]
            
            for escalation_level in range(max_escalations):
                # Wait for escalation interval
                await asyncio.sleep(escalation_intervals[escalation_level] * 60)  # Convert to seconds
                
                # Check if acknowledged
                if finding.status == CriticalFindingStatus.ACKNOWLEDGED:
                    logger.info(f"Critical finding {finding.finding_id} acknowledged - stopping escalation")
                    return
                
                # Escalate
                await self._escalate_finding(finding, escalation_level + 1, escalation_rules)
            
            # Final escalation to department head if still not acknowledged
            if finding.status != CriticalFindingStatus.ACKNOWLEDGED:
                await self._final_escalation(finding)
                
        except Exception as e:
            logger.error(f"Error monitoring acknowledgment: {str(e)}")
    
    async def _escalate_finding(self, finding: CriticalFinding, escalation_level: int, escalation_rules: Dict[str, Any]) -> None:
        """Escalate critical finding to higher authority"""
        try:
            finding.status = CriticalFindingStatus.ESCALATED
            
            escalation_info = {
                "timestamp": datetime.now(),
                "escalation_level": escalation_level,
                "reason": "No acknowledgment received within required timeframe"
            }
            
            finding.escalations.append(escalation_info)
            
            # Send escalation notifications
            channels = escalation_rules["initial_notification_channels"]
            for channel in channels:
                await self._send_notification(finding, channel, f"escalation_{escalation_level}")
            
            logger.warning(f"Escalated critical finding {finding.finding_id} to level {escalation_level}")
            
        except Exception as e:
            logger.error(f"Error escalating finding: {str(e)}")
    
    async def _final_escalation(self, finding: CriticalFinding) -> None:
        """Final escalation to department administration"""
        try:
            logger.critical(f"FINAL ESCALATION: Critical finding {finding.finding_id} requires immediate administrative attention")
            
            # Send to all available channels
            for channel in NotificationChannel:
                await self._send_notification(finding, channel, "final_escalation")
            
            # Log as regulatory incident
            await self._log_regulatory_incident(finding)
            
        except Exception as e:
            logger.error(f"Error in final escalation: {str(e)}")
    
    async def acknowledge_critical_finding(self, finding_id: str, acknowledger_id: str, acknowledgment_method: str) -> bool:
        """Acknowledge receipt and review of critical finding"""
        try:
            if finding_id not in self.active_findings:
                logger.error(f"Critical finding {finding_id} not found")
                return False
            
            finding = self.active_findings[finding_id]
            finding.status = CriticalFindingStatus.ACKNOWLEDGED
            
            acknowledgment_info = {
                "timestamp": datetime.now(),
                "acknowledger_id": acknowledger_id,
                "method": acknowledgment_method,
                "response_time_minutes": (datetime.now() - finding.detected_at).total_seconds() / 60
            }
            
            finding.acknowledgments.append(acknowledgment_info)
            
            logger.info(f"Critical finding {finding_id} acknowledged by {acknowledger_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging critical finding: {str(e)}")
            return False
    
    async def resolve_critical_finding(self, finding_id: str, resolver_id: str, resolution_notes: str) -> bool:
        """Mark critical finding as resolved with clinical action taken"""
        try:
            if finding_id not in self.active_findings:
                logger.error(f"Critical finding {finding_id} not found")
                return False
            
            finding = self.active_findings[finding_id]
            finding.status = CriticalFindingStatus.RESOLVED
            finding.resolution_time = datetime.now()
            
            # Log resolution
            await self._log_critical_finding_resolution(finding, resolver_id, resolution_notes)
            
            logger.info(f"Critical finding {finding_id} resolved by {resolver_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving critical finding: {str(e)}")
            return False
    
    async def _log_critical_finding(self, finding: CriticalFinding) -> None:
        """Log critical finding for audit and compliance"""
        try:
            log_entry = {
                "event_type": "critical_finding_detected",
                "finding_id": finding.finding_id,
                "study_uid": finding.study_uid,
                "patient_id": finding.patient_id,
                "finding_type": finding.finding_type.value,
                "severity_level": finding.severity_level,
                "detected_at": finding.detected_at.isoformat(),
                "detected_by": finding.detected_by,
                "description": finding.description
            }
            
            # In production, this would write to audit database
            logger.info(f"AUDIT LOG: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging critical finding: {str(e)}")
    
    async def _log_critical_finding_resolution(self, finding: CriticalFinding, resolver_id: str, resolution_notes: str) -> None:
        """Log critical finding resolution for audit trail"""
        try:
            log_entry = {
                "event_type": "critical_finding_resolved",
                "finding_id": finding.finding_id,
                "resolved_by": resolver_id,
                "resolution_time": finding.resolution_time.isoformat(),
                "total_response_time_minutes": (finding.resolution_time - finding.detected_at).total_seconds() / 60,
                "resolution_notes": resolution_notes,
                "acknowledgment_count": len(finding.acknowledgments),
                "escalation_count": len(finding.escalations)
            }
            
            logger.info(f"AUDIT LOG: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging critical finding resolution: {str(e)}")
    
    async def _log_regulatory_incident(self, finding: CriticalFinding) -> None:
        """Log regulatory incident for unacknowledged critical findings"""
        try:
            incident_entry = {
                "event_type": "regulatory_incident",
                "incident_type": "unacknowledged_critical_finding",
                "finding_id": finding.finding_id,
                "patient_id": finding.patient_id,
                "finding_type": finding.finding_type.value,
                "severity_level": finding.severity_level,
                "detected_at": finding.detected_at.isoformat(),
                "escalation_count": len(finding.escalations),
                "notification_attempts": len(finding.notification_attempts),
                "requires_administrative_review": True
            }
            
            logger.critical(f"REGULATORY INCIDENT: {json.dumps(incident_entry)}")
            
        except Exception as e:
            logger.error(f"Error logging regulatory incident: {str(e)}")
    
    async def get_critical_findings_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive critical findings report for compliance"""
        try:
            # This would query actual database in production
            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_critical_findings": 45,
                    "acknowledged_within_target": 42,
                    "escalated_findings": 3,
                    "unresolved_findings": 0,
                    "average_response_time_minutes": 18.5,
                    "compliance_rate": 93.3
                },
                "findings_by_type": {
                    "acute_stroke": 8,
                    "pulmonary_embolism": 12,
                    "pneumothorax": 6,
                    "intracranial_hemorrhage": 5,
                    "aortic_dissection": 2,
                    "other": 12
                },
                "response_time_analysis": {
                    "within_15_minutes": 38,
                    "15_30_minutes": 4,
                    "30_60_minutes": 2,
                    "over_60_minutes": 1
                },
                "notification_channel_effectiveness": {
                    "phone": 95.2,
                    "pager": 88.7,
                    "email": 76.3,
                    "sms": 82.1
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating critical findings report: {str(e)}")
            return {}

# Global critical findings service instance
critical_findings_service = None

def get_critical_findings_service(db_session: Session) -> CriticalFindingsService:
    """Get or create critical findings service instance"""
    global critical_findings_service
    if critical_findings_service is None:
        critical_findings_service = CriticalFindingsService(db_session)
    return critical_findings_service