"""
Billing service for CPT/ICD-10 code mapping and superbill generation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

# Fix the imports to use relative imports
try:
    from ..models import Report, Superbill, BillingCode
except ImportError:
    from backend.models import Report, Superbill, BillingCode

# Import directly from schemas.py file
import importlib.util
import os
schemas_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas.py')
spec = importlib.util.spec_from_file_location("schemas_module", schemas_path)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)

SuperbillResponse = schemas_module.SuperbillResponse
ServiceLine = schemas_module.ServiceLine
DiagnosisCode = schemas_module.DiagnosisCode
PatientInfo = schemas_module.PatientInfo

try:
    from .audit_service import AuditService
    from ..config import settings
except ImportError:
    from backend.services.audit_service import AuditService
    from backend.config import settings

logger = logging.getLogger(__name__)

class BillingService:
    """Service for billing code mapping and superbill generation."""
    
    def __init__(self):
        self.audit_service = AuditService()
        self.cpt_mappings = self._load_cpt_mappings()
        self.icd10_mappings = self._load_icd10_mappings()
        self.billing_rules = self._load_billing_rules()
    
    def _load_cpt_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load CPT code mappings for different exam types."""
        return {
            "echo_complete": {
                "primary_cpt": "93306",
                "description": "Echocardiography, transthoracic, real-time with image documentation (2D), includes M-mode recording, when performed, complete",
                "base_charge": 450.00,
                "rvu": 2.89,
                "modifiers": [],
                "additional_codes": {
                    "93320": {
                        "description": "Doppler echocardiography, pulsed wave and/or continuous wave with spectral display",
                        "base_charge": 125.00,
                        "condition": "doppler_performed"
                    },
                    "93325": {
                        "description": "Doppler echocardiography color flow velocity mapping",
                        "base_charge": 150.00,
                        "condition": "color_doppler_performed"
                    }
                },
                "bilateral_applicable": False,
                "requires_modifier": False
            },
            "vascular_carotid": {
                "primary_cpt": "93880",
                "description": "Duplex scan of extracranial arteries; complete bilateral study",
                "base_charge": 380.00,
                "rvu": 2.45,
                "modifiers": ["26", "TC"],  # Professional/Technical components
                "additional_codes": {
                    "93882": {
                        "description": "Duplex scan of extracranial arteries; unilateral or limited study",
                        "base_charge": 280.00,
                        "condition": "unilateral_only"
                    }
                },
                "bilateral_applicable": True,
                "requires_modifier": True
            },
            "ct_scan": {
                "primary_cpt": "71260",
                "description": "Computed tomography, thorax; with contrast material(s)",
                "base_charge": 650.00,
                "rvu": 4.12,
                "modifiers": ["26", "TC"],
                "additional_codes": {
                    "71250": {
                        "description": "Computed tomography, thorax; without contrast material",
                        "base_charge": 520.00,
                        "condition": "no_contrast"
                    }
                },
                "bilateral_applicable": False,
                "requires_modifier": True
            },
            "mri_scan": {
                "primary_cpt": "70553",
                "description": "Magnetic resonance (eg, proton) imaging, brain (including brain stem); without contrast material, followed by contrast material(s) and further sequences",
                "base_charge": 1200.00,
                "rvu": 7.85,
                "modifiers": ["26", "TC"],
                "additional_codes": {},
                "bilateral_applicable": False,
                "requires_modifier": True
            },
            "xray": {
                "primary_cpt": "71020",
                "description": "Radiologic examination, chest, 2 views, frontal and lateral",
                "base_charge": 85.00,
                "rvu": 0.65,
                "modifiers": ["26", "TC"],
                "additional_codes": {
                    "71010": {
                        "description": "Radiologic examination, chest; single view, frontal",
                        "base_charge": 65.00,
                        "condition": "single_view"
                    }
                },
                "bilateral_applicable": False,
                "requires_modifier": False
            }
        }
    
    def _load_icd10_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load ICD-10 diagnosis code mappings."""
        return {
            "normal_findings": {
                "Z51.89": {
                    "description": "Other specified aftercare",
                    "category": "screening",
                    "primary_suitable": True
                },
                "Z87.891": {
                    "description": "Personal history of nicotine dependence",
                    "category": "history",
                    "primary_suitable": False
                },
                "Z12.31": {
                    "description": "Encounter for screening mammogram for malignant neoplasm of breast",
                    "category": "screening",
                    "primary_suitable": True
                }
            },
            "cardiac_pathology": {
                "heart_failure": {
                    "I50.9": {
                        "description": "Heart failure, unspecified",
                        "category": "cardiac",
                        "severity": "unspecified",
                        "primary_suitable": True
                    },
                    "I25.5": {
                        "description": "Ischemic cardiomyopathy",
                        "category": "cardiac",
                        "severity": "chronic",
                        "primary_suitable": True
                    }
                },
                "valve_disease": {
                    "I34.9": {
                        "description": "Nonrheumatic mitral valve disorder, unspecified",
                        "category": "cardiac",
                        "severity": "unspecified",
                        "primary_suitable": True
                    },
                    "I35.9": {
                        "description": "Nonrheumatic aortic valve disorder, unspecified",
                        "category": "cardiac",
                        "severity": "unspecified",
                        "primary_suitable": True
                    },
                    "I36.9": {
                        "description": "Nonrheumatic tricuspid valve disorder, unspecified",
                        "category": "cardiac",
                        "severity": "unspecified",
                        "primary_suitable": True
                    }
                },
                "cardiomyopathy": {
                    "I42.9": {
                        "description": "Cardiomyopathy, unspecified",
                        "category": "cardiac",
                        "severity": "unspecified",
                        "primary_suitable": True
                    }
                }
            },
            "vascular_pathology": {
                "carotid_stenosis": {
                    "I65.21": {
                        "description": "Occlusion and stenosis of right carotid artery",
                        "category": "vascular",
                        "severity": "significant",
                        "primary_suitable": True
                    },
                    "I65.22": {
                        "description": "Occlusion and stenosis of left carotid artery",
                        "category": "vascular",
                        "severity": "significant",
                        "primary_suitable": True
                    },
                    "I65.23": {
                        "description": "Occlusion and stenosis of bilateral carotid arteries",
                        "category": "vascular",
                        "severity": "significant",
                        "primary_suitable": True
                    }
                },
                "atherosclerosis": {
                    "I70.90": {
                        "description": "Unspecified atherosclerosis",
                        "category": "vascular",
                        "severity": "chronic",
                        "primary_suitable": True
                    },
                    "I25.10": {
                        "description": "Atherosclerotic heart disease of native coronary artery without angina pectoris",
                        "category": "cardiac",
                        "severity": "chronic",
                        "primary_suitable": True
                    }
                },
                "occlusion": {
                    "I65.01": {
                        "description": "Occlusion and stenosis of right vertebral artery",
                        "category": "vascular",
                        "severity": "severe",
                        "primary_suitable": True
                    },
                    "I65.02": {
                        "description": "Occlusion and stenosis of left vertebral artery",
                        "category": "vascular",
                        "severity": "severe",
                        "primary_suitable": True
                    }
                }
            },
            "pulmonary_pathology": {
                "J44.1": {
                    "description": "Chronic obstructive pulmonary disease with acute exacerbation",
                    "category": "pulmonary",
                    "severity": "acute",
                    "primary_suitable": True
                },
                "J18.9": {
                    "description": "Pneumonia, unspecified organism",
                    "category": "pulmonary",
                    "severity": "acute",
                    "primary_suitable": True
                }
            }
        }
    
    def _load_billing_rules(self) -> Dict[str, Any]:
        """Load billing validation rules and payer requirements."""
        return {
            "cpt_icd10_combinations": {
                "93306": {  # Echo complete
                    "required_categories": ["cardiac", "screening"],
                    "excluded_codes": [],
                    "max_diagnoses": 4,
                    "requires_primary": True
                },
                "93880": {  # Carotid duplex
                    "required_categories": ["vascular", "screening"],
                    "excluded_codes": [],
                    "max_diagnoses": 3,
                    "requires_primary": True
                },
                "71260": {  # CT chest
                    "required_categories": ["pulmonary", "cardiac", "screening"],
                    "excluded_codes": [],
                    "max_diagnoses": 5,
                    "requires_primary": True
                }
            },
            "modifier_rules": {
                "26": {  # Professional component
                    "description": "Professional component",
                    "multiplier": 0.4,
                    "mutually_exclusive": ["TC"]
                },
                "TC": {  # Technical component
                    "description": "Technical component",
                    "multiplier": 0.6,
                    "mutually_exclusive": ["26"]
                },
                "50": {  # Bilateral procedure
                    "description": "Bilateral procedure",
                    "multiplier": 1.5,
                    "applicable_cpts": ["93880"]
                }
            },
            "reimbursement_rates": {
                "medicare": {
                    "conversion_factor": 34.61,  # 2024 Medicare conversion factor
                    "geographic_adjustment": 1.0
                },
                "commercial": {
                    "medicare_percentage": 120,  # 120% of Medicare rates
                    "negotiated_rates": {}
                }
            }
        }
    
    async def generate_superbill(
        self,
        db: Session,
        report_id: str,
        user_id: Optional[str] = None
    ) -> SuperbillResponse:
        """Generate a complete superbill from a finalized report."""
        
        try:
            # Get the report
            report = db.query(Report).filter(Report.report_id == report_id).first()
            if not report:
                raise ValueError(f"Report not found: {report_id}")
            
            if report.status != "final":
                raise ValueError("Report must be finalized before generating superbill")
            
            logger.info(f"Generating superbill for report {report_id}")
            
            # Generate service lines from CPT codes
            services = await self._generate_service_lines(
                report.exam_type, 
                report.cpt_codes or [],
                report.measurements or {}
            )
            
            # Generate diagnosis codes
            diagnoses = await self._generate_diagnosis_lines(
                report.diagnosis_codes or [],
                report.findings or "",
                report.exam_type
            )
            
            # Calculate total charges
            total_charges = sum(service["charge"] for service in services)
            
            # Generate patient info (mock data for prototype)
            patient_info = self._generate_patient_info(report.study_uid)
            
            # Generate 837P data
            x12_837p_data = await self._generate_837p_data(
                patient_info, services, diagnoses, report
            )
            
            # Create superbill record
            superbill = Superbill(
                report_id=report.report_id,
                patient_info=patient_info,
                services=services,
                diagnoses=diagnoses,
                total_charges=total_charges,
                x12_837p_data=x12_837p_data,
                provider_npi=settings.default_provider_npi,
                facility_name=settings.default_facility_name,
                facility_address=settings.default_facility_address,
                validated=True,
                validation_errors=[]
            )
            
            db.add(superbill)
            db.commit()
            db.refresh(superbill)
            
            # Log superbill generation
            await self.audit_service.log_billing_action(
                db=db,
                superbill_id=str(superbill.superbill_id),
                action="GENERATED",
                report_id=report_id,
                user_id=user_id,
                billing_data={
                    "total_charges": total_charges,
                    "service_count": len(services),
                    "diagnosis_count": len(diagnoses)
                }
            )
            
            logger.info(f"Superbill {superbill.superbill_id} generated successfully")
            
            # Convert to response format
            return self._convert_to_superbill_response(superbill)
            
        except Exception as e:
            logger.error(f"Error generating superbill: {e}")
            raise
    
    async def _generate_service_lines(
        self,
        exam_type: str,
        cpt_codes: List[str],
        measurements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate service lines from CPT codes and exam type."""
        
        services = []
        
        try:
            # Get CPT mapping for exam type
            cpt_mapping = self.cpt_mappings.get(exam_type, {})
            
            if not cpt_mapping:
                # Fallback to generic mapping
                logger.warning(f"No CPT mapping found for exam type: {exam_type}")
                return [{
                    "cpt_code": "76000",
                    "description": "Diagnostic imaging procedure",
                    "units": 1,
                    "charge": 200.00,
                    "modifiers": []
                }]
            
            # Add primary CPT code
            primary_service = {
                "cpt_code": cpt_mapping["primary_cpt"],
                "description": cpt_mapping["description"],
                "units": 1,
                "charge": cpt_mapping["base_charge"],
                "modifiers": []
            }
            
            # Add modifiers if required
            if cpt_mapping.get("requires_modifier", False):
                # Default to professional component for prototype
                primary_service["modifiers"] = ["26"]
                primary_service["charge"] *= 0.4  # Professional component rate
            
            services.append(primary_service)
            
            # Add additional codes based on conditions
            additional_codes = cpt_mapping.get("additional_codes", {})
            for code, code_info in additional_codes.items():
                condition = code_info.get("condition")
                
                # Simple condition checking (in real implementation, this would be more sophisticated)
                should_include = False
                
                if condition == "doppler_performed" and "doppler" in str(measurements).lower():
                    should_include = True
                elif condition == "color_doppler_performed" and "color" in str(measurements).lower():
                    should_include = True
                elif condition == "unilateral_only" and exam_type == "vascular_carotid":
                    # Check if only one side has measurements
                    left_measurements = any("left" in key for key in measurements.keys())
                    right_measurements = any("right" in key for key in measurements.keys())
                    should_include = left_measurements != right_measurements
                
                if should_include:
                    additional_service = {
                        "cpt_code": code,
                        "description": code_info["description"],
                        "units": 1,
                        "charge": code_info["base_charge"],
                        "modifiers": []
                    }
                    services.append(additional_service)
            
            return services
            
        except Exception as e:
            logger.error(f"Error generating service lines: {e}")
            return []
    
    async def _generate_diagnosis_lines(
        self,
        diagnosis_codes: List[str],
        findings: str,
        exam_type: str
    ) -> List[Dict[str, Any]]:
        """Generate diagnosis lines from ICD-10 codes and findings."""
        
        diagnoses = []
        
        try:
            if not diagnosis_codes:
                # Default to normal findings
                diagnosis_codes = ["Z51.89"]
            
            # Process each diagnosis code
            for i, code in enumerate(diagnosis_codes):
                diagnosis_info = self._find_icd10_info(code)
                
                diagnosis = {
                    "icd10_code": code,
                    "description": diagnosis_info.get("description", f"Diagnosis code {code}"),
                    "primary": i == 0  # First code is primary
                }
                
                diagnoses.append(diagnosis)
            
            return diagnoses
            
        except Exception as e:
            logger.error(f"Error generating diagnosis lines: {e}")
            return [{
                "icd10_code": "Z51.89",
                "description": "Other specified aftercare",
                "primary": True
            }]
    
    def _find_icd10_info(self, code: str) -> Dict[str, Any]:
        """Find ICD-10 code information in mappings."""
        
        for category, subcategories in self.icd10_mappings.items():
            if isinstance(subcategories, dict):
                for subcategory, codes in subcategories.items():
                    if isinstance(codes, dict):
                        if code in codes:
                            return codes[code]
                        # Check nested structure
                        for nested_codes in codes.values():
                            if isinstance(nested_codes, dict) and code in nested_codes:
                                return nested_codes[code]
                    elif code == subcategory:
                        return codes
        
        return {"description": f"Diagnosis code {code}", "category": "unknown"}
    
    def _generate_patient_info(self, study_uid: str) -> Dict[str, Any]:
        """Generate mock patient information for prototype."""
        
        # In real implementation, this would come from EHR integration
        return {
            "patient_id": f"PAT{study_uid[-6:]}",
            "name": "Test Patient",
            "dob": "1980-01-01",
            "gender": "M",
            "address": "123 Main St, Healthcare City, HC 12345",
            "insurance": {
                "primary": {
                    "payer_name": "Medicare",
                    "policy_number": "123456789A",
                    "group_number": "001"
                }
            }
        }
    
    async def _generate_837p_data(
        self,
        patient_info: Dict[str, Any],
        services: List[Dict[str, Any]],
        diagnoses: List[Dict[str, Any]],
        report: Report
    ) -> Dict[str, Any]:
        """Generate 837P-compatible JSON data."""
        
        return {
            "transaction_set": "837P",
            "version": "005010X222A1",
            "submitter": {
                "name": settings.default_facility_name,
                "npi": settings.default_provider_npi,
                "contact": {
                    "name": "Billing Department",
                    "phone": "555-123-4567",
                    "email": "billing@kiromini.com"
                }
            },
            "receiver": {
                "name": patient_info["insurance"]["primary"]["payer_name"],
                "id": "MEDICARE"
            },
            "claim": {
                "claim_id": str(report.report_id),
                "patient": {
                    "id": patient_info["patient_id"],
                    "name": patient_info["name"],
                    "dob": patient_info["dob"],
                    "gender": patient_info["gender"],
                    "address": patient_info["address"]
                },
                "subscriber": {
                    "id": patient_info["insurance"]["primary"]["policy_number"],
                    "group": patient_info["insurance"]["primary"]["group_number"]
                },
                "provider": {
                    "npi": settings.default_provider_npi,
                    "name": settings.default_facility_name,
                    "address": settings.default_facility_address
                },
                "service_date": datetime.utcnow().strftime("%Y%m%d"),
                "diagnosis_codes": [d["icd10_code"] for d in diagnoses],
                "service_lines": [
                    {
                        "line_number": i + 1,
                        "procedure_code": service["cpt_code"],
                        "modifiers": service.get("modifiers", []),
                        "units": service["units"],
                        "charges": service["charge"],
                        "diagnosis_pointers": [1]  # Point to primary diagnosis
                    }
                    for i, service in enumerate(services)
                ],
                "total_charges": sum(s["charge"] for s in services)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def validate_code_combinations(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str]
    ) -> Dict[str, Any]:
        """Validate CPT-ICD-10 code combinations for compliance."""
        
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "estimated_reimbursement": 0.0,
            "denial_risk_score": 0.0
        }
        
        try:
            # Validate each CPT code
            for cpt_code in cpt_codes:
                cpt_rules = self.billing_rules["cpt_icd10_combinations"].get(cpt_code)
                
                if not cpt_rules:
                    validation["warnings"].append(f"No validation rules found for CPT {cpt_code}")
                    continue
                
                # Check required categories
                required_categories = cpt_rules.get("required_categories", [])
                if required_categories:
                    found_categories = set()
                    
                    for icd10_code in icd10_codes:
                        icd10_info = self._find_icd10_info(icd10_code)
                        category = icd10_info.get("category", "unknown")
                        found_categories.add(category)
                    
                    missing_categories = set(required_categories) - found_categories
                    if missing_categories:
                        validation["errors"].append(
                            f"CPT {cpt_code} requires diagnosis from categories: {', '.join(missing_categories)}"
                        )
                        validation["valid"] = False
                
                # Check maximum diagnoses
                max_diagnoses = cpt_rules.get("max_diagnoses", 10)
                if len(icd10_codes) > max_diagnoses:
                    validation["warnings"].append(
                        f"CPT {cpt_code} supports maximum {max_diagnoses} diagnoses, {len(icd10_codes)} provided"
                    )
                
                # Check for primary diagnosis
                if cpt_rules.get("requires_primary", False) and not icd10_codes:
                    validation["errors"].append(f"CPT {cpt_code} requires at least one primary diagnosis")
                    validation["valid"] = False
            
            # Calculate estimated reimbursement
            validation["estimated_reimbursement"] = await self._calculate_estimated_reimbursement(
                cpt_codes, icd10_codes
            )
            
            # Calculate denial risk score
            validation["denial_risk_score"] = self._calculate_denial_risk(
                cpt_codes, icd10_codes, validation["errors"], validation["warnings"]
            )
            
            # Generate suggestions
            if validation["errors"] or validation["warnings"]:
                validation["suggestions"] = await self._generate_coding_suggestions(
                    cpt_codes, icd10_codes, validation["errors"]
                )
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating code combinations: {e}")
            validation["valid"] = False
            validation["errors"].append(f"Validation error: {str(e)}")
            return validation
    
    async def _calculate_estimated_reimbursement(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str]
    ) -> float:
        """Calculate estimated reimbursement for code combination."""
        
        total_reimbursement = 0.0
        
        try:
            medicare_cf = self.billing_rules["reimbursement_rates"]["medicare"]["conversion_factor"]
            
            for cpt_code in cpt_codes:
                # Find RVU for CPT code
                rvu = 0.0
                for exam_type, mapping in self.cpt_mappings.items():
                    if mapping.get("primary_cpt") == cpt_code:
                        rvu = mapping.get("rvu", 0.0)
                        break
                
                if rvu > 0:
                    reimbursement = rvu * medicare_cf
                    total_reimbursement += reimbursement
            
            return round(total_reimbursement, 2)
            
        except Exception as e:
            logger.error(f"Error calculating reimbursement: {e}")
            return 0.0
    
    def _calculate_denial_risk(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        errors: List[str],
        warnings: List[str]
    ) -> float:
        """Calculate denial risk score (0-1, where 1 is highest risk)."""
        
        risk_score = 0.0
        
        # Base risk from errors and warnings
        risk_score += len(errors) * 0.3
        risk_score += len(warnings) * 0.1
        
        # Risk from code combinations
        if not icd10_codes:
            risk_score += 0.4  # High risk if no diagnosis codes
        
        if len(cpt_codes) > 3:
            risk_score += 0.1  # Slight risk for multiple procedures
        
        # Cap at 1.0
        return min(1.0, risk_score)
    
    async def _generate_coding_suggestions(
        self,
        cpt_codes: List[str],
        icd10_codes: List[str],
        errors: List[str]
    ) -> List[str]:
        """Generate coding improvement suggestions."""
        
        suggestions = []
        
        # Suggest missing diagnosis categories
        for error in errors:
            if "requires diagnosis from categories" in error:
                suggestions.append("Consider adding diagnosis codes from the required categories")
        
        # Suggest primary diagnosis if missing
        if not icd10_codes:
            suggestions.append("Add at least one primary diagnosis code to support medical necessity")
        
        # Suggest modifier usage
        for cpt_code in cpt_codes:
            for exam_type, mapping in self.cpt_mappings.items():
                if mapping.get("primary_cpt") == cpt_code and mapping.get("requires_modifier"):
                    suggestions.append(f"Consider adding appropriate modifier (26/TC) for CPT {cpt_code}")
        
        return suggestions
    
    async def suggest_diagnosis_codes(
        self,
        findings: str,
        exam_type: str
    ) -> List[Dict[str, Any]]:
        """Suggest appropriate ICD-10 codes based on findings and exam type."""
        
        suggestions = []
        
        try:
            findings_lower = findings.lower()
            
            # Analyze findings for pathology keywords
            pathology_keywords = {
                "normal": "normal_findings",
                "stenosis": "vascular_pathology.carotid_stenosis",
                "atherosclerosis": "vascular_pathology.atherosclerosis",
                "heart failure": "cardiac_pathology.heart_failure",
                "valve": "cardiac_pathology.valve_disease",
                "cardiomyopathy": "cardiac_pathology.cardiomyopathy",
                "pneumonia": "pulmonary_pathology",
                "copd": "pulmonary_pathology"
            }
            
            # Find matching pathologies
            matched_categories = []
            for keyword, category in pathology_keywords.items():
                if keyword in findings_lower:
                    matched_categories.append(category)
            
            # If no pathology found, suggest normal findings
            if not matched_categories:
                matched_categories = ["normal_findings"]
            
            # Generate suggestions from matched categories
            for category_path in matched_categories:
                category_data = self._get_nested_category(category_path)
                
                if isinstance(category_data, dict):
                    for code, info in category_data.items():
                        if isinstance(info, dict) and "description" in info:
                            suggestions.append({
                                "code": code,
                                "description": info["description"],
                                "category": info.get("category", "unknown"),
                                "confidence": 0.8,
                                "primary_suggested": info.get("primary_suitable", False)
                            })
            
            # Sort by confidence and primary suitability
            suggestions.sort(key=lambda x: (x["primary_suggested"], x["confidence"]), reverse=True)
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting diagnosis codes: {e}")
            return []
    
    def _get_nested_category(self, category_path: str) -> Any:
        """Get nested category data from ICD-10 mappings."""
        
        parts = category_path.split(".")
        data = self.icd10_mappings
        
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return {}
        
        return data
    
    async def generate_superbill_async(self, db: Session, report_id: str):
        """Async wrapper for superbill generation (for background tasks)."""
        try:
            await self.generate_superbill(db, report_id)
        except Exception as e:
            logger.error(f"Background superbill generation failed: {e}")
    
    def _convert_to_superbill_response(self, superbill: Superbill) -> SuperbillResponse:
        """Convert Superbill model to SuperbillResponse schema."""
        
        # Convert services to ServiceLine objects
        services = [
            ServiceLine(
                cpt_code=service["cpt_code"],
                description=service["description"],
                units=service["units"],
                charge=service["charge"],
                modifiers=service.get("modifiers", [])
            )
            for service in superbill.services
        ]
        
        # Convert diagnoses to DiagnosisCode objects
        diagnoses = [
            DiagnosisCode(
                icd10_code=diagnosis["icd10_code"],
                description=diagnosis["description"],
                primary=diagnosis["primary"]
            )
            for diagnosis in superbill.diagnoses
        ]
        
        # Convert patient info to PatientInfo object
        patient_info = PatientInfo(
            patient_id=superbill.patient_info["patient_id"],
            name=superbill.patient_info["name"],
            dob=superbill.patient_info["dob"],
            gender=superbill.patient_info["gender"],
            address=superbill.patient_info.get("address"),
            insurance=superbill.patient_info.get("insurance")
        )
        
        return SuperbillResponse(
            id=superbill.id,
            superbill_id=superbill.superbill_id,
            report_id=superbill.report_id,
            patient_info=patient_info,
            services=services,
            diagnoses=diagnoses,
            total_charges=superbill.total_charges,
            x12_837p_data=superbill.x12_837p_data,
            provider_npi=superbill.provider_npi,
            facility_name=superbill.facility_name,
            facility_address=superbill.facility_address,
            validated=superbill.validated,
            validation_errors=superbill.validation_errors,
            submitted=superbill.submitted,
            submission_date=superbill.submission_date,
            created_at=superbill.created_at,
            updated_at=superbill.updated_at
        )