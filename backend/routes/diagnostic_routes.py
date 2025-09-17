from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from services.enhanced_ai_service import EnhancedAIService, DiagnosticAnalysis
from services.study_service import StudyService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/studies", tags=["diagnostic"])

# Dependency injection
def get_enhanced_ai_service() -> EnhancedAIService:
    return EnhancedAIService()

def get_study_service() -> StudyService:
    return StudyService()

@router.post("/{study_uid}/diagnostic-analysis")
async def perform_diagnostic_analysis(
    study_uid: str,
    exam_type: str,
    ai_service: EnhancedAIService = Depends(get_enhanced_ai_service)
) -> Dict[str, Any]:
    """Perform AI diagnostic analysis on a study."""
    
    try:
        analysis = await ai_service.perform_diagnostic_analysis(
            study_uid=study_uid,
            exam_type=exam_type
        )
        
        return {
            "success": True,
            "diagnostic_analysis": {
                "analysis_id": analysis.analysis_id,
                "study_uid": analysis.study_uid,
                "exam_type": analysis.exam_type,
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
                "model_version": analysis.model_version,
                "analysis_timestamp": analysis.analysis_timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error performing diagnostic analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{study_uid}/diagnostic-analysis")
async def get_diagnostic_analysis(
    study_uid: str,
    ai_service: EnhancedAIService = Depends(get_enhanced_ai_service)
) -> Dict[str, Any]:
    """Get existing diagnostic analysis for a study."""
    
    try:
        analysis_summary = await ai_service.get_analysis_summary(study_uid)
        
        if not analysis_summary:
            raise HTTPException(status_code=404, detail="No diagnostic analysis found")
        
        return {
            "success": True,
            "diagnostic_analysis": analysis_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving diagnostic analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{study_uid}/enhanced-report")
async def generate_enhanced_report(
    study_uid: str,
    exam_type: str,
    ai_service: EnhancedAIService = Depends(get_enhanced_ai_service)
) -> Dict[str, Any]:
    """Generate enhanced report with diagnostic analysis."""
    
    try:
        # Perform diagnostic analysis first
        analysis = await ai_service.perform_diagnostic_analysis(
            study_uid=study_uid,
            exam_type=exam_type
        )
        
        # Generate enhanced report
        enhanced_report = await ai_service.generate_enhanced_report(analysis)
        
        return {
            "success": True,
            "enhanced_report": enhanced_report
        }
        
    except Exception as e:
        logger.error(f"Error generating enhanced report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))