"""
Advanced Radiologist Workflow Management Service

This service implements professional-grade workflow management features
based on 20+ years of radiology practice experience, including:
- Priority-based worklist management
- Subspecialty routing and assignment
- Radiologist load balancing
- Performance analytics and tracking
- Preliminary/final report workflows
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

logger = logging.getLogger(__name__)

class StudyPriority(Enum):
    STAT = "stat"
    URGENT = "urgent"
    ROUTINE = "routine"
    RESEARCH = "research"

class StudyStatus(Enum):
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    ADDENDUM = "addendum"

class SubspecialtyType(Enum):
    GENERAL = "general"
    CARDIAC = "cardiac"
    NEURO = "neuro"
    BODY = "body"
    CHEST = "chest"
    MSK = "msk"
    BREAST = "breast"
    PEDIATRIC = "pediatric"
    INTERVENTIONAL = "interventional"

@dataclass
class RadiologistProfile:
    """Radiologist profile with subspecialty expertise and capacity"""
    radiologist_id: str
    name: str
    subspecialties: List[SubspecialtyType]
    max_concurrent_studies: int
    current_workload: int
    performance_score: float
    availability_status: str
    shift_start: datetime
    shift_end: datetime
    
@dataclass
class WorklistItem:
    """Enhanced worklist item with priority and routing information"""
    study_uid: str
    patient_id: str
    exam_type: str
    priority: StudyPriority
    subspecialty: SubspecialtyType
    assigned_radiologist: Optional[str]
    status: StudyStatus
    arrival_time: datetime
    target_completion_time: datetime
    estimated_reading_time: int
    complexity_score: float
    
class WorkflowService:
    """Advanced workflow management service for radiology practices"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.radiologist_profiles: Dict[str, RadiologistProfile] = {}
        self.subspecialty_rules = self._initialize_subspecialty_rules()
        self.priority_weights = {
            StudyPriority.STAT: 1000,
            StudyPriority.URGENT: 100,
            StudyPriority.ROUTINE: 10,
            StudyPriority.RESEARCH: 1
        }
        
    def _initialize_subspecialty_rules(self) -> Dict[str, SubspecialtyType]:
        """Initialize exam type to subspecialty mapping rules"""
        return {
            # Cardiac subspecialty
            "echo_complete": SubspecialtyType.CARDIAC,
            "echo_stress": SubspecialtyType.CARDIAC,
            "cardiac_ct": SubspecialtyType.CARDIAC,
            "cardiac_mri": SubspecialtyType.CARDIAC,
            "vascular_carotid": SubspecialtyType.CARDIAC,
            "vascular_peripheral": SubspecialtyType.CARDIAC,
            
            # Neuro subspecialty
            "brain_mri": SubspecialtyType.NEURO,
            "brain_ct": SubspecialtyType.NEURO,
            "spine_mri": SubspecialtyType.NEURO,
            "spine_ct": SubspecialtyType.NEURO,
            "head_ct": SubspecialtyType.NEURO,
            
            # Body subspecialty
            "abdomen_ct": SubspecialtyType.BODY,
            "pelvis_ct": SubspecialtyType.BODY,
            "abdomen_mri": SubspecialtyType.BODY,
            "liver_mri": SubspecialtyType.BODY,
            
            # Chest subspecialty
            "chest_ct": SubspecialtyType.CHEST,
            "chest_xray": SubspecialtyType.CHEST,
            "lung_ct": SubspecialtyType.CHEST,
            "pe_ct": SubspecialtyType.CHEST,
            
            # MSK subspecialty
            "knee_mri": SubspecialtyType.MSK,
            "shoulder_mri": SubspecialtyType.MSK,
            "hip_mri": SubspecialtyType.MSK,
            "bone_scan": SubspecialtyType.MSK,
            
            # Breast subspecialty
            "mammography": SubspecialtyType.BREAST,
            "breast_mri": SubspecialtyType.BREAST,
            "breast_ultrasound": SubspecialtyType.BREAST,
            
            # Pediatric subspecialty
            "pediatric_ct": SubspecialtyType.PEDIATRIC,
            "pediatric_mri": SubspecialtyType.PEDIATRIC,
            "pediatric_ultrasound": SubspecialtyType.PEDIATRIC,
        }
    
    async def register_radiologist(self, profile: RadiologistProfile) -> bool:
        """Register a radiologist with their profile and capabilities"""
        try:
            self.radiologist_profiles[profile.radiologist_id] = profile
            logger.info(f"Registered radiologist {profile.name} with subspecialties: {profile.subspecialties}")
            return True
        except Exception as e:
            logger.error(f"Error registering radiologist {profile.radiologist_id}: {str(e)}")
            return False
    
    async def determine_study_priority(self, study_data: Dict[str, Any]) -> StudyPriority:
        """Determine study priority based on clinical indicators and ordering information"""
        try:
            # Check for STAT indicators
            stat_keywords = ["stat", "emergency", "trauma", "stroke", "cardiac arrest", "pe protocol"]
            urgent_keywords = ["urgent", "same day", "asap", "expedite"]
            
            exam_description = study_data.get("study_description", "").lower()
            clinical_history = study_data.get("clinical_history", "").lower()
            
            # STAT priority conditions
            if any(keyword in exam_description or keyword in clinical_history for keyword in stat_keywords):
                return StudyPriority.STAT
            
            # Check for time-sensitive conditions
            if "pe" in exam_description or "pulmonary embolism" in clinical_history:
                return StudyPriority.STAT
            
            if "stroke" in clinical_history or "cva" in clinical_history:
                return StudyPriority.STAT
            
            # Urgent priority conditions
            if any(keyword in exam_description or keyword in clinical_history for keyword in urgent_keywords):
                return StudyPriority.URGENT
            
            # Check patient location for priority
            patient_location = study_data.get("patient_location", "").lower()
            if "er" in patient_location or "emergency" in patient_location or "icu" in patient_location:
                return StudyPriority.URGENT
            
            # Research studies
            if "research" in exam_description or "protocol" in exam_description:
                return StudyPriority.RESEARCH
            
            # Default to routine
            return StudyPriority.ROUTINE
            
        except Exception as e:
            logger.error(f"Error determining study priority: {str(e)}")
            return StudyPriority.ROUTINE
    
    async def determine_subspecialty(self, exam_type: str, study_data: Dict[str, Any]) -> SubspecialtyType:
        """Determine appropriate subspecialty for study routing"""
        try:
            # Direct mapping from exam type
            if exam_type in self.subspecialty_rules:
                return self.subspecialty_rules[exam_type]
            
            # Fallback analysis based on study description
            study_description = study_data.get("study_description", "").lower()
            
            if any(keyword in study_description for keyword in ["cardiac", "heart", "echo", "vascular"]):
                return SubspecialtyType.CARDIAC
            elif any(keyword in study_description for keyword in ["brain", "head", "spine", "neuro"]):
                return SubspecialtyType.NEURO
            elif any(keyword in study_description for keyword in ["chest", "lung", "thorax"]):
                return SubspecialtyType.CHEST
            elif any(keyword in study_description for keyword in ["abdomen", "pelvis", "liver", "kidney"]):
                return SubspecialtyType.BODY
            elif any(keyword in study_description for keyword in ["bone", "joint", "msk", "orthopedic"]):
                return SubspecialtyType.MSK
            elif any(keyword in study_description for keyword in ["breast", "mammography"]):
                return SubspecialtyType.BREAST
            elif any(keyword in study_description for keyword in ["pediatric", "child", "infant"]):
                return SubspecialtyType.PEDIATRIC
            
            # Default to general radiology
            return SubspecialtyType.GENERAL
            
        except Exception as e:
            logger.error(f"Error determining subspecialty: {str(e)}")
            return SubspecialtyType.GENERAL
    
    async def calculate_complexity_score(self, study_data: Dict[str, Any]) -> float:
        """Calculate study complexity score for reading time estimation"""
        try:
            base_score = 1.0
            
            # Modality complexity factors
            modality = study_data.get("modality", "").upper()
            modality_factors = {
                "CT": 1.2,
                "MRI": 1.5,
                "US": 0.8,
                "XR": 0.5,
                "NM": 1.3,
                "PET": 1.8
            }
            
            if modality in modality_factors:
                base_score *= modality_factors[modality]
            
            # Series count factor
            series_count = study_data.get("series_count", 1)
            if series_count > 5:
                base_score *= 1.3
            elif series_count > 10:
                base_score *= 1.6
            
            # Contrast enhancement factor
            study_description = study_data.get("study_description", "").lower()
            if "contrast" in study_description or "enhanced" in study_description:
                base_score *= 1.2
            
            # Multi-phase studies
            if any(phase in study_description for phase in ["arterial", "venous", "delayed", "dynamic"]):
                base_score *= 1.4
            
            # Prior study comparison factor
            if study_data.get("has_priors", False):
                base_score *= 1.3
            
            return min(base_score, 3.0)  # Cap at 3.0
            
        except Exception as e:
            logger.error(f"Error calculating complexity score: {str(e)}")
            return 1.0
    
    async def estimate_reading_time(self, exam_type: str, complexity_score: float) -> int:
        """Estimate reading time in minutes based on exam type and complexity"""
        try:
            # Base reading times by exam type (in minutes)
            base_times = {
                "chest_xray": 2,
                "chest_ct": 8,
                "abdomen_ct": 12,
                "brain_ct": 6,
                "brain_mri": 15,
                "spine_mri": 12,
                "echo_complete": 10,
                "vascular_carotid": 8,
                "mammography": 5,
                "bone_scan": 6,
                "pet_ct": 20,
                "cardiac_mri": 18
            }
            
            base_time = base_times.get(exam_type, 10)  # Default 10 minutes
            estimated_time = int(base_time * complexity_score)
            
            return max(estimated_time, 2)  # Minimum 2 minutes
            
        except Exception as e:
            logger.error(f"Error estimating reading time: {str(e)}")
            return 10
    
    async def find_optimal_radiologist(self, worklist_item: WorklistItem) -> Optional[str]:
        """Find the optimal radiologist for assignment using intelligent load balancing"""
        try:
            eligible_radiologists = []
            
            for rad_id, profile in self.radiologist_profiles.items():
                # Check availability
                if profile.availability_status != "available":
                    continue
                
                # Check shift hours
                current_time = datetime.now()
                if not (profile.shift_start <= current_time <= profile.shift_end):
                    continue
                
                # Check workload capacity
                if profile.current_workload >= profile.max_concurrent_studies:
                    continue
                
                # Check subspecialty match
                if (worklist_item.subspecialty in profile.subspecialties or 
                    SubspecialtyType.GENERAL in profile.subspecialties):
                    
                    # Calculate assignment score
                    subspecialty_match = 1.0 if worklist_item.subspecialty in profile.subspecialties else 0.7
                    workload_factor = 1.0 - (profile.current_workload / profile.max_concurrent_studies)
                    performance_factor = profile.performance_score
                    
                    assignment_score = subspecialty_match * workload_factor * performance_factor
                    
                    eligible_radiologists.append((rad_id, assignment_score))
            
            if not eligible_radiologists:
                logger.warning(f"No eligible radiologists found for study {worklist_item.study_uid}")
                return None
            
            # Sort by assignment score and return best match
            eligible_radiologists.sort(key=lambda x: x[1], reverse=True)
            selected_radiologist = eligible_radiologists[0][0]
            
            logger.info(f"Assigned study {worklist_item.study_uid} to radiologist {selected_radiologist}")
            return selected_radiologist
            
        except Exception as e:
            logger.error(f"Error finding optimal radiologist: {str(e)}")
            return None
    
    async def create_worklist_item(self, study_data: Dict[str, Any]) -> WorklistItem:
        """Create a comprehensive worklist item with all workflow metadata"""
        try:
            study_uid = study_data["study_uid"]
            exam_type = study_data.get("exam_type", "unknown")
            
            # Determine workflow parameters
            priority = await self.determine_study_priority(study_data)
            subspecialty = await self.determine_subspecialty(exam_type, study_data)
            complexity_score = await self.calculate_complexity_score(study_data)
            estimated_reading_time = await self.estimate_reading_time(exam_type, complexity_score)
            
            # Calculate target completion time based on priority
            arrival_time = datetime.now()
            priority_targets = {
                StudyPriority.STAT: 15,      # 15 minutes
                StudyPriority.URGENT: 60,    # 1 hour
                StudyPriority.ROUTINE: 240,  # 4 hours
                StudyPriority.RESEARCH: 1440 # 24 hours
            }
            
            target_minutes = priority_targets.get(priority, 240)
            target_completion_time = arrival_time + timedelta(minutes=target_minutes)
            
            worklist_item = WorklistItem(
                study_uid=study_uid,
                patient_id=study_data.get("patient_id", ""),
                exam_type=exam_type,
                priority=priority,
                subspecialty=subspecialty,
                assigned_radiologist=None,
                status=StudyStatus.UNASSIGNED,
                arrival_time=arrival_time,
                target_completion_time=target_completion_time,
                estimated_reading_time=estimated_reading_time,
                complexity_score=complexity_score
            )
            
            return worklist_item
            
        except Exception as e:
            logger.error(f"Error creating worklist item: {str(e)}")
            raise
    
    async def assign_study(self, worklist_item: WorklistItem) -> bool:
        """Assign study to optimal radiologist"""
        try:
            optimal_radiologist = await self.find_optimal_radiologist(worklist_item)
            
            if optimal_radiologist:
                worklist_item.assigned_radiologist = optimal_radiologist
                worklist_item.status = StudyStatus.ASSIGNED
                
                # Update radiologist workload
                if optimal_radiologist in self.radiologist_profiles:
                    self.radiologist_profiles[optimal_radiologist].current_workload += 1
                
                logger.info(f"Successfully assigned study {worklist_item.study_uid} to {optimal_radiologist}")
                return True
            else:
                logger.warning(f"Could not assign study {worklist_item.study_uid} - no available radiologists")
                return False
                
        except Exception as e:
            logger.error(f"Error assigning study: {str(e)}")
            return False
    
    async def get_prioritized_worklist(self, radiologist_id: Optional[str] = None) -> List[WorklistItem]:
        """Get prioritized worklist for a specific radiologist or all unassigned studies"""
        try:
            # This would typically query the database
            # For now, returning a mock prioritized list
            worklist = []
            
            # In a real implementation, this would:
            # 1. Query database for studies matching criteria
            # 2. Apply priority weighting and sorting
            # 3. Consider subspecialty preferences
            # 4. Factor in turnaround time requirements
            
            return sorted(worklist, key=lambda x: (
                -self.priority_weights[x.priority],  # Higher priority first
                x.arrival_time,                      # Older studies first within priority
                -x.complexity_score                  # More complex studies first within same priority/time
            ))
            
        except Exception as e:
            logger.error(f"Error getting prioritized worklist: {str(e)}")
            return []
    
    async def update_study_status(self, study_uid: str, new_status: StudyStatus, radiologist_id: str) -> bool:
        """Update study status and manage radiologist workload"""
        try:
            # Update study status in database
            # This would be implemented with actual database operations
            
            # Update radiologist workload if study is completed
            if new_status in [StudyStatus.FINAL, StudyStatus.PRELIMINARY]:
                if radiologist_id in self.radiologist_profiles:
                    self.radiologist_profiles[radiologist_id].current_workload = max(
                        0, self.radiologist_profiles[radiologist_id].current_workload - 1
                    )
            
            logger.info(f"Updated study {study_uid} status to {new_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating study status: {str(e)}")
            return False
    
    async def get_performance_metrics(self, radiologist_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive performance metrics for a radiologist"""
        try:
            # This would query actual database for metrics
            # Mock implementation for demonstration
            
            metrics = {
                "radiologist_id": radiologist_id,
                "period_days": days,
                "studies_read": 245,
                "average_turnaround_time": 28.5,  # minutes
                "stat_turnaround_time": 12.3,
                "urgent_turnaround_time": 45.2,
                "routine_turnaround_time": 156.7,
                "quality_score": 4.7,  # out of 5
                "peer_review_score": 4.8,
                "discrepancy_rate": 0.02,  # 2%
                "critical_findings_rate": 0.08,  # 8%
                "addendum_rate": 0.03,  # 3%
                "productivity_percentile": 85,
                "subspecialty_distribution": {
                    "cardiac": 45,
                    "general": 30,
                    "chest": 25
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}

# Global workflow service instance
workflow_service = None

def get_workflow_service(db_session: Session) -> WorkflowService:
    """Get or create workflow service instance"""
    global workflow_service
    if workflow_service is None:
        workflow_service = WorkflowService(db_session)
    return workflow_service