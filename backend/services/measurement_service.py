"""
Measurement service for managing structured medical measurements.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class MeasurementService:
    """Service for managing medical measurements and calculations."""
    
    def __init__(self):
        self.measurement_templates = self._load_measurement_templates()
        self.normal_ranges = self._load_normal_ranges()
    
    def _load_measurement_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load measurement templates for different exam types."""
        return {
            "echo_complete": {
                "left_ventricular_ejection_fraction": {
                    "name": "Left Ventricular Ejection Fraction",
                    "unit": "%",
                    "normal_range": "55-70%",
                    "category": "systolic_function",
                    "required": True
                },
                "left_ventricular_end_diastolic_dimension": {
                    "name": "LV End Diastolic Dimension",
                    "unit": "cm",
                    "normal_range": "3.9-5.3 cm",
                    "category": "dimensions",
                    "required": True
                },
                "interventricular_septal_thickness": {
                    "name": "Interventricular Septal Thickness",
                    "unit": "cm",
                    "normal_range": "0.6-1.0 cm",
                    "category": "dimensions",
                    "required": True
                },
                "left_atrial_dimension": {
                    "name": "Left Atrial Dimension",
                    "unit": "cm",
                    "normal_range": "2.7-4.0 cm",
                    "category": "dimensions",
                    "required": True
                },
                "aortic_root_dimension": {
                    "name": "Aortic Root Dimension",
                    "unit": "cm",
                    "normal_range": "2.0-3.7 cm",
                    "category": "dimensions",
                    "required": False
                },
                "mitral_valve_e_velocity": {
                    "name": "Mitral E Velocity",
                    "unit": "m/s",
                    "normal_range": "0.6-1.3 m/s",
                    "category": "diastolic_function",
                    "required": False
                },
                "mitral_valve_a_velocity": {
                    "name": "Mitral A Velocity",
                    "unit": "m/s",
                    "normal_range": "0.4-1.0 m/s",
                    "category": "diastolic_function",
                    "required": False
                }
            },
            "vascular_carotid": {
                "right_ica_peak_systolic_velocity": {
                    "name": "Right ICA Peak Systolic Velocity",
                    "unit": "cm/s",
                    "normal_range": "<125 cm/s",
                    "category": "velocities",
                    "required": True
                },
                "left_ica_peak_systolic_velocity": {
                    "name": "Left ICA Peak Systolic Velocity",
                    "unit": "cm/s",
                    "normal_range": "<125 cm/s",
                    "category": "velocities",
                    "required": True
                },
                "right_ica_end_diastolic_velocity": {
                    "name": "Right ICA End Diastolic Velocity",
                    "unit": "cm/s",
                    "normal_range": "<40 cm/s",
                    "category": "velocities",
                    "required": True
                },
                "left_ica_end_diastolic_velocity": {
                    "name": "Left ICA End Diastolic Velocity",
                    "unit": "cm/s",
                    "normal_range": "<40 cm/s",
                    "category": "velocities",
                    "required": True
                },
                "right_ica_stenosis_percentage": {
                    "name": "Right ICA Stenosis Percentage",
                    "unit": "%",
                    "normal_range": "<50%",
                    "category": "stenosis",
                    "required": False
                },
                "left_ica_stenosis_percentage": {
                    "name": "Left ICA Stenosis Percentage",
                    "unit": "%",
                    "normal_range": "<50%",
                    "category": "stenosis",
                    "required": False
                }
            },
            "ct_scan": {
                "cardiac_thoracic_ratio": {
                    "name": "Cardiac Thoracic Ratio",
                    "unit": "ratio",
                    "normal_range": "<0.50",
                    "category": "cardiac",
                    "required": False
                },
                "aortic_diameter": {
                    "name": "Aortic Diameter",
                    "unit": "cm",
                    "normal_range": "2.5-3.5 cm",
                    "category": "vascular",
                    "required": False
                }
            }
        }
    
    def _load_normal_ranges(self) -> Dict[str, Dict[str, Any]]:
        """Load normal ranges with age and gender considerations."""
        return {
            "left_ventricular_ejection_fraction": {
                "normal": {"min": 55, "max": 70},
                "mild_dysfunction": {"min": 45, "max": 54},
                "moderate_dysfunction": {"min": 30, "max": 44},
                "severe_dysfunction": {"min": 0, "max": 29}
            },
            "ica_peak_systolic_velocity": {
                "normal": {"min": 0, "max": 125},
                "mild_stenosis": {"min": 125, "max": 230},
                "moderate_stenosis": {"min": 230, "max": 400},
                "severe_stenosis": {"min": 400, "max": 1000}
            }
        }
    
    def get_measurement_template(self, exam_type: str) -> Dict[str, Any]:
        """Get measurement template for exam type."""
        return self.measurement_templates.get(exam_type, {})
    
    def validate_measurements(
        self, 
        measurements: Dict[str, Any], 
        exam_type: str
    ) -> Dict[str, Any]:
        """Validate measurements against templates and normal ranges."""
        
        template = self.get_measurement_template(exam_type)
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "validated_measurements": {},
            "abnormal_findings": []
        }
        
        try:
            for measurement_key, measurement_data in measurements.items():
                if measurement_key not in template:
                    validation_result["warnings"].append(
                        f"Unknown measurement: {measurement_key}"
                    )
                    continue
                
                template_info = template[measurement_key]
                validated_measurement = self._validate_single_measurement(
                    measurement_key, measurement_data, template_info
                )
                
                validation_result["validated_measurements"][measurement_key] = validated_measurement
                
                # Check if abnormal
                if validated_measurement.get("abnormal", False):
                    validation_result["abnormal_findings"].append({
                        "measurement": measurement_key,
                        "value": validated_measurement["value"],
                        "normal_range": validated_measurement["normal_range"],
                        "severity": validated_measurement.get("severity", "unknown")
                    })
            
            # Check for required measurements
            required_measurements = [
                key for key, info in template.items() 
                if info.get("required", False)
            ]
            
            missing_required = [
                key for key in required_measurements 
                if key not in measurements
            ]
            
            if missing_required:
                validation_result["errors"].extend([
                    f"Missing required measurement: {key}" 
                    for key in missing_required
                ])
                validation_result["valid"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating measurements: {e}")
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            return validation_result
    
    def _validate_single_measurement(
        self, 
        key: str, 
        measurement: Dict[str, Any], 
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single measurement."""
        
        validated = {
            "value": measurement.get("value"),
            "unit": measurement.get("unit", template.get("unit")),
            "normal_range": template.get("normal_range"),
            "category": template.get("category"),
            "abnormal": False,
            "severity": None
        }
        
        try:
            value = float(measurement.get("value", 0))
            validated["value"] = value
            
            # Check against normal ranges
            if key in self.normal_ranges:
                ranges = self.normal_ranges[key]
                
                if "normal" in ranges:
                    normal_range = ranges["normal"]
                    if not (normal_range["min"] <= value <= normal_range["max"]):
                        validated["abnormal"] = True
                        
                        # Determine severity
                        for severity, range_info in ranges.items():
                            if severity != "normal":
                                if range_info["min"] <= value <= range_info["max"]:
                                    validated["severity"] = severity
                                    break
            
            # Additional validation based on measurement type
            if "ejection_fraction" in key:
                if value < 30:
                    validated["severity"] = "severe_dysfunction"
                elif value < 45:
                    validated["severity"] = "moderate_dysfunction"
                elif value < 55:
                    validated["severity"] = "mild_dysfunction"
            
            return validated
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error validating measurement {key}: {e}")
            validated["error"] = str(e)
            return validated
    
    def calculate_derived_measurements(
        self, 
        measurements: Dict[str, Any], 
        exam_type: str
    ) -> Dict[str, Any]:
        """Calculate derived measurements from primary measurements."""
        
        derived = {}
        
        try:
            if exam_type == "echo_complete":
                # Calculate E/A ratio if both E and A velocities are present
                e_vel = measurements.get("mitral_valve_e_velocity", {}).get("value")
                a_vel = measurements.get("mitral_valve_a_velocity", {}).get("value")
                
                if e_vel and a_vel and float(a_vel) > 0:
                    e_a_ratio = float(e_vel) / float(a_vel)
                    derived["mitral_e_a_ratio"] = {
                        "value": round(e_a_ratio, 2),
                        "unit": "ratio",
                        "normal_range": "0.8-2.0",
                        "abnormal": not (0.8 <= e_a_ratio <= 2.0),
                        "calculated": True
                    }
                
                # Calculate left ventricular mass index if dimensions available
                lvedd = measurements.get("left_ventricular_end_diastolic_dimension", {}).get("value")
                ivs = measurements.get("interventricular_septal_thickness", {}).get("value")
                
                if lvedd and ivs:
                    # Simplified LV mass calculation (Devereux formula approximation)
                    lv_mass = 0.8 * (1.04 * ((float(lvedd) + float(ivs))**3 - float(lvedd)**3)) + 0.6
                    derived["left_ventricular_mass"] = {
                        "value": round(lv_mass, 1),
                        "unit": "g",
                        "normal_range": "67-162 g (female), 88-224 g (male)",
                        "calculated": True
                    }
            
            elif exam_type == "vascular_carotid":
                # Calculate stenosis ratios
                right_psv = measurements.get("right_ica_peak_systolic_velocity", {}).get("value")
                left_psv = measurements.get("left_ica_peak_systolic_velocity", {}).get("value")
                
                if right_psv:
                    # Estimate stenosis percentage based on PSV
                    stenosis_pct = self._estimate_carotid_stenosis(float(right_psv))
                    derived["right_ica_estimated_stenosis"] = {
                        "value": stenosis_pct,
                        "unit": "%",
                        "normal_range": "<50%",
                        "abnormal": stenosis_pct >= 50,
                        "calculated": True
                    }
                
                if left_psv:
                    stenosis_pct = self._estimate_carotid_stenosis(float(left_psv))
                    derived["left_ica_estimated_stenosis"] = {
                        "value": stenosis_pct,
                        "unit": "%",
                        "normal_range": "<50%",
                        "abnormal": stenosis_pct >= 50,
                        "calculated": True
                    }
            
            return derived
            
        except Exception as e:
            logger.error(f"Error calculating derived measurements: {e}")
            return {}
    
    def _estimate_carotid_stenosis(self, psv: float) -> int:
        """Estimate carotid stenosis percentage from peak systolic velocity."""
        if psv < 125:
            return 0
        elif psv < 230:
            return int(50 + (psv - 125) / (230 - 125) * 20)  # 50-70%
        elif psv < 400:
            return int(70 + (psv - 230) / (400 - 230) * 20)  # 70-90%
        else:
            return min(99, int(90 + (psv - 400) / 100 * 9))  # 90-99%
    
    def generate_measurement_summary(
        self, 
        measurements: Dict[str, Any], 
        exam_type: str
    ) -> Dict[str, Any]:
        """Generate a summary of measurements for reporting."""
        
        validation = self.validate_measurements(measurements, exam_type)
        derived = self.calculate_derived_measurements(measurements, exam_type)
        
        # Combine all measurements
        all_measurements = {**validation["validated_measurements"], **derived}
        
        # Categorize measurements
        categories = {}
        abnormal_count = 0
        
        for key, measurement in all_measurements.items():
            category = measurement.get("category", "other")
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                "key": key,
                "name": measurement.get("name", key.replace("_", " ").title()),
                "value": measurement["value"],
                "unit": measurement["unit"],
                "normal_range": measurement["normal_range"],
                "abnormal": measurement.get("abnormal", False),
                "severity": measurement.get("severity"),
                "calculated": measurement.get("calculated", False)
            })
            
            if measurement.get("abnormal", False):
                abnormal_count += 1
        
        return {
            "exam_type": exam_type,
            "total_measurements": len(all_measurements),
            "abnormal_measurements": abnormal_count,
            "categories": categories,
            "validation": validation,
            "abnormal_findings": validation["abnormal_findings"],
            "summary_text": self._generate_measurement_text(categories, exam_type),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_measurement_text(
        self, 
        categories: Dict[str, List[Dict[str, Any]]], 
        exam_type: str
    ) -> str:
        """Generate text summary of measurements."""
        
        text_parts = []
        
        for category, measurements in categories.items():
            category_title = category.replace("_", " ").title()
            text_parts.append(f"\n{category_title}:")
            
            for measurement in measurements:
                abnormal_flag = " (ABNORMAL)" if measurement["abnormal"] else ""
                calculated_flag = " (calculated)" if measurement["calculated"] else ""
                
                text_parts.append(
                    f"- {measurement['name']}: {measurement['value']} {measurement['unit']}"
                    f" (normal: {measurement['normal_range']}){abnormal_flag}{calculated_flag}"
                )
        
        return "\n".join(text_parts)
    
    def get_measurement_recommendations(
        self, 
        measurements: Dict[str, Any], 
        exam_type: str
    ) -> List[str]:
        """Generate recommendations based on measurements."""
        
        recommendations = []
        validation = self.validate_measurements(measurements, exam_type)
        
        try:
            abnormal_findings = validation.get("abnormal_findings", [])
            
            for finding in abnormal_findings:
                measurement = finding["measurement"]
                severity = finding.get("severity")
                
                if "ejection_fraction" in measurement:
                    if severity == "severe_dysfunction":
                        recommendations.append(
                            "Severe LV systolic dysfunction identified. "
                            "Consider cardiology consultation and heart failure management."
                        )
                    elif severity == "moderate_dysfunction":
                        recommendations.append(
                            "Moderate LV systolic dysfunction. "
                            "Consider ACE inhibitor therapy and cardiology follow-up."
                        )
                
                elif "stenosis" in measurement and exam_type == "vascular_carotid":
                    if finding["value"] >= 70:
                        recommendations.append(
                            "Significant carotid stenosis detected. "
                            "Consider vascular surgery consultation for intervention evaluation."
                        )
                    elif finding["value"] >= 50:
                        recommendations.append(
                            "Moderate carotid stenosis. "
                            "Optimize medical management and consider serial monitoring."
                        )
            
            # General recommendations
            if not abnormal_findings:
                recommendations.append("Normal measurements. Continue routine care as appropriate.")
            else:
                recommendations.append("Clinical correlation recommended for abnormal findings.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Clinical correlation recommended."]