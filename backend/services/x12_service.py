"""
X12 EDI conversion service for 837P billing data.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
import json

from models import Superbill, Report, Study
from services.audit_service import AuditService

logger = logging.getLogger(__name__)

class X12Service:
    """Service for converting 837P JSON to X12 EDI format."""
    
    def __init__(self):
        self.audit_service = AuditService()
        self.interchange_control_number = 1
        self.group_control_number = 1
        self.transaction_control_number = 1
    
    async def convert_superbill_to_x12(
        self,
        db: Session,
        superbill_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Convert a superbill to X12 837P format.
        """
        try:
            # Get superbill and related data
            superbill = db.query(Superbill).filter(
                Superbill.superbill_id == superbill_id
            ).first()
            
            if not superbill:
                raise ValueError(f"Superbill {superbill_id} not found")
            
            report = db.query(Report).filter(
                Report.report_id == superbill.report_id
            ).first()
            
            if not report:
                raise ValueError(f"Report {superbill.report_id} not found")
            
            study = db.query(Study).filter(
                Study.study_uid == report.study_uid
            ).first()
            
            if not study:
                raise ValueError(f"Study {report.study_uid} not found")
            
            # Generate X12 837P
            x12_content = self._generate_837p_x12(superbill, report, study)
            
            # Log audit event
            await self.audit_service.log_event(
                db=db,
                event_type="X12_EXPORT",
                event_description=f"X12 837P generated for superbill {superbill_id}",
                resource_type="Superbill",
                resource_id=superbill_id,
                superbill_id=superbill_id,
                report_id=str(superbill.report_id),
                study_uid=report.study_uid,
                user_id=user_id or "system",
                metadata={
                    "export_format": "X12 837P",
                    "transaction_count": 1,
                    "total_charges": float(superbill.total_charges)
                }
            )
            
            logger.info(f"X12 837P generated for superbill {superbill_id}")
            return x12_content
            
        except Exception as e:
            logger.error(f"Error converting superbill to X12: {str(e)}")
            raise
    
    def _generate_837p_x12(
        self,
        superbill: Superbill,
        report: Report,
        study: Study
    ) -> str:
        """
        Generate X12 837P EDI content.
        """
        lines = []
        
        # ISA - Interchange Control Header
        lines.append(self._create_isa_segment())
        
        # GS - Functional Group Header
        lines.append(self._create_gs_segment())
        
        # ST - Transaction Set Header
        lines.append(self._create_st_segment())
        
        # BHT - Beginning of Hierarchical Transaction
        lines.append(self._create_bht_segment(superbill))
        
        # NM1 - Submitter Name
        lines.append(self._create_submitter_nm1_segment())
        
        # PER - Submitter EDI Contact Information
        lines.append(self._create_submitter_per_segment())
        
        # NM1 - Receiver Name
        lines.append(self._create_receiver_nm1_segment())
        
        # HL - Billing Provider Hierarchical Level
        lines.append(self._create_billing_provider_hl_segment())
        
        # NM1 - Billing Provider Name
        lines.append(self._create_billing_provider_nm1_segment(superbill))
        
        # N3 - Billing Provider Address
        lines.append(self._create_billing_provider_n3_segment(superbill))
        
        # N4 - Billing Provider City/State/ZIP
        lines.append(self._create_billing_provider_n4_segment(superbill))
        
        # REF - Billing Provider Tax Identification
        lines.append(self._create_billing_provider_ref_segment(superbill))
        
        # HL - Subscriber Hierarchical Level
        lines.append(self._create_subscriber_hl_segment())
        
        # SBR - Subscriber Information
        lines.append(self._create_sbr_segment())
        
        # NM1 - Subscriber Name
        lines.append(self._create_subscriber_nm1_segment(superbill))
        
        # N3 - Subscriber Address
        lines.append(self._create_subscriber_n3_segment(superbill))
        
        # N4 - Subscriber City/State/ZIP
        lines.append(self._create_subscriber_n4_segment(superbill))
        
        # DMG - Subscriber Demographics
        lines.append(self._create_subscriber_dmg_segment(superbill))
        
        # NM1 - Payer Name
        lines.append(self._create_payer_nm1_segment(superbill))
        
        # HL - Patient Hierarchical Level
        lines.append(self._create_patient_hl_segment())
        
        # PAT - Patient Information
        lines.append(self._create_pat_segment())
        
        # NM1 - Patient Name
        lines.append(self._create_patient_nm1_segment(superbill))
        
        # N3 - Patient Address
        lines.append(self._create_patient_n3_segment(superbill))
        
        # N4 - Patient City/State/ZIP
        lines.append(self._create_patient_n4_segment(superbill))
        
        # DMG - Patient Demographics
        lines.append(self._create_patient_dmg_segment(superbill))
        
        # CLM - Claim Information
        lines.append(self._create_clm_segment(superbill, study))
        
        # DTP - Date - Service Date
        lines.append(self._create_service_date_dtp_segment(study))
        
        # HI - Health Care Diagnosis Code
        lines.append(self._create_hi_segment(superbill))
        
        # Service Lines
        for i, service in enumerate(superbill.services, 1):
            lines.extend(self._create_service_line_segments(service, i))
        
        # SE - Transaction Set Trailer
        lines.append(self._create_se_segment(len(lines) + 1))
        
        # GE - Functional Group Trailer
        lines.append(self._create_ge_segment())
        
        # IEA - Interchange Control Trailer
        lines.append(self._create_iea_segment())
        
        return "~\n".join(lines) + "~\n"
    
    def _create_isa_segment(self) -> str:
        """Create ISA (Interchange Control Header) segment."""
        return (
            f"ISA*00*          *00*          *ZZ*KIROMINI      *ZZ*CLEARINGHOUSE *"
            f"{datetime.now().strftime('%y%m%d')}*{datetime.now().strftime('%H%M')}*^*00501*"
            f"{self.interchange_control_number:09d}*0*P*:"
        )
    
    def _create_gs_segment(self) -> str:
        """Create GS (Functional Group Header) segment."""
        return (
            f"GS*HC*KIROMINI*CLEARINGHOUSE*{datetime.now().strftime('%Y%m%d')}*"
            f"{datetime.now().strftime('%H%M%S')}*{self.group_control_number}*X*005010X222A1"
        )
    
    def _create_st_segment(self) -> str:
        """Create ST (Transaction Set Header) segment."""
        return f"ST*837*{self.transaction_control_number:04d}*005010X222A1"
    
    def _create_bht_segment(self, superbill: Superbill) -> str:
        """Create BHT (Beginning of Hierarchical Transaction) segment."""
        return (
            f"BHT*0019*00*{superbill.superbill_id}*{datetime.now().strftime('%Y%m%d')}*"
            f"{datetime.now().strftime('%H%M%S')}*CH"
        )
    
    def _create_submitter_nm1_segment(self) -> str:
        """Create submitter NM1 segment."""
        return "NM1*41*2*KIRO MEDICAL CENTER*****46*1234567890"
    
    def _create_submitter_per_segment(self) -> str:
        """Create submitter PER segment."""
        return "PER*IC*BILLING DEPARTMENT*TE*5551234567*EM*billing@kiromini.com"
    
    def _create_receiver_nm1_segment(self) -> str:
        """Create receiver NM1 segment."""
        return "NM1*40*2*CLEARINGHOUSE*****46*CLEARINGHOUSE123"
    
    def _create_billing_provider_hl_segment(self) -> str:
        """Create billing provider HL segment."""
        return "HL*1**20*1"
    
    def _create_billing_provider_nm1_segment(self, superbill: Superbill) -> str:
        """Create billing provider NM1 segment."""
        return f"NM1*85*2*{superbill.facility_name}*****XX*{superbill.provider_npi}"
    
    def _create_billing_provider_n3_segment(self, superbill: Superbill) -> str:
        """Create billing provider N3 segment."""
        address = superbill.facility_address or "123 Medical Drive"
        return f"N3*{address}"
    
    def _create_billing_provider_n4_segment(self, superbill: Superbill) -> str:
        """Create billing provider N4 segment."""
        return "N4*Healthcare City*HC*12345"
    
    def _create_billing_provider_ref_segment(self, superbill: Superbill) -> str:
        """Create billing provider REF segment."""
        return f"REF*EI*{superbill.provider_npi}"
    
    def _create_subscriber_hl_segment(self) -> str:
        """Create subscriber HL segment."""
        return "HL*2*1*22*0"
    
    def _create_sbr_segment(self) -> str:
        """Create SBR segment."""
        return "SBR*P*18*******CI"
    
    def _create_subscriber_nm1_segment(self, superbill: Superbill) -> str:
        """Create subscriber NM1 segment."""
        patient_name = superbill.patient_info.get("name", "PATIENT NAME")
        name_parts = patient_name.split(" ", 1)
        last_name = name_parts[0] if name_parts else "PATIENT"
        first_name = name_parts[1] if len(name_parts) > 1 else "NAME"
        
        return f"NM1*IL*1*{last_name}*{first_name}****MI*{superbill.patient_info.get('patient_id', 'UNKNOWN')}"
    
    def _create_subscriber_n3_segment(self, superbill: Superbill) -> str:
        """Create subscriber N3 segment."""
        address = superbill.patient_info.get("address", "123 Patient Street")
        return f"N3*{address}"
    
    def _create_subscriber_n4_segment(self, superbill: Superbill) -> str:
        """Create subscriber N4 segment."""
        return "N4*Patient City*PC*12345"
    
    def _create_subscriber_dmg_segment(self, superbill: Superbill) -> str:
        """Create subscriber DMG segment."""
        dob = superbill.patient_info.get("dob", "19800101")
        gender = superbill.patient_info.get("gender", "U")
        return f"DMG*D8*{dob.replace('-', '')}*{gender}"
    
    def _create_payer_nm1_segment(self, superbill: Superbill) -> str:
        """Create payer NM1 segment."""
        insurance = superbill.patient_info.get("insurance", {})
        payer_name = insurance.get("payer_name", "PRIMARY INSURANCE")
        payer_id = insurance.get("payer_id", "PAYER123")
        
        return f"NM1*PR*2*{payer_name}*****PI*{payer_id}"
    
    def _create_patient_hl_segment(self) -> str:
        """Create patient HL segment."""
        return "HL*3*2*23*0"
    
    def _create_pat_segment(self) -> str:
        """Create PAT segment."""
        return "PAT*19"
    
    def _create_patient_nm1_segment(self, superbill: Superbill) -> str:
        """Create patient NM1 segment."""
        patient_name = superbill.patient_info.get("name", "PATIENT NAME")
        name_parts = patient_name.split(" ", 1)
        last_name = name_parts[0] if name_parts else "PATIENT"
        first_name = name_parts[1] if len(name_parts) > 1 else "NAME"
        
        return f"NM1*QC*1*{last_name}*{first_name}"
    
    def _create_patient_n3_segment(self, superbill: Superbill) -> str:
        """Create patient N3 segment."""
        address = superbill.patient_info.get("address", "123 Patient Street")
        return f"N3*{address}"
    
    def _create_patient_n4_segment(self, superbill: Superbill) -> str:
        """Create patient N4 segment."""
        return "N4*Patient City*PC*12345"
    
    def _create_patient_dmg_segment(self, superbill: Superbill) -> str:
        """Create patient DMG segment."""
        dob = superbill.patient_info.get("dob", "19800101")
        gender = superbill.patient_info.get("gender", "U")
        return f"DMG*D8*{dob.replace('-', '')}*{gender}"
    
    def _create_clm_segment(self, superbill: Superbill, study: Study) -> str:
        """Create CLM segment."""
        return (
            f"CLM*{superbill.superbill_id}*{superbill.total_charges:.2f}***"
            f"11:B:1*Y*A*Y*I*P"
        )
    
    def _create_service_date_dtp_segment(self, study: Study) -> str:
        """Create service date DTP segment."""
        service_date = study.study_date or study.created_at
        return f"DTP*472*D8*{service_date.strftime('%Y%m%d')}"
    
    def _create_hi_segment(self, superbill: Superbill) -> str:
        """Create HI (diagnosis codes) segment."""
        diagnosis_codes = []
        for i, diagnosis in enumerate(superbill.diagnoses):
            pointer = "ABK" if i == 0 else "ABF"  # Primary vs secondary
            diagnosis_codes.append(f"{pointer}:{diagnosis['icd10_code']}")
        
        return f"HI*{':'.join(diagnosis_codes)}"
    
    def _create_service_line_segments(self, service: Dict[str, Any], line_number: int) -> List[str]:
        """Create service line segments (LX, SV1, DTP)."""
        segments = []
        
        # LX - Service Line Number
        segments.append(f"LX*{line_number}")
        
        # SV1 - Professional Service
        cpt_code = service.get("cpt_code", "")
        charge = service.get("charge", 0)
        units = service.get("units", 1)
        
        segments.append(f"SV1*HC:{cpt_code}*{charge:.2f}*UN*{units}***1")
        
        # DTP - Service Date
        segments.append(f"DTP*472*D8*{datetime.now().strftime('%Y%m%d')}")
        
        return segments
    
    def _create_se_segment(self, segment_count: int) -> str:
        """Create SE (Transaction Set Trailer) segment."""
        return f"SE*{segment_count}*{self.transaction_control_number:04d}"
    
    def _create_ge_segment(self) -> str:
        """Create GE (Functional Group Trailer) segment."""
        return f"GE*1*{self.group_control_number}"
    
    def _create_iea_segment(self) -> str:
        """Create IEA (Interchange Control Trailer) segment."""
        return f"IEA*1*{self.interchange_control_number:09d}"
    
    async def validate_x12_format(self, x12_content: str) -> Dict[str, Any]:
        """
        Validate X12 format and structure.
        """
        try:
            lines = x12_content.strip().split("~\n")
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "segment_count": len(lines),
                "transaction_sets": 0
            }
            
            # Basic validation
            if not lines[0].startswith("ISA"):
                validation_result["valid"] = False
                validation_result["errors"].append("Missing ISA segment")
            
            if not lines[-1].startswith("IEA"):
                validation_result["valid"] = False
                validation_result["errors"].append("Missing IEA segment")
            
            # Count transaction sets
            st_count = sum(1 for line in lines if line.startswith("ST*837"))
            validation_result["transaction_sets"] = st_count
            
            if st_count == 0:
                validation_result["valid"] = False
                validation_result["errors"].append("No 837P transaction sets found")
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "segment_count": 0,
                "transaction_sets": 0
            }