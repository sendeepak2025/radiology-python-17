"""
Workflow Management API Routes

Provides endpoints for workflow automation, monitoring, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import get_db
from ..services.workflow_service import get_workflow_service, WorkflowService
from ..services.automated_workflow_engine import get_automation_engine, AutomatedWorkflowEngine
from ..schemas import WorkflowResponse, NotificationResponse

router = APIRouter(prefix="/workflow", tags=["workflow"])

@router.post("/studies/process")
async def process_new_study(
    study_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process a new study through the automated workflow"""
    try:
        workflow_service = get_workflow_service(db)
        automation_engine = get_automation_engine(db, workflow_service)
        
        # Process study in background
        background_tasks.add_task(automation_engine.process_new_study, study_data)
        
        return {
            "status": "success",
            "message": "Study queued for processing",
            "study_uid": study_data.get("study_uid")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing study: {str(e)}")

@router.get("/dashboard")
async def get_workflow_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive workflow dashboard data"""
    try:
        workflow_service = get_workflow_service(db)
        automation_engine = get_automation_engine(db, workflow_service)
        
        dashboard_data = await automation_engine.get_workflow_dashboard_data()
        
        return {
            "status": "success",
            "data": dashboard_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")

@router.get("/worklist")
async def get_prioritized_worklist(
    radiologist_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get prioritized worklist for a radiologist or all unassigned studies"""
    try:
        workflow_service = get_workflow_service(db)
        
        worklist = await workflow_service.get_prioritized_worklist(radiologist_id)
        
        return {
            "status": "success",
            "worklist": [
                {
                    "study_uid": item.study_uid,
                    "patient_id": item.patient_id,
                    "exam_type": item.exam_type,
                    "priority": item.priority.value,
                    "subspecialty": item.subspecialty.value,
                    "assigned_radiologist": item.assigned_radiologist,
                    "status": item.status.value,
                    "arrival_time": item.arrival_time.isoformat(),
                    "target_completion_time": item.target_completion_time.isoformat(),
                    "estimated_reading_time": item.estimated_reading_time,
                    "complexity_score": item.complexity_score
                }
                for item in worklist
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting worklist: {str(e)}")

@router.post("/studies/{study_uid}/assign")
async def assign_study(
    study_uid: str,
    radiologist_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Assign a study to a radiologist (manual or automatic)"""
    try:
        workflow_service = get_workflow_service(db)
        
        # This would typically fetch the worklist item from database
        # For now, creating a mock item
        from ..services.workflow_service import WorklistItem, StudyPriority, StudyStatus, SubspecialtyType
        
        # Mock worklist item - in real implementation, fetch from database
        worklist_item = WorklistItem(
            study_uid=study_uid,
            patient_id="PAT001",
            exam_type="chest_ct",
            priority=StudyPriority.ROUTINE,
            subspecialty=SubspecialtyType.CHEST,
            assigned_radiologist=radiologist_id,
            status=StudyStatus.UNASSIGNED,
            arrival_time=datetime.now(),
            target_completion_time=datetime.now(),
            estimated_reading_time=10,
            complexity_score=1.2
        )
        
        success = await workflow_service.assign_study(worklist_item)
        
        if success:
            return {
                "status": "success",
                "message": f"Study {study_uid} assigned successfully",
                "assigned_radiologist": worklist_item.assigned_radiologist
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to assign study")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning study: {str(e)}")

@router.put("/studies/{study_uid}/status")
async def update_study_status(
    study_uid: str,
    new_status: str,
    radiologist_id: str,
    db: Session = Depends(get_db)
):
    """Update study status"""
    try:
        workflow_service = get_workflow_service(db)
        
        from ..services.workflow_service import StudyStatus
        
        # Convert string to enum
        status_enum = StudyStatus(new_status)
        
        success = await workflow_service.update_study_status(study_uid, status_enum, radiologist_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Study {study_uid} status updated to {new_status}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update study status")
            
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating study status: {str(e)}")

@router.get("/radiologists/{radiologist_id}/performance")
async def get_radiologist_performance(
    radiologist_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get performance metrics for a radiologist"""
    try:
        workflow_service = get_workflow_service(db)
        
        metrics = await workflow_service.get_performance_metrics(radiologist_id, days)
        
        return {
            "status": "success",
            "metrics": metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")

@router.get("/notifications/{user_id}")
async def get_user_notifications(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get notifications for a user"""
    try:
        workflow_service = get_workflow_service(db)
        automation_engine = get_automation_engine(db, workflow_service)
        
        # Get notifications from Redis
        notifications = await automation_engine.redis_client.lrange(
            f"notifications:{user_id}", 0, limit - 1
        )
        
        parsed_notifications = []
        for notif in notifications:
            try:
                import json
                parsed_notifications.append(json.loads(notif))
            except json.JSONDecodeError:
                continue
        
        return {
            "status": "success",
            "notifications": parsed_notifications
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notifications: {str(e)}")

@router.post("/automation/start")
async def start_automation_engine(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start the automated workflow engine"""
    try:
        workflow_service = get_workflow_service(db)
        automation_engine = get_automation_engine(db, workflow_service)
        
        # Start automation engine in background
        background_tasks.add_task(automation_engine.start_automation_engine)
        
        return {
            "status": "success",
            "message": "Automation engine started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting automation engine: {str(e)}")

@router.post("/automation/stop")
async def stop_automation_engine(
    db: Session = Depends(get_db)
):
    """Stop the automated workflow engine"""
    try:
        workflow_service = get_workflow_service(db)
        automation_engine = get_automation_engine(db, workflow_service)
        
        await automation_engine.stop_automation_engine()
        
        return {
            "status": "success",
            "message": "Automation engine stopped"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping automation engine: {str(e)}")