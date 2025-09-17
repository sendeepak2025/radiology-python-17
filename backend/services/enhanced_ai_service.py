import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid
import numpy as np
from dataclasses import dataclass
from enum import Enum

from services.redis_service import RedisService
from services.ai_service import AIService
from config import settings

logger = logging.getLogger(__name__)

class AbnormalityType(Enum):
    """Types of abnormalities that can be detected."""
    CRITICAL = "critical"
    SIGNIFICANT = "significant"
    MINOR = "minor"
    INCIDENTAL = "incidental"

class ConfidenceLevel(Enum):
    """Confidence levels for AI analysis."""
    HIGH = "high"  # >90%
    MODERATE = "moderate"  # 70-90%
    LOW = "low"  # 50-70%
    UNCERTAIN = "uncertain"  # <50%

@dataclass
class AbnormalityFinding:
    """Represents a detected abnormality."""
    id: str
    type: AbnormalityType
    description: str
    location: str
    confidence: float
    severity_score: int  # 1-10 scale
    requires_urgent_review: bool
    suggested_followup: str
    coordinates: Optional[Dict[str, float]] = None

@dataclass
class DiagnosticAnalysis:
    """Complete diagnostic analysis result."""
    study_uid: str
    analysis_id: str
    exam_type: str
    overall_confidence: float
    confidence_level: ConfidenceLevel
    abnormalities: List[AbnormalityFinding]
    normal_findings: List[str]
    critical_alerts: List[str]
    processing_time: float
    model_version: str
    analysis_timestamp: datetime

class EnhancedAIService(AIService):
    """Enhanced AI service with advanced diagnostic capabilities."""
    
    def __init__(self):
        super().__init__()
        self.model_version = "kiro-enhanced-v2.0"
        self.abnormality_threshold = 0.7
        self.critical_threshold = 0.85
    
    async def perform_diagnostic_analysis(
        self,
        study_uid: str,
        exam_type: str,
        image_data: Optional[bytes] = None
    ) -> DiagnosticAnalysis:
        """Perform comprehensive diagnostic analysis with abnormality detection."""
        
        start_time = datetime.utcnow()
        analysis_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting diagnostic analysis for study {study_uid}")
            
            # Simulate advanced AI processing
            abnormalities = await self._detect_abnormalities(study_uid, exam_type)
            normal_findings = await self._identify_normal_findings(exam_type)
            critical_alerts = await self._generate_critical_alerts(abnormalities)
            
            # Calculate overall confidence
            overall_confidence = await self._calculate_overall_confidence(abnormalities)
            confidence_level = self._determine_confidence_level(overall_confidence)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            analysis = DiagnosticAnalysis(
                study_uid=study_uid,
                analysis_id=analysis_id,
                exam_type=exam_type,
                overall_confidence=overall_confidence,
                confidence_level=confidence_level,
                abnormalities=abnormalities,
                normal_findings=normal_findings,
                critical_alerts=critical_alerts,
                processing_time=processing_time,
                model_version=self.model_version,
                analysis_timestamp=datetime.utcnow()
            )
            
            # Cache analysis results
            await self._cache_analysis_results(analysis)
            
            # Trigger alerts if critical findings
            if critical_alerts:
                await self._trigger_critical_alerts(analysis)
            
            logger.info(f"Diagnostic analysis completed for study {study_uid} in {processing_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in diagnostic analysis for study {study_uid}: {str(e)}")
            raise
    
    async def _detect_abnormalities(
        self,
        study_uid: str,
        exam_type: str
    ) -> List[AbnormalityFinding]:
        """Detect abnormalities based on exam type."""
        
        abnormalities = []
        
        if exam_type == "echo_complete":
            abnormalities.extend(await self._detect_cardiac_abnormalities(study_uid))
        elif exam_type == "vascular_carotid":
            abnormalities.extend(await self._detect_vascular_abnormalities(study_uid))
        elif exam_type == "ct_scan":
            abnormalities.extend(await self._detect_ct_abnormalities(study_uid))
        elif exam_type == "mri_scan":
            abnormalities.extend(await self._detect_mri_abnormalities(study_uid))
        elif exam_type == "xray":
            abnormalities.extend(await self._detect_xray_abnormalities(study_uid))
        
        return abnormalities
    
    async def _detect_cardiac_abnormalities(self, study_uid: str) -> List[AbnormalityFinding]:
        """Detect cardiac abnormalities in echocardiograms."""
        
        # Simulate AI detection with realistic findings
        findings = []
        
        # Simulate detection probability
        if np.random.random() > 0.7:  # 30% chance of abnormality
            findings.append(AbnormalityFinding(
                id=str(uuid.uuid4()),
                type=AbnormalityType.SIGNIFICANT,
                description="Mild mitral regurgitation detected",
                location="Mitral valve",
                confidence=0.82,
                severity_score=4,
                requires_urgent_review=False,
                suggested_followup="Routine cardiology follow-up in 6 months",
                coordinates={"x": 0.45, "y": 0.32, "width": 0.15, "height": 0.12}
            ))
        
        if np.random.random() > 0.85:  # 15% chance of critical finding
            findings.append(AbnormalityFinding(
                id=str(uuid.uuid4()),
                type=AbnormalityType.CRITICAL,
                description="Severe left ventricular dysfunction (EF <35%)",
                location="Left ventricle",
                confidence=0.91,
                severity_score=8,
                requires_urgent_review=True,
                suggested_followup="Urgent cardiology consultation within 24 hours",
                coordinates={"x": 0.25, "y": 0.40, "width": 0.30, "height": 0.25}
            ))
        
        return findings
    
    async def _detect_vascular_abnormalities(self, study_uid: str) -> List[AbnormalityFinding]:
        """Detect vascular abnormalities in carotid studies."""
        
        findings = []
        
        if np.random.random() > 0.6:  # 40% chance of stenosis
            findings.append(AbnormalityFinding(
                id=str(uuid.uuid4()),
                type=AbnormalityType.SIGNIFICANT,
                description="Moderate carotid stenosis (50-69%)",
                location="Right internal carotid artery",
                confidence=0.88,
                severity_score=6,
                requires_urgent_review=False,
                suggested_followup="Vascular surgery consultation recommended",
                coordinates={"x": 0.60, "y": 0.25, "width": 0.20, "height": 0.15}
            ))
        
        return findings
    
    async def _detect_ct_abnormalities(self, study_uid: str) -> List[AbnormalityFinding]:
        """Detect abnormalities in CT scans."""
        
        findings = []
        
        if np.random.random() > 0.8:  # 20% chance of pulmonary finding
            findings.append(AbnormalityFinding(
                id=str(uuid.uuid4()),
                type=AbnormalityType.MINOR,
                description="Small pulmonary nodule identified",
                location="Right upper lobe",
                confidence=0.75,
                severity_score=3,
                requires_urgent_review=False,
                suggested_followup="Follow-up CT in 6 months to assess stability",
                coordinates={"x": 0.70, "y": 0.30, "width": 0.08, "height": 0.08}
            ))
        
        return findings
    
    async def _detect_mri_abnormalities(self, study_uid: str) -> List[AbnormalityFinding]:
        """Detect abnormalities in MRI scans."""
        return []  # Placeholder for MRI-specific detection
    
    async def _detect_xray_abnormalities(self, study_uid: str) -> List[AbnormalityFinding]:
        """Detect abnormalities in X-rays."""
        return []  # Placeholder for X-ray specific detection
    
    async def _identify_normal_findings(self, exam_type: str) -> List[str]:
        """Identify normal anatomical structures and findings."""
        
        normal_findings_map = {
            "echo_complete": [
                "Normal left ventricular size and wall motion",
                "Normal right ventricular function",
                "Normal atrial dimensions",
                "No pericardial effusion"
            ],
            "vascular_carotid": [
                "Patent bilateral carotid arteries",
                "Normal flow velocities",
                "No significant plaque burden"
            ],
            "ct_scan": [
                "Clear lung fields",
                "Normal mediastinal contours",
                "No acute osseous abnormalities"
            ]
        }
        
        return normal_findings_map.get(exam_type, ["Study within normal limits"])
    
    async def _generate_critical_alerts(self, abnormalities: List[AbnormalityFinding]) -> List[str]:
        """Generate critical alerts for urgent findings."""
        
        alerts = []
        for abnormality in abnormalities:
            if abnormality.requires_urgent_review:
                alerts.append(
                    f"CRITICAL: {abnormality.description} - {abnormality.suggested_followup}"
                )
        
        return alerts
    
    async def _calculate_overall_confidence(self, abnormalities: List[AbnormalityFinding]) -> float:
        """Calculate overall confidence score for the analysis."""
        
        if not abnormalities:
            return 0.95  # High confidence for normal studies
        
        # Weight confidence by severity
        total_weighted_confidence = 0
        total_weight = 0
        
        for abnormality in abnormalities:
            weight = abnormality.severity_score / 10.0
            total_weighted_confidence += abnormality.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.80
        
        return min(total_weighted_confidence / total_weight, 0.99)
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level based on score."""
        
        if confidence >= 0.90:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.MODERATE
        elif confidence >= 0.50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    async def _cache_analysis_results(self, analysis: DiagnosticAnalysis) -> None:
        """Cache analysis results for quick retrieval."""
        
        cache_key = f"diagnostic_analysis:{analysis.study_uid}:{analysis.analysis_id}"
        cache_data = {
            "analysis_id": analysis.analysis_id,
            "study_uid": analysis.study_uid,
            "exam_type": analysis.exam_type,
            "overall_confidence": analysis.overall_confidence,
            "confidence_level": analysis.confidence_level.value,
            "abnormalities_count": len(analysis.abnormalities),
            "critical_alerts_count": len(analysis.critical_alerts),
            "processing_time": analysis.processing_time,
            "timestamp": analysis.analysis_timestamp.isoformat()
        }
        
        await self.redis_service.set_with_expiry(
            cache_key, 
            cache_data, 
            expiry_seconds=86400  # 24 hours
        )
    
    async def _trigger_critical_alerts(self, analysis: DiagnosticAnalysis) -> None:
        """Trigger alerts for critical findings."""
        
        alert_data = {
            "study_uid": analysis.study_uid,
            "analysis_id": analysis.analysis_id,
            "critical_alerts": analysis.critical_alerts,
            "timestamp": analysis.analysis_timestamp.isoformat(),
            "requires_immediate_attention": True
        }
        
        # Queue critical alert for immediate processing
        await self.redis_service.enqueue_job(
            queue_name="critical_alerts",
            job_data=alert_data,
            priority=10  # Highest priority
        )
        
        logger.critical(f"Critical findings detected in study {analysis.study_uid}")
    
    async def get_analysis_summary(self, study_uid: str) -> Optional[Dict[str, Any]]:
        """Get summary of diagnostic analysis for a study."""
        
        # Search for cached analysis
        pattern = f"diagnostic_analysis:{study_uid}:*"
        keys = await self.redis_service.scan_keys(pattern)
        
        if not keys:
            return None
        
        # Get the most recent analysis
        latest_key = sorted(keys)[-1]
        return await self.redis_service.get(latest_key)
    
    async def generate_enhanced_report(
        self,
        analysis: DiagnosticAnalysis
    ) -> Dict[str, Any]:
        """Generate enhanced report with diagnostic analysis."""
        
        # Get base report from parent class
        base_report = await self.generate_report_draft(
            analysis.study_uid,
            analysis.exam_type
        )
        
        # Enhance with diagnostic analysis
        enhanced_report = base_report.copy()
        enhanced_report.update({
            "diagnostic_analysis": {
                "analysis_id": analysis.analysis_id,
                "overall_confidence": analysis.overall_confidence,
                "confidence_level": analysis.confidence_level.value,
                "abnormalities": [
                    {
                        "id": ab.id,
                        "type": ab.type.value,
                        "description": ab.description,
                        "location": ab.location,
                        "confidence": ab.confidence,
                        "severity_score": ab.severity_score,
                        "requires_urgent_review": ab.requires_urgent_review,
                        "suggested_followup": ab.suggested_followup,
                        "coordinates": ab.coordinates
                    }
                    for ab in analysis.abnormalities
                ],
                "normal_findings": analysis.normal_findings,
                "critical_alerts": analysis.critical_alerts,
                "processing_time": analysis.processing_time,
                "model_version": analysis.model_version
            }
        })
        
        return enhanced_report