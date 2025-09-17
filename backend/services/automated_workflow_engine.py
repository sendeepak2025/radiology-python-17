"""
Automated Workflow Engine for Kiro-mini

This service provides intelligent automation for radiology workflows including:
- Automated study routing and assignment
- Real-time notification system
- Workflow monitoring and optimization
- Escalation management
- Performance analytics
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import json
from sqlalchemy.orm import Session

from .workflow_service import (
    WorkflowService, WorklistItem, StudyPriority, StudyStatus, 
    SubspecialtyType, RadiologistProfile
)
from .redis_service import get_redis_client
from .websocket_billing_service import WebSocketManager

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    STUDY_ASSIGNED = "study_assigned"
    STUDY_OVERDUE = "study_overdue"
    CRITICAL_FINDING = "critical_finding"
    WORKLOAD_HIGH = "workload_high"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_ALERT = "performance_alert"

class EscalationLevel(Enum):
    NONE = "none"
    SUPERVISOR = "supervisor"
    DEPARTMENT_HEAD = "department_head"
    ADMINISTRATION = "administration"

@dataclass
class NotificationRule:
    """Defines when and how to send notifications"""
    rule_id: str
    name: str
    condition: str  # JSON condition string
    notification_type: NotificationType
    recipients: List[str]
    escalation_level: EscalationLevel
    delay_minutes: int = 0
    repeat_interval_minutes: Optional[int] = None
    max_repeats: int = 3
    active: bool = True

@dataclass
class WorkflowEvent:
    """Represents a workflow event for tracking and automation"""
    event_id: str
    event_type: str
    study_uid: str
    radiologist_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False

@dataclass
class AutomationRule:
    """Defines automated actions based on conditions"""
    rule_id: str
    name: str
    trigger_condition: str
    action_type: str
    action_parameters: Dict[str, Any]
    priority: int = 1
    active: bool = True

class AutomatedWorkflowEngine:
    """Advanced workflow automation engine"""
    
    def __init__(self, db_session: Session, workflow_service: WorkflowService):
        self.db = db_session
        self.workflow_service = workflow_service
        self.redis_client = get_redis_client()
        self.websocket_manager = WebSocketManager()
        
        # Automation components
        self.notification_rules: Dict[str, NotificationRule] = {}
        self.automation_rules: Dict[str, AutomationRule] = {}
        self.pending_notifications: List[Dict[str, Any]] = []
        self.workflow_events: List[WorkflowEvent] = []
        
        # Performance tracking
        self.performance_metrics = {
            "studies_processed": 0,
            "average_assignment_time": 0.0,
            "automation_success_rate": 0.0,
            "notification_delivery_rate": 0.0
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
        # Start background tasks
        self.running = False
        
    def _initialize_default_rules(self):
        """Initialize default notification and automation rules"""
        
        # Default notification rules
        default_notifications = [
            NotificationRule(
                rule_id="stat_overdue",
                name="STAT Study Overdue",
                condition='{"priority": "stat", "overdue_minutes": 15}',
                notification_type=NotificationType.STUDY_OVERDUE,
                recipients=["supervisor", "radiologist"],
                escalation_level=EscalationLevel.SUPERVISOR,
                repeat_interval_minutes=5,
                max_repeats=3
            ),
            NotificationRule(
                rule_id="urgent_overdue",
                name="Urgent Study Overdue",
                condition='{"priority": "urgent", "overdue_minutes": 60}',
                notification_type=NotificationType.STUDY_OVERDUE,
                recipients=["radiologist"],
                escalation_level=EscalationLevel.NONE,
                repeat_interval_minutes=30,
                max_repeats=2
            ),
            NotificationRule(
                rule_id="high_workload",
                name="High Workload Alert",
                condition='{"workload_percentage": 90}',
                notification_type=NotificationType.WORKLOAD_HIGH,
                recipients=["supervisor"],
                escalation_level=EscalationLevel.SUPERVISOR
            )
        ]
        
        for rule in default_notifications:
            self.notification_rules[rule.rule_id] = rule
        
        # Default automation rules
        default_automations = [
            AutomationRule(
                rule_id="auto_assign_routine",
                name="Auto-assign Routine Studies",
                trigger_condition='{"priority": "routine", "unassigned_minutes": 5}',
                action_type="auto_assign",
                action_parameters={"method": "load_balanced"},
                priority=1
            ),
            AutomationRule(
                rule_id="escalate_stat_studies",
                name="Escalate Unassigned STAT Studies",
                trigger_condition='{"priority": "stat", "unassigned_minutes": 10}',
                action_type="escalate_assignment",
                action_parameters={"escalation_level": "supervisor"},
                priority=10
            )
        ]
        
        for rule in default_automations:
            self.automation_rules[rule.rule_id] = rule
    
    async def start_automation_engine(self):
        """Start the automated workflow engine"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting automated workflow engine")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._monitor_workflow_events()),
            asyncio.create_task(self._process_automation_rules()),
            asyncio.create_task(self._handle_notifications()),
            asyncio.create_task(self._monitor_performance_metrics())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in automation engine: {str(e)}")
        finally:
            self.running = False
    
    async def stop_automation_engine(self):
        """Stop the automated workflow engine"""
        self.running = False
        logger.info("Stopped automated workflow engine")
    
    async def _monitor_workflow_events(self):
        """Monitor workflow events and trigger automation"""
        while self.running:
            try:
                # Check for new studies
                await self._check_new_studies()
                
                # Check for overdue studies
                await self._check_overdue_studies()
                
                # Check radiologist workloads
                await self._check_workload_status()
                
                # Process pending events
                await self._process_pending_events()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring workflow events: {str(e)}")
                await asyncio.sleep(60)
    
    async def _process_automation_rules(self):
        """Process automation rules and execute actions"""
        while self.running:
            try:
                for rule in self.automation_rules.values():
                    if not rule.active:
                        continue
                    
                    # Check if rule conditions are met
                    if await self._evaluate_rule_condition(rule.trigger_condition):
                        await self._execute_automation_action(rule)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error processing automation rules: {str(e)}")
                await asyncio.sleep(120)
    
    async def _handle_notifications(self):
        """Handle notification delivery and escalation"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Process pending notifications
                for notification in self.pending_notifications[:]:
                    if current_time >= notification["scheduled_time"]:
                        await self._send_notification(notification)
                        self.pending_notifications.remove(notification)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error handling notifications: {str(e)}")
                await asyncio.sleep(30)
    
    async def _monitor_performance_metrics(self):
        """Monitor and update performance metrics"""
        while self.running:
            try:
                # Calculate current metrics
                metrics = await self._calculate_performance_metrics()
                self.performance_metrics.update(metrics)
                
                # Store metrics in Redis for real-time access
                await self.redis_client.setex(
                    "workflow_performance_metrics",
                    300,  # 5 minutes TTL
                    json.dumps(metrics)
                )
                
                # Broadcast metrics via WebSocket
                await self.websocket_manager.broadcast_to_group(
                    "workflow_monitoring",
                    {
                        "type": "performance_update",
                        "data": metrics,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring performance: {str(e)}")
                await asyncio.sleep(600)
    
    async def process_new_study(self, study_data: Dict[str, Any]) -> bool:
        """Process a new study through the automated workflow"""
        try:
            # Create worklist item
            worklist_item = await self.workflow_service.create_worklist_item(study_data)
            
            # Log workflow event
            event = WorkflowEvent(
                event_id=f"study_received_{worklist_item.study_uid}_{int(datetime.now().timestamp())}",
                event_type="study_received",
                study_uid=worklist_item.study_uid,
                radiologist_id=None,
                timestamp=datetime.now(),
                data={"priority": worklist_item.priority.value, "subspecialty": worklist_item.subspecialty.value}
            )
            self.workflow_events.append(event)
            
            # Attempt automatic assignment for high-priority studies
            if worklist_item.priority in [StudyPriority.STAT, StudyPriority.URGENT]:
                assignment_success = await self.workflow_service.assign_study(worklist_item)
                
                if assignment_success:
                    # Send assignment notification
                    await self._create_notification(
                        NotificationType.STUDY_ASSIGNED,
                        worklist_item.study_uid,
                        worklist_item.assigned_radiologist,
                        {"priority": worklist_item.priority.value}
                    )
                else:
                    # Schedule escalation for unassigned high-priority studies
                    await self._schedule_escalation(worklist_item)
            
            # Update performance metrics
            self.performance_metrics["studies_processed"] += 1
            
            logger.info(f"Processed new study {worklist_item.study_uid} with priority {worklist_item.priority.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing new study: {str(e)}")
            return False
    
    async def _create_notification(self, notification_type: NotificationType, 
                                 study_uid: str, recipient_id: Optional[str], 
                                 data: Dict[str, Any]):
        """Create and schedule a notification"""
        notification = {
            "id": f"notif_{int(datetime.now().timestamp())}",
            "type": notification_type.value,
            "study_uid": study_uid,
            "recipient_id": recipient_id,
            "data": data,
            "created_time": datetime.now(),
            "scheduled_time": datetime.now(),
            "attempts": 0,
            "max_attempts": 3
        }
        
        self.pending_notifications.append(notification)
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification via appropriate channel"""
        try:
            # Send via WebSocket for real-time notifications
            await self.websocket_manager.send_to_user(
                notification["recipient_id"],
                {
                    "type": "workflow_notification",
                    "notification_type": notification["type"],
                    "study_uid": notification["study_uid"],
                    "data": notification["data"],
                    "timestamp": notification["created_time"].isoformat()
                }
            )
            
            # Store notification in Redis for persistence
            await self.redis_client.lpush(
                f"notifications:{notification['recipient_id']}",
                json.dumps(notification, default=str)
            )
            
            # Trim notification list to last 100
            await self.redis_client.ltrim(f"notifications:{notification['recipient_id']}", 0, 99)
            
            logger.info(f"Sent notification {notification['id']} to {notification['recipient_id']}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            notification["attempts"] += 1
            
            if notification["attempts"] < notification["max_attempts"]:
                # Reschedule for retry
                notification["scheduled_time"] = datetime.now() + timedelta(minutes=5)
                self.pending_notifications.append(notification)
    
    async def _check_new_studies(self):
        """Check for new studies that need processing"""
        # This would query the database for new unprocessed studies
        # Mock implementation for demonstration
        pass
    
    async def _check_overdue_studies(self):
        """Check for overdue studies and trigger notifications"""
        # This would query for studies past their target completion time
        # Mock implementation for demonstration
        pass
    
    async def _check_workload_status(self):
        """Check radiologist workload and trigger alerts if needed"""
        for radiologist_id, profile in self.workflow_service.radiologist_profiles.items():
            workload_percentage = (profile.current_workload / profile.max_concurrent_studies) * 100
            
            if workload_percentage >= 90:
                await self._create_notification(
                    NotificationType.WORKLOAD_HIGH,
                    "",
                    "supervisor",
                    {"radiologist_id": radiologist_id, "workload_percentage": workload_percentage}
                )
    
    async def _process_pending_events(self):
        """Process pending workflow events"""
        for event in self.workflow_events[:]:
            if not event.processed:
                # Process event based on type
                await self._handle_workflow_event(event)
                event.processed = True
    
    async def _handle_workflow_event(self, event: WorkflowEvent):
        """Handle a specific workflow event"""
        # Implementation would handle different event types
        pass
    
    async def _evaluate_rule_condition(self, condition: str) -> bool:
        """Evaluate if a rule condition is met"""
        try:
            # Parse condition JSON and evaluate against current state
            condition_data = json.loads(condition)
            # Implementation would evaluate the condition
            return False  # Mock implementation
        except Exception as e:
            logger.error(f"Error evaluating rule condition: {str(e)}")
            return False
    
    async def _execute_automation_action(self, rule: AutomationRule):
        """Execute an automation action"""
        try:
            if rule.action_type == "auto_assign":
                await self._auto_assign_studies(rule.action_parameters)
            elif rule.action_type == "escalate_assignment":
                await self._escalate_unassigned_studies(rule.action_parameters)
            
            logger.info(f"Executed automation rule: {rule.name}")
            
        except Exception as e:
            logger.error(f"Error executing automation action: {str(e)}")
    
    async def _auto_assign_studies(self, parameters: Dict[str, Any]):
        """Automatically assign studies based on parameters"""
        # Implementation would find unassigned studies and assign them
        pass
    
    async def _escalate_unassigned_studies(self, parameters: Dict[str, Any]):
        """Escalate unassigned studies to supervisors"""
        # Implementation would escalate to appropriate personnel
        pass
    
    async def _schedule_escalation(self, worklist_item: WorklistItem):
        """Schedule escalation for unassigned high-priority studies"""
        escalation_delay = 10 if worklist_item.priority == StudyPriority.STAT else 30
        
        notification = {
            "id": f"escalation_{worklist_item.study_uid}_{int(datetime.now().timestamp())}",
            "type": "escalation",
            "study_uid": worklist_item.study_uid,
            "recipient_id": "supervisor",
            "data": {"priority": worklist_item.priority.value, "reason": "unassigned"},
            "created_time": datetime.now(),
            "scheduled_time": datetime.now() + timedelta(minutes=escalation_delay),
            "attempts": 0,
            "max_attempts": 1
        }
        
        self.pending_notifications.append(notification)
    
    async def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate current performance metrics"""
        return {
            "studies_processed_today": self.performance_metrics["studies_processed"],
            "average_assignment_time_minutes": 2.3,
            "automation_success_rate": 0.94,
            "notification_delivery_rate": 0.98,
            "overdue_studies_count": 3,
            "unassigned_studies_count": 7,
            "active_radiologists": len([p for p in self.workflow_service.radiologist_profiles.values() 
                                       if p.availability_status == "available"]),
            "average_workload_percentage": 67.5,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_workflow_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive workflow dashboard data"""
        try:
            # Get current worklist statistics
            worklist_stats = await self._get_worklist_statistics()
            
            # Get radiologist status
            radiologist_status = await self._get_radiologist_status()
            
            # Get recent notifications
            recent_notifications = await self._get_recent_notifications()
            
            # Get performance metrics
            performance_metrics = await self._calculate_performance_metrics()
            
            return {
                "worklist_statistics": worklist_stats,
                "radiologist_status": radiologist_status,
                "recent_notifications": recent_notifications,
                "performance_metrics": performance_metrics,
                "automation_rules_active": len([r for r in self.automation_rules.values() if r.active]),
                "notification_rules_active": len([r for r in self.notification_rules.values() if r.active]),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow dashboard data: {str(e)}")
            return {}
    
    async def _get_worklist_statistics(self) -> Dict[str, Any]:
        """Get current worklist statistics"""
        # Mock implementation - would query actual database
        return {
            "total_studies": 45,
            "unassigned_studies": 7,
            "in_progress_studies": 23,
            "overdue_studies": 3,
            "stat_studies": 2,
            "urgent_studies": 8,
            "routine_studies": 35
        }
    
    async def _get_radiologist_status(self) -> List[Dict[str, Any]]:
        """Get current radiologist status"""
        status_list = []
        
        for rad_id, profile in self.workflow_service.radiologist_profiles.items():
            status_list.append({
                "radiologist_id": rad_id,
                "name": profile.name,
                "availability_status": profile.availability_status,
                "current_workload": profile.current_workload,
                "max_workload": profile.max_concurrent_studies,
                "workload_percentage": (profile.current_workload / profile.max_concurrent_studies) * 100,
                "subspecialties": [s.value for s in profile.subspecialties],
                "performance_score": profile.performance_score
            })
        
        return status_list
    
    async def _get_recent_notifications(self) -> List[Dict[str, Any]]:
        """Get recent notifications"""
        # Mock implementation - would query Redis or database
        return [
            {
                "id": "notif_001",
                "type": "study_assigned",
                "message": "STAT CT Head assigned to Dr. Smith",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "severity": "info"
            },
            {
                "id": "notif_002",
                "type": "study_overdue",
                "message": "Urgent MRI Brain overdue by 15 minutes",
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "severity": "warning"
            }
        ]

# Global automation engine instance
automation_engine = None

def get_automation_engine(db_session: Session, workflow_service: WorkflowService) -> AutomatedWorkflowEngine:
    """Get or create automation engine instance"""
    global automation_engine
    if automation_engine is None:
        automation_engine = AutomatedWorkflowEngine(db_session, workflow_service)
    return automation_engine