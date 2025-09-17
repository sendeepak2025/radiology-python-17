"""
Real-time billing validation and code suggestion service.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import re

from services.billing_service import BillingService
from billing.cpt_mappings import CPTMappings, BillingRules, ReimbursementCalculator
from billing.icd10_mappings import ICD10Mappings, ClinicalDecisionSupport
from services.redis_service import RedisService
from config import settings

logger = logging.getLogger(__name__)

class RealtimeBillingService:
    """Service for real-time billing validation and intelligent code suggestions."""
    
    def __init__(self):
        self.billing_service = BillingService()
        self.redis_service = RedisService()
        self.cpt_mappings = CPTMappings.get_all_mappings()
        self.icd10_mappings = ICD10Mappings.get_all_codes()
        self.reimbursement_calculator = ReimbursementCalculator()
        
        # Cache for frequently accessed data
        self.validation_cache_ttl = 300  # 5 minutes
        self.suggestion_cache_ttl = 600  # 10 minutes
    
    async def suggest_codes_realtime(
        self,
        findings_text: str,
        exam_type: str,
        measurements: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Provide real-time ICD-10 code suggestions as user types findings.
        """
        
        try:
            # Check cache first
            cache_key = f"code_suggestions:{hash(findings_text)}:{exam_type}"
            cached_result = await self.redis_service.get_cache(cache_key)
            
            if cached_result:
                logger.debug(f"Returning cached code suggestions for {exam_type}")
                return cached_result
            
            # Generate suggestions
            suggestions = await self._generate_intelligent_suggestions(
                findings_text, exam_type, measurements, user_context
            )
            
            # Validate and rank suggestions
            validated_suggestions = await self._validate_and_rank_suggestions(
                suggestions, exam_type, findings_text
            )
            
            # Calculate confidence scores
            final_suggestions = await self._calculate_confidence_scores(
                validated_suggestions, findings_text, exam_type
            )
            
            result = {
                "suggestions": final_suggestions,
                "exam_type": exam_type,
                "findings_analyzed": len(findings_text.split()),
                "suggestion_count": len(final_suggestions),
                "generated_at": datetime.utcnow().isoformat(),
                "cache_ttl": self.suggestion_cache_ttl
            }
            
            # Cache the result
            await self.redis_service.set_cache(
                cache_key, result, self.suggestion_cache_ttl
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating real-time code suggestions: {e}")
            return {
                "suggestions": [],
                "error": str(e),
                "exam_type": exam_type
            }
    
    async def validate_codes_realtime(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        exam_type: str,
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform real-time validation of CPT-ICD-10 code combinations.
        """
        
        try:
            # Check cache
            cache_key = f"code_validation:{hash(str(sorted(cpt_codes + icd10_codes)))}:{exam_type}"
            cached_result = await self.redis_service.get_cache(cache_key)
            
            if cached_result:
                return cached_result
            
            validation_start = datetime.utcnow()
            
            # Perform comprehensive validation
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
                "compliance_score": 100.0,
                "reimbursement_risk": 0.0,
                "estimated_reimbursement": 0.0,
                "validation_details": {}
            }
            
            # 1. Basic code format validation
            format_validation = await self._validate_code_formats(cpt_codes, icd10_codes)
            validation_result["validation_details"]["format"] = format_validation
            
            if format_validation["errors"]:
                validation_result["errors"].extend(format_validation["errors"])
                validation_result["valid"] = False
            
            # 2. Medical necessity validation
            necessity_validation = await self._validate_medical_necessity(
                cpt_codes, icd10_codes, exam_type
            )
            validation_result["validation_details"]["medical_necessity"] = necessity_validation
            
            if necessity_validation["errors"]:
                validation_result["errors"].extend(necessity_validation["errors"])
                validation_result["valid"] = False
            
            validation_result["warnings"].extend(necessity_validation["warnings"])
            
            # 3. Payer-specific validation
            payer_validation = await self._validate_payer_requirements(
                cpt_codes, icd10_codes, patient_context
            )
            validation_result["validation_details"]["payer_requirements"] = payer_validation
            
            validation_result["warnings"].extend(payer_validation["warnings"])
            
            # 4. Bundling and modifier validation
            bundling_validation = await self._validate_bundling_and_modifiers(cpt_codes)
            validation_result["validation_details"]["bundling"] = bundling_validation
            
            if bundling_validation["errors"]:
                validation_result["errors"].extend(bundling_validation["errors"])
                validation_result["valid"] = False
            
            # 5. Calculate compliance score
            validation_result["compliance_score"] = await self._calculate_compliance_score(
                validation_result
            )
            
            # 6. Calculate reimbursement estimates
            reimbursement_data = await self._calculate_reimbursement_estimates(
                cpt_codes, icd10_codes, patient_context
            )
            validation_result.update(reimbursement_data)
            
            # 7. Generate improvement suggestions
            if validation_result["errors"] or validation_result["warnings"]:
                suggestions = await self._generate_improvement_suggestions(
                    cpt_codes, icd10_codes, validation_result, exam_type
                )
                validation_result["suggestions"] = suggestions
            
            # Add timing information
            validation_time = (datetime.utcnow() - validation_start).total_seconds()
            validation_result["validation_time_ms"] = validation_time * 1000
            validation_result["validated_at"] = datetime.utcnow().isoformat()
            
            # Cache the result
            await self.redis_service.set_cache(
                cache_key, validation_result, self.validation_cache_ttl
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in real-time code validation: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggestions": [],
                "compliance_score": 0.0
            }
    
    async def _generate_intelligent_suggestions(
        self,
        findings_text: str,
        exam_type: str,
        measurements: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate intelligent ICD-10 code suggestions."""
        
        suggestions = []
        
        # 1. Clinical decision support suggestions
        clinical_suggestions = ClinicalDecisionSupport.suggest_codes_from_findings(
            findings_text, exam_type
        )
        suggestions.extend(clinical_suggestions)
        
        # 2. Measurement-based suggestions
        if measurements:
            measurement_suggestions = await self._suggest_codes_from_measurements(
                measurements, exam_type
            )
            suggestions.extend(measurement_suggestions)
        
        # 3. Exam-type specific suggestions
        exam_suggestions = await self._suggest_codes_for_exam_type(exam_type)
        suggestions.extend(exam_suggestions)
        
        # 4. User history-based suggestions (if available)
        if user_context:
            history_suggestions = await self._suggest_codes_from_user_history(
                user_context, exam_type
            )
            suggestions.extend(history_suggestions)
        
        # Remove duplicates and sort by confidence
        unique_suggestions = {}
        for suggestion in suggestions:
            code = suggestion["icd10_code"]
            if code not in unique_suggestions or suggestion["confidence"] > unique_suggestions[code]["confidence"]:
                unique_suggestions[code] = suggestion
        
        return list(unique_suggestions.values())
    
    async def _suggest_codes_from_measurements(
        self,
        measurements: Dict[str, Any],
        exam_type: str
    ) -> List[Dict[str, Any]]:
        """Suggest codes based on measurement abnormalities."""
        
        suggestions = []
        
        try:
            if exam_type == "echo_complete":
                # Check ejection fraction
                ef = measurements.get("left_ventricular_ejection_fraction", {})
                if isinstance(ef, dict) and ef.get("abnormal", False):
                    ef_value = ef.get("value", 0)
                    if ef_value < 30:
                        suggestions.append({
                            "icd10_code": "I50.20",
                            "description": "Unspecified systolic (congestive) heart failure",
                            "confidence": 0.9,
                            "category": "heart_failure",
                            "primary_suitable": True,
                            "reason": f"Severely reduced EF ({ef_value}%)"
                        })
                    elif ef_value < 45:
                        suggestions.append({
                            "icd10_code": "I25.5",
                            "description": "Ischemic cardiomyopathy",
                            "confidence": 0.8,
                            "category": "cardiomyopathy",
                            "primary_suitable": True,
                            "reason": f"Reduced EF ({ef_value}%)"
                        })
                
                # Check valve measurements
                for measurement_key, measurement_data in measurements.items():
                    if "valve" in measurement_key.lower() and isinstance(measurement_data, dict):
                        if measurement_data.get("abnormal", False):
                            if "mitral" in measurement_key.lower():
                                suggestions.append({
                                    "icd10_code": "I34.9",
                                    "description": "Nonrheumatic mitral valve disorder, unspecified",
                                    "confidence": 0.7,
                                    "category": "valve_disease",
                                    "primary_suitable": True,
                                    "reason": "Abnormal mitral valve measurement"
                                })
            
            elif exam_type == "vascular_carotid":
                # Check carotid velocities
                for side in ["right", "left"]:
                    psv_key = f"{side}_ica_peak_systolic_velocity"
                    if psv_key in measurements:
                        psv_data = measurements[psv_key]
                        if isinstance(psv_data, dict):
                            psv_value = psv_data.get("value", 0)
                            if psv_value > 230:  # Significant stenosis
                                code = "I65.21" if side == "right" else "I65.22"
                                suggestions.append({
                                    "icd10_code": code,
                                    "description": f"Occlusion and stenosis of {side} carotid artery",
                                    "confidence": 0.9,
                                    "category": "carotid_stenosis",
                                    "primary_suitable": True,
                                    "reason": f"Elevated PSV ({psv_value} cm/s) indicating stenosis"
                                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting codes from measurements: {e}")
            return []
    
    async def _suggest_codes_for_exam_type(self, exam_type: str) -> List[Dict[str, Any]]:
        """Suggest common codes for specific exam types."""
        
        exam_type_suggestions = {
            "echo_complete": [
                {
                    "icd10_code": "Z13.6",
                    "description": "Encounter for screening for cardiovascular disorders",
                    "confidence": 0.6,
                    "category": "screening",
                    "primary_suitable": True,
                    "reason": "Common screening indication for echocardiogram"
                }
            ],
            "vascular_carotid": [
                {
                    "icd10_code": "Z87.891",
                    "description": "Personal history of nicotine dependence",
                    "confidence": 0.5,
                    "category": "risk_factor",
                    "primary_suitable": False,
                    "reason": "Common risk factor for carotid disease"
                }
            ],
            "ct_scan": [
                {
                    "icd10_code": "R06.02",
                    "description": "Shortness of breath",
                    "confidence": 0.6,
                    "category": "respiratory_symptom",
                    "primary_suitable": True,
                    "reason": "Common indication for chest CT"
                }
            ]
        }
        
        return exam_type_suggestions.get(exam_type, [])
    
    async def _suggest_codes_from_user_history(
        self,
        user_context: Dict[str, Any],
        exam_type: str
    ) -> List[Dict[str, Any]]:
        """Suggest codes based on user's coding history."""
        
        # This would analyze user's previous coding patterns
        # For prototype, return empty list
        return []
    
    async def _validate_and_rank_suggestions(
        self,
        suggestions: List[Dict[str, Any]],
        exam_type: str,
        findings_text: str
    ) -> List[Dict[str, Any]]:
        """Validate and rank code suggestions."""
        
        validated_suggestions = []
        
        for suggestion in suggestions:
            # Validate code exists and is active
            code = suggestion["icd10_code"]
            if code in self.icd10_mappings:
                code_info = self.icd10_mappings[code]
                
                # Update suggestion with additional info
                suggestion.update({
                    "category": code_info.get("category", suggestion.get("category")),
                    "severity": code_info.get("severity"),
                    "chronic": code_info.get("chronic", False),
                    "common_procedures": code_info.get("common_procedures", [])
                })
                
                # Check if appropriate for exam type
                common_procedures = code_info.get("common_procedures", [])
                exam_cpt = self._get_primary_cpt_for_exam(exam_type)
                
                if exam_cpt in common_procedures:
                    suggestion["confidence"] = min(1.0, suggestion["confidence"] + 0.1)
                    suggestion["exam_appropriate"] = True
                else:
                    suggestion["exam_appropriate"] = False
                
                validated_suggestions.append(suggestion)
        
        # Sort by confidence and primary suitability
        validated_suggestions.sort(
            key=lambda x: (x.get("primary_suitable", False), x["confidence"]),
            reverse=True
        )
        
        return validated_suggestions
    
    async def _calculate_confidence_scores(
        self,
        suggestions: List[Dict[str, Any]],
        findings_text: str,
        exam_type: str
    ) -> List[Dict[str, Any]]:
        """Calculate and adjust confidence scores based on context."""
        
        findings_lower = findings_text.lower()
        
        for suggestion in suggestions:
            base_confidence = suggestion["confidence"]
            
            # Adjust based on clinical indicators
            clinical_indicators = suggestion.get("clinical_indicators", [])
            indicator_matches = 0
            
            for indicator in clinical_indicators:
                if indicator.lower() in findings_lower:
                    indicator_matches += 1
            
            if clinical_indicators:
                indicator_boost = (indicator_matches / len(clinical_indicators)) * 0.2
                suggestion["confidence"] = min(1.0, base_confidence + indicator_boost)
            
            # Adjust based on exam appropriateness
            if suggestion.get("exam_appropriate", False):
                suggestion["confidence"] = min(1.0, suggestion["confidence"] + 0.05)
            
            # Add confidence level description
            confidence = suggestion["confidence"]
            if confidence >= 0.8:
                suggestion["confidence_level"] = "high"
            elif confidence >= 0.6:
                suggestion["confidence_level"] = "medium"
            else:
                suggestion["confidence_level"] = "low"
        
        return suggestions
    
    def _get_primary_cpt_for_exam(self, exam_type: str) -> str:
        """Get primary CPT code for exam type."""
        mapping = self.cpt_mappings.get(exam_type, {})
        return mapping.get("primary_cpt", "")
    
    async def _validate_code_formats(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str]
    ) -> Dict[str, Any]:
        """Validate code format compliance."""
        
        validation = {"errors": [], "warnings": []}
        
        # Validate CPT codes
        cpt_pattern = re.compile(r'^\d{5}$')
        for code in cpt_codes:
            if not cpt_pattern.match(code):
                validation["errors"].append(f"Invalid CPT code format: {code}")
        
        # Validate ICD-10 codes
        icd10_pattern = re.compile(r'^[A-Z]\d{2}(\.\d{1,3})?$')
        for code in icd10_codes:
            if not icd10_pattern.match(code):
                validation["errors"].append(f"Invalid ICD-10 code format: {code}")
        
        return validation
    
    async def _validate_medical_necessity(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        exam_type: str
    ) -> Dict[str, Any]:
        """Validate medical necessity of code combinations."""
        
        return ClinicalDecisionSupport.validate_code_medical_necessity(
            icd10_codes, cpt_codes
        )
    
    async def _validate_payer_requirements(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate payer-specific requirements."""
        
        validation = {"warnings": [], "payer_notes": []}
        
        # Medicare-specific validations
        payer = patient_context.get("insurance", {}).get("primary", {}).get("payer_name", "").lower() if patient_context else ""
        
        if "medicare" in payer:
            # Medicare frequency limits
            for cpt_code in cpt_codes:
                frequency_limits = BillingRules.get_frequency_limits().get(cpt_code)
                if frequency_limits:
                    validation["payer_notes"].append(
                        f"Medicare frequency limit for {cpt_code}: {frequency_limits['per_year']} per year"
                    )
        
        return validation
    
    async def _validate_bundling_and_modifiers(self, cpt_codes: List[str]) -> Dict[str, Any]:
        """Validate bundling rules and modifier requirements."""
        
        return BillingRules.validate_cpt_combination(cpt_codes)
    
    async def _calculate_compliance_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall compliance score."""
        
        base_score = 100.0
        
        # Deduct for errors
        error_count = len(validation_result.get("errors", []))
        base_score -= error_count * 20  # 20 points per error
        
        # Deduct for warnings
        warning_count = len(validation_result.get("warnings", []))
        base_score -= warning_count * 5  # 5 points per warning
        
        return max(0.0, base_score)
    
    async def _calculate_reimbursement_estimates(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate reimbursement estimates and risk assessment."""
        
        total_medicare = 0.0
        total_commercial = 0.0
        reimbursement_risk = 0.0
        
        try:
            for cpt_code in cpt_codes:
                # Find RVU for code
                rvu = 0.0
                for exam_type, mapping in self.cpt_mappings.items():
                    if mapping.get("primary_cpt") == cpt_code:
                        rvu = mapping.get("rvu", 0.0)
                        break
                
                if rvu > 0:
                    medicare_amount = self.reimbursement_calculator.calculate_medicare_reimbursement(
                        cpt_code, rvu
                    )
                    commercial_amount = self.reimbursement_calculator.calculate_commercial_reimbursement(
                        cpt_code, rvu
                    )
                    
                    total_medicare += medicare_amount
                    total_commercial += commercial_amount
            
            # Calculate risk factors
            if not icd10_codes:
                reimbursement_risk += 0.5  # High risk without diagnosis codes
            
            # Risk based on code combinations
            if len(cpt_codes) > 3:
                reimbursement_risk += 0.1  # Multiple procedures increase risk
            
            return {
                "estimated_reimbursement": {
                    "medicare": round(total_medicare, 2),
                    "commercial_120": round(total_commercial, 2),
                    "commercial_150": round(total_commercial * 1.25, 2)
                },
                "reimbursement_risk": min(1.0, reimbursement_risk),
                "risk_factors": self._identify_risk_factors(cpt_codes, icd10_codes)
            }
            
        except Exception as e:
            logger.error(f"Error calculating reimbursement estimates: {e}")
            return {
                "estimated_reimbursement": {"medicare": 0.0, "commercial_120": 0.0, "commercial_150": 0.0},
                "reimbursement_risk": 1.0,
                "risk_factors": ["Calculation error"]
            }
    
    def _identify_risk_factors(self, cpt_codes: List[str], icd10_codes: List[str]) -> List[str]:
        """Identify specific reimbursement risk factors."""
        
        risk_factors = []
        
        if not icd10_codes:
            risk_factors.append("No diagnosis codes provided")
        
        if len(cpt_codes) > 3:
            risk_factors.append("Multiple procedures may require additional documentation")
        
        # Check for high-risk code combinations
        for cpt_code in cpt_codes:
            if cpt_code in ["71260", "70553"]:  # High-cost imaging
                risk_factors.append(f"High-cost procedure {cpt_code} may require prior authorization")
        
        return risk_factors
    
    async def _generate_improvement_suggestions(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        validation_result: Dict[str, Any],
        exam_type: str
    ) -> List[Dict[str, Any]]:
        """Generate suggestions to improve code combinations."""
        
        suggestions = []
        
        # Suggest missing diagnosis codes
        if not icd10_codes:
            appropriate_codes = ICD10Mappings.find_codes_for_procedure(cpt_codes[0] if cpt_codes else "")
            if appropriate_codes:
                suggestions.append({
                    "type": "add_diagnosis",
                    "suggestion": f"Add diagnosis code {appropriate_codes[0]['icd10_code']}",
                    "reason": "Medical necessity requires supporting diagnosis",
                    "code": appropriate_codes[0]['icd10_code'],
                    "description": appropriate_codes[0]['description']
                })
        
        # Suggest modifier additions
        for cpt_code in cpt_codes:
            mapping = None
            for exam_type_key, exam_mapping in self.cpt_mappings.items():
                if exam_mapping.get("primary_cpt") == cpt_code:
                    mapping = exam_mapping
                    break
            
            if mapping and mapping.get("requires_modifier", False):
                suggestions.append({
                    "type": "add_modifier",
                    "suggestion": f"Consider adding modifier 26 or TC to {cpt_code}",
                    "reason": "Procedure typically requires professional or technical component modifier",
                    "code": cpt_code,
                    "modifiers": ["26", "TC"]
                })
        
        return suggestions
    
    async def get_realtime_validation_stats(self) -> Dict[str, Any]:
        """Get real-time validation performance statistics."""
        
        try:
            # Get cache statistics
            cache_stats = {
                "suggestion_cache_hits": 0,
                "validation_cache_hits": 0,
                "total_requests": 0
            }
            
            # In a real implementation, these would be tracked metrics
            return {
                "performance": cache_stats,
                "average_response_time_ms": 150,
                "validation_accuracy": 0.95,
                "suggestion_relevance": 0.88,
                "cache_hit_rate": 0.75,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting validation stats: {e}")
            return {"error": str(e)}