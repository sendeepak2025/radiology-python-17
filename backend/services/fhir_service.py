"""
HL7 FHIR export service for EHR integration.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import json

from models import Study, Report, Superbill
from services.audit_service import AuditService

logger = logging.getLogger(__name__)

class FHIRService:
    """Service for generating HL7 FHIR resources for EHR integration."""
    
    def __init__(self):
        self.audit_service = AuditService()
        self.fhir_version = "4.0.1"
        self.system_url = "https://kiro-mini.healthcare"
    
    async def export_diagnostic_report(
        self,
        db: Session,
        report_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a report as a FHIR DiagnosticReport resource.
        """
        try:
            # Get the report and associated study
            report = db.query(Report).filter(Report.report_id == report_id).first()
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            study = db.query(Study).filter(Study.study_uid == report.study_uid).first()
            if not study:
                raise ValueError(f"Study {report.study_uid} not found")
            
            # Create FHIR DiagnosticReport
            fhir_report = {
                "resourceType": "DiagnosticReport",
                "id": str(report.report_id),
                "meta": {
                    "versionId": "1",
                    "lastUpdated": report.updated_at.isoformat() if report.updated_at else report.created_at.isoformat(),
                    "profile": [
                        "http://hl7.org/fhir/StructureDefinition/DiagnosticReport"
                    ]
                },
                "identifier": [
                    {
                        "use": "official",
                        "system": f"{self.system_url}/report-id",
                        "value": str(report.report_id)
                    }
                ],
                "basedOn": [
                    {
                        "reference": f"ServiceRequest/{study.study_uid}",
                        "display": f"Imaging Study {study.exam_type}"
                    }
                ],
                "status": self._map_report_status_to_fhir(report.status),
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                                "code": "RAD",
                                "display": "Radiology"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": self._get_loinc_code_for_exam(study.exam_type),
                            "display": self._get_exam_display_name(study.exam_type)
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{study.patient_id}",
                    "display": f"Patient {study.patient_id}"
                },
                "effectiveDateTime": study.study_date.isoformat() if study.study_date else study.created_at.isoformat(),
                "issued": report.created_at.isoformat(),
                "performer": [
                    {
                        "reference": f"Practitioner/{report.radiologist_id or 'unknown'}",
                        "display": f"Radiologist {report.radiologist_id or 'Unknown'}"
                    }
                ],
                "resultsInterpreter": [
                    {
                        "reference": f"Practitioner/{report.radiologist_id or 'unknown'}",
                        "display": f"Radiologist {report.radiologist_id or 'Unknown'}"
                    }
                ],
                "imagingStudy": [
                    {
                        "reference": f"ImagingStudy/{study.study_uid}",
                        "display": f"{study.modality} Study"
                    }
                ],
                "conclusion": report.impressions or "No impression provided",
                "conclusionCode": self._create_conclusion_codes(report.diagnosis_codes or [])
            }
            
            # Add findings as observations
            if report.findings:
                fhir_report["result"] = await self._create_observation_references(
                    db, report, study
                )
            
            # Add measurements as observations
            if report.measurements:
                measurement_refs = await self._create_measurement_observations(
                    db, report, study
                )
                if "result" not in fhir_report:
                    fhir_report["result"] = []
                fhir_report["result"].extend(measurement_refs)
            
            # Add presentation attachment if available
            fhir_report["presentedForm"] = [
                {
                    "contentType": "text/plain",
                    "language": "en-US",
                    "data": self._encode_report_text(report),
                    "title": f"Radiology Report - {study.exam_type}",
                    "creation": report.created_at.isoformat()
                }
            ]
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="FHIR_EXPORT",
                event_description=f"FHIR DiagnosticReport exported for report {report_id}",
                resource_type="Report",
                resource_id=report_id,
                report_id=report_id,
                study_uid=report.study_uid,
                user_id=user_id or "system",
                metadata={
                    "fhir_resource_type": "DiagnosticReport",
                    "export_format": "FHIR R4",
                    "includes_measurements": bool(report.measurements),
                    "includes_findings": bool(report.findings)
                }
            )
            
            logger.info(f"FHIR DiagnosticReport exported for report {report_id}")
            return fhir_report
            
        except Exception as e:
            logger.error(f"Error exporting FHIR DiagnosticReport: {str(e)}")
            raise
    
    async def export_imaging_study(
        self,
        db: Session,
        study_uid: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a study as a FHIR ImagingStudy resource.
        """
        try:
            study = db.query(Study).filter(Study.study_uid == study_uid).first()
            if not study:
                raise ValueError(f"Study {study_uid} not found")
            
            fhir_study = {
                "resourceType": "ImagingStudy",
                "id": study.study_uid,
                "meta": {
                    "versionId": "1",
                    "lastUpdated": study.updated_at.isoformat() if study.updated_at else study.created_at.isoformat(),
                    "profile": [
                        "http://hl7.org/fhir/StructureDefinition/ImagingStudy"
                    ]
                },
                "identifier": [
                    {
                        "use": "official",
                        "system": f"{self.system_url}/study-uid",
                        "value": study.study_uid
                    }
                ],
                "status": "available",
                "modality": [
                    {
                        "system": "http://dicom.nema.org/resources/ontology/DCM",
                        "code": study.modality,
                        "display": self._get_modality_display(study.modality)
                    }
                ],
                "subject": {
                    "reference": f"Patient/{study.patient_id}",
                    "display": f"Patient {study.patient_id}"
                },
                "started": study.study_date.isoformat() if study.study_date else study.created_at.isoformat(),
                "numberOfSeries": 1,  # Simplified for prototype
                "numberOfInstances": 1,  # Simplified for prototype
                "procedureCode": [
                    {
                        "coding": [
                            {
                                "system": "http://www.radlex.org",
                                "code": self._get_radlex_code_for_exam(study.exam_type),
                                "display": study.study_description or study.exam_type
                            }
                        ]
                    }
                ],
                "reasonCode": [
                    {
                        "text": f"Clinical indication for {study.exam_type}"
                    }
                ],
                "description": study.study_description or f"{study.modality} {study.exam_type}",
                "series": [
                    {
                        "uid": f"{study.study_uid}.1",
                        "number": 1,
                        "modality": {
                            "system": "http://dicom.nema.org/resources/ontology/DCM",
                            "code": study.modality,
                            "display": self._get_modality_display(study.modality)
                        },
                        "description": study.series_description or "Primary Series",
                        "numberOfInstances": 1,
                        "bodySite": {
                            "system": "http://snomed.info/sct",
                            "code": self._get_body_site_code(study.exam_type),
                            "display": self._get_body_site_display(study.exam_type)
                        },
                        "started": study.study_date.isoformat() if study.study_date else study.created_at.isoformat(),
                        "instance": [
                            {
                                "uid": f"{study.study_uid}.1.1",
                                "sopClass": {
                                    "system": "urn:ietf:rfc:3986",
                                    "code": "urn:oid:1.2.840.10008.5.1.4.1.1.3.1"  # Ultrasound Image Storage
                                },
                                "number": 1,
                                "title": "Primary Image"
                            }
                        ]
                    }
                ]
            }
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="FHIR_EXPORT",
                event_description=f"FHIR ImagingStudy exported for study {study_uid}",
                resource_type="Study",
                resource_id=study_uid,
                study_uid=study_uid,
                user_id=user_id or "system",
                metadata={
                    "fhir_resource_type": "ImagingStudy",
                    "export_format": "FHIR R4",
                    "modality": study.modality,
                    "exam_type": study.exam_type
                }
            )
            
            logger.info(f"FHIR ImagingStudy exported for study {study_uid}")
            return fhir_study
            
        except Exception as e:
            logger.error(f"Error exporting FHIR ImagingStudy: {str(e)}")
            raise
    
    async def export_bundle(
        self,
        db: Session,
        study_uid: str,
        include_reports: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a complete FHIR Bundle containing study and related resources.
        """
        try:
            study = db.query(Study).filter(Study.study_uid == study_uid).first()
            if not study:
                raise ValueError(f"Study {study_uid} not found")
            
            # Create bundle
            bundle = {
                "resourceType": "Bundle",
                "id": str(uuid.uuid4()),
                "meta": {
                    "lastUpdated": datetime.utcnow().isoformat(),
                    "profile": [
                        "http://hl7.org/fhir/StructureDefinition/Bundle"
                    ]
                },
                "identifier": {
                    "system": f"{self.system_url}/bundle-id",
                    "value": f"bundle-{study_uid}"
                },
                "type": "collection",
                "timestamp": datetime.utcnow().isoformat(),
                "entry": []
            }
            
            # Add ImagingStudy
            imaging_study = await self.export_imaging_study(db, study_uid, user_id)
            bundle["entry"].append({
                "fullUrl": f"{self.system_url}/ImagingStudy/{study_uid}",
                "resource": imaging_study
            })
            
            # Add DiagnosticReports if requested
            if include_reports:
                reports = db.query(Report).filter(Report.study_uid == study_uid).all()
                for report in reports:
                    diagnostic_report = await self.export_diagnostic_report(
                        db, str(report.report_id), user_id
                    )
                    bundle["entry"].append({
                        "fullUrl": f"{self.system_url}/DiagnosticReport/{report.report_id}",
                        "resource": diagnostic_report
                    })
            
            # Update bundle total
            bundle["total"] = len(bundle["entry"])
            
            logger.info(f"FHIR Bundle exported for study {study_uid} with {bundle['total']} resources")
            return bundle
            
        except Exception as e:
            logger.error(f"Error exporting FHIR Bundle: {str(e)}")
            raise
    
    def _map_report_status_to_fhir(self, status: str) -> str:
        """Map internal report status to FHIR DiagnosticReport status."""
        status_mapping = {
            "draft": "preliminary",
            "final": "final",
            "billed": "final"
        }
        return status_mapping.get(status, "unknown")
    
    def _get_loinc_code_for_exam(self, exam_type: str) -> str:
        """Get LOINC code for exam type."""
        loinc_mapping = {
            "echo_complete": "34552-0",  # Echocardiography study
            "vascular_carotid": "24627-2",  # Carotid artery study
            "ct_scan": "24627-2",  # CT study
            "mri_scan": "24627-2",  # MRI study
            "xray": "36643-5"  # X-ray study
        }
        return loinc_mapping.get(exam_type, "18748-4")  # Diagnostic imaging study
    
    def _get_exam_display_name(self, exam_type: str) -> str:
        """Get display name for exam type."""
        display_mapping = {
            "echo_complete": "Echocardiography study",
            "vascular_carotid": "Carotid artery duplex scan",
            "ct_scan": "CT scan",
            "mri_scan": "MRI scan",
            "xray": "X-ray study"
        }
        return display_mapping.get(exam_type, "Diagnostic imaging study")
    
    def _get_modality_display(self, modality: str) -> str:
        """Get display name for DICOM modality."""
        modality_mapping = {
            "US": "Ultrasound",
            "CT": "Computed Tomography",
            "MR": "Magnetic Resonance",
            "CR": "Computed Radiography",
            "DX": "Digital Radiography"
        }
        return modality_mapping.get(modality, modality)
    
    def _get_radlex_code_for_exam(self, exam_type: str) -> str:
        """Get RadLex code for exam type."""
        # Simplified RadLex codes for prototype
        radlex_mapping = {
            "echo_complete": "RID10312",  # Echocardiography
            "vascular_carotid": "RID10321",  # Carotid ultrasound
            "ct_scan": "RID10312",  # CT imaging
            "mri_scan": "RID10312",  # MRI imaging
            "xray": "RID10312"  # Radiography
        }
        return radlex_mapping.get(exam_type, "RID10312")
    
    def _get_body_site_code(self, exam_type: str) -> str:
        """Get SNOMED CT body site code for exam type."""
        body_site_mapping = {
            "echo_complete": "80891009",  # Heart structure
            "vascular_carotid": "69105007",  # Carotid artery structure
            "ct_scan": "123037004",  # Body structure
            "mri_scan": "123037004",  # Body structure
            "xray": "123037004"  # Body structure
        }
        return body_site_mapping.get(exam_type, "123037004")
    
    def _get_body_site_display(self, exam_type: str) -> str:
        """Get display name for body site."""
        body_site_mapping = {
            "echo_complete": "Heart",
            "vascular_carotid": "Carotid artery",
            "ct_scan": "Body",
            "mri_scan": "Body",
            "xray": "Body"
        }
        return body_site_mapping.get(exam_type, "Body")
    
    def _create_conclusion_codes(self, diagnosis_codes: List[str]) -> List[Dict[str, Any]]:
        """Create FHIR conclusion codes from ICD-10 codes."""
        conclusion_codes = []
        for code in diagnosis_codes:
            conclusion_codes.append({
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10-cm",
                        "code": code,
                        "display": f"ICD-10 {code}"
                    }
                ]
            })
        return conclusion_codes
    
    async def _create_observation_references(
        self,
        db: Session,
        report: Report,
        study: Study
    ) -> List[Dict[str, Any]]:
        """Create observation references for findings."""
        # In a full implementation, this would create separate Observation resources
        # For now, we'll create inline observations
        return [
            {
                "reference": f"Observation/findings-{report.report_id}",
                "display": "Clinical Findings"
            }
        ]
    
    async def _create_measurement_observations(
        self,
        db: Session,
        report: Report,
        study: Study
    ) -> List[Dict[str, Any]]:
        """Create observation references for measurements."""
        # In a full implementation, this would create separate Observation resources
        # For now, we'll create inline observations
        observations = []
        if report.measurements:
            for measurement_name in report.measurements.keys():
                observations.append({
                    "reference": f"Observation/measurement-{report.report_id}-{measurement_name}",
                    "display": f"Measurement: {measurement_name}"
                })
        return observations
    
    def _encode_report_text(self, report: Report) -> str:
        """Encode report text as base64 for FHIR attachment."""
        import base64
        
        report_text = f"""
RADIOLOGY REPORT

Findings:
{report.findings or 'No findings documented'}

Impressions:
{report.impressions or 'No impressions documented'}

Recommendations:
{report.recommendations or 'No recommendations documented'}

Generated: {report.created_at.isoformat()}
Status: {report.status}
"""
        
        return base64.b64encode(report_text.encode()).decode()