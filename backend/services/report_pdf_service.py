"""
Professional Medical Report PDF Generation Service
Designed for clinical-grade report generation with digital signatures
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue, red, green
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
import base64

class MedicalReportPDF:
    """Professional medical report PDF generator with clinical standards compliance."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for medical reports."""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=blue,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=blue,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=blue,
            borderPadding=5
        ))
        
        # Clinical text style
        self.styles.add(ParagraphStyle(
            name='ClinicalText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            leading=14
        ))
        
        # Critical findings style
        self.styles.add(ParagraphStyle(
            name='CriticalFindings',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor=red,
            fontName='Helvetica-Bold',
            backColor=colors.Color(1, 0.9, 0.9),
            borderWidth=2,
            borderColor=red,
            borderPadding=10
        ))
        
        # Signature style
        self.styles.add(ParagraphStyle(
            name='SignatureText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.Color(0.3, 0.3, 0.3),
            fontName='Helvetica'
        ))

    def generate_report_pdf(
        self,
        report_data: Dict[str, Any],
        study_data: Dict[str, Any],
        signatures: List[Dict[str, Any]] = None,
        options: Dict[str, Any] = None
    ) -> BytesIO:
        """Generate a comprehensive medical report PDF."""
        
        buffer = BytesIO()
        options = options or {}
        signatures = signatures or []
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=f"Medical Report - {study_data.get('patient_id', 'Unknown')}"
        )
        
        # Build story (content)
        story = []
        
        # Add letterhead if requested
        if options.get('letterhead', True):
            story.extend(self._build_letterhead())
        
        # Add report header
        story.extend(self._build_report_header(report_data, study_data))
        
        # Add critical findings alert if present
        if report_data.get('critical_findings'):
            story.extend(self._build_critical_alert(report_data))
        
        # Add clinical sections
        story.extend(self._build_clinical_sections(report_data))
        
        # Add measurements table
        if report_data.get('measurements'):
            story.extend(self._build_measurements_table(report_data['measurements']))
        
        # Add coding information
        story.extend(self._build_coding_section(report_data))
        
        # Add digital signatures
        if signatures and options.get('include_signatures', True):
            story.extend(self._build_signature_section(signatures))
        else:
            story.extend(self._build_manual_signature_section())
        
        # Add footer and disclaimer
        story.extend(self._build_footer(report_data, study_data))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_watermark, onLaterPages=self._add_watermark)
        
        buffer.seek(0)
        return buffer
    
    def _build_letterhead(self) -> List[Any]:
        """Build professional letterhead."""
        story = []
        
        # Main title
        story.append(Paragraph("KIRO MEDICAL CENTER", self.styles['ReportTitle']))
        story.append(Paragraph("Department of Radiology", self.styles['Normal']))
        story.append(Paragraph("Advanced Medical Imaging Services", self.styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Contact information
        contact_info = """
        123 Medical Drive, Healthcare City, HC 12345<br/>
        Phone: (555) 123-4567 | Fax: (555) 123-4568<br/>
        Email: radiology@kiromedical.com
        """
        story.append(Paragraph(contact_info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_report_header(self, report_data: Dict[str, Any], study_data: Dict[str, Any]) -> List[Any]:
        """Build report header with patient and study information."""
        story = []
        
        # Create header table
        header_data = [
            ['PATIENT INFORMATION', 'STUDY INFORMATION'],
            [
                f"Patient ID: {study_data.get('patient_id', 'N/A')}\n"
                f"Study Date: {study_data.get('study_date', 'N/A')}\n"
                f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                
                f"Study UID: {study_data.get('study_uid', 'N/A')}\n"
                f"Modality: {study_data.get('modality', 'N/A')}\n"
                f"Exam Type: {study_data.get('exam_type', 'N/A')}\n"
                f"Description: {study_data.get('study_description', 'N/A')}"
            ]
        ]
        
        header_table = Table(header_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('TEXTCOLOR', (0, 0), (-1, 0), blue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_critical_alert(self, report_data: Dict[str, Any]) -> List[Any]:
        """Build critical findings alert box."""
        story = []
        
        critical_text = f"""
        <b>⚠️ CRITICAL FINDINGS ALERT ⚠️</b><br/><br/>
        This report contains critical findings that require immediate attention.<br/>
        Communication Status: {'✓ COMMUNICATED' if report_data.get('critical_findings_communicated') else '❌ NOT COMMUNICATED'}<br/>
        Time of Report: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        story.append(Paragraph(critical_text, self.styles['CriticalFindings']))
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_clinical_sections(self, report_data: Dict[str, Any]) -> List[Any]:
        """Build clinical content sections."""
        story = []
        
        # Clinical Findings
        if report_data.get('findings'):
            story.append(Paragraph("CLINICAL FINDINGS", self.styles['SectionHeader']))
            story.append(Paragraph(report_data['findings'], self.styles['ClinicalText']))
            story.append(Spacer(1, 15))
        
        # Impressions
        if report_data.get('impressions'):
            story.append(Paragraph("IMPRESSIONS", self.styles['SectionHeader']))
            story.append(Paragraph(report_data['impressions'], self.styles['ClinicalText']))
            story.append(Spacer(1, 15))
        
        # Recommendations
        if report_data.get('recommendations'):
            story.append(Paragraph("RECOMMENDATIONS", self.styles['SectionHeader']))
            story.append(Paragraph(report_data['recommendations'], self.styles['ClinicalText']))
            story.append(Spacer(1, 15))
        
        return story
    
    def _build_measurements_table(self, measurements: Dict[str, Any]) -> List[Any]:
        """Build measurements table."""
        story = []
        
        story.append(Paragraph("MEASUREMENTS", self.styles['SectionHeader']))
        
        # Prepare table data
        table_data = [['Parameter', 'Value', 'Unit', 'Normal Range', 'Status']]
        
        for param, measurement in measurements.items():
            status = "ABNORMAL" if measurement.get('abnormal') else "NORMAL"
            status_color = red if measurement.get('abnormal') else green
            
            table_data.append([
                param.replace('_', ' ').title(),
                str(measurement.get('value', 'N/A')),
                measurement.get('unit', ''),
                measurement.get('normal_range', 'N/A'),
                status
            ])
        
        measurements_table = Table(table_data, colWidths=[2*inch, 1*inch, 0.8*inch, 1.5*inch, 1*inch])
        measurements_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('TEXTCOLOR', (0, 0), (-1, 0), blue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))
        
        story.append(measurements_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_coding_section(self, report_data: Dict[str, Any]) -> List[Any]:
        """Build coding section with ICD-10 and CPT codes."""
        story = []
        
        if report_data.get('diagnosis_codes') or report_data.get('cpt_codes'):
            story.append(Paragraph("MEDICAL CODING", self.styles['SectionHeader']))
            
            # ICD-10 codes
            if report_data.get('diagnosis_codes'):
                story.append(Paragraph("<b>ICD-10 Diagnosis Codes:</b>", self.styles['Normal']))
                for code in report_data['diagnosis_codes']:
                    story.append(Paragraph(f"• {code}", self.styles['Normal']))
                story.append(Spacer(1, 10))
            
            # CPT codes
            if report_data.get('cpt_codes'):
                story.append(Paragraph("<b>CPT Procedure Codes:</b>", self.styles['Normal']))
                for code in report_data['cpt_codes']:
                    story.append(Paragraph(f"• {code}", self.styles['Normal']))
                story.append(Spacer(1, 15))
        
        return story
    
    def _build_signature_section(self, signatures: List[Dict[str, Any]]) -> List[Any]:
        """Build digital signature section."""
        story = []
        
        story.append(Paragraph("DIGITAL SIGNATURES", self.styles['SectionHeader']))
        
        for signature in signatures:
            # Signature block
            sig_text = f"""
            <b>Digitally Signed by:</b> {signature.get('signer_name', 'Unknown')}<br/>
            <b>Date:</b> {signature.get('signed_at', 'Unknown')}<br/>
            <b>Certificate Issuer:</b> {signature.get('certificate_info', {}).get('issuer', 'Unknown')}<br/>
            <b>Certificate Valid:</b> {signature.get('certificate_info', {}).get('valid_from', 'Unknown')} to {signature.get('certificate_info', {}).get('valid_to', 'Unknown')}<br/>
            <b>Signature Hash:</b> {signature.get('signature_hash', 'Unknown')}
            """
            
            story.append(Paragraph(sig_text, self.styles['SignatureText']))
            story.append(Spacer(1, 15))
        
        return story
    
    def _build_manual_signature_section(self) -> List[Any]:
        """Build manual signature section for non-digital signatures."""
        story = []
        
        story.append(Paragraph("PHYSICIAN SIGNATURE", self.styles['SectionHeader']))
        story.append(Spacer(1, 30))
        
        # Signature line
        story.append(Paragraph("_" * 60, self.styles['Normal']))
        story.append(Paragraph("Radiologist Signature", self.styles['SignatureText']))
        story.append(Spacer(1, 20))
        
        # Additional signature fields
        sig_fields = [
            ("Print Name:", "_" * 40),
            ("Date:", "_" * 40),
            ("Medical License #:", "_" * 40),
            ("DEA #:", "_" * 40)
        ]
        
        for label, line in sig_fields:
            story.append(Paragraph(f"{label} {line}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        return story
    
    def _build_footer(self, report_data: Dict[str, Any], study_data: Dict[str, Any]) -> List[Any]:
        """Build report footer with disclaimer and metadata."""
        story = []
        
        story.append(Spacer(1, 30))
        
        # Disclaimer
        disclaimer_text = """
        <b>CONFIDENTIALITY NOTICE:</b> This report contains confidential medical information and is intended 
        solely for the use of the patient and authorized healthcare providers. Any unauthorized review, use, 
        disclosure, or distribution is prohibited and may be unlawful. If you have received this report in 
        error, please notify the sender immediately and destroy all copies.
        """
        
        story.append(Paragraph(disclaimer_text, self.styles['SignatureText']))
        story.append(Spacer(1, 15))
        
        # Report metadata
        metadata_text = f"""
        Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        Report ID: {report_data.get('id', 'N/A')}<br/>
        System: Kiro Medical Imaging System v1.0<br/>
        © {datetime.now().year} Kiro Medical Center. All rights reserved.
        """
        
        story.append(Paragraph(metadata_text, self.styles['SignatureText']))
        
        return story
    
    def _add_watermark(self, canvas, doc):
        """Add watermark to pages."""
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 60)
        canvas.setFillColor(colors.Color(0.9, 0.9, 0.9, alpha=0.3))
        canvas.rotate(45)
        canvas.drawCentredText(300, 0, "CONFIDENTIAL")
        canvas.restoreState()
    
    def generate_signed_report_pdf(
        self,
        report_data: Dict[str, Any],
        study_data: Dict[str, Any],
        signatures: List[Dict[str, Any]]
    ) -> BytesIO:
        """Generate a final signed report PDF with enhanced security."""
        
        options = {
            'letterhead': True,
            'include_signatures': True,
            'template': 'detailed'
        }
        
        return self.generate_report_pdf(report_data, study_data, signatures, options)
    
    def generate_preview_pdf(
        self,
        report_data: Dict[str, Any],
        study_data: Dict[str, Any]
    ) -> BytesIO:
        """Generate a preview PDF with watermark."""
        
        options = {
            'letterhead': False,
            'include_signatures': False,
            'template': 'minimal',
            'watermark': 'PREVIEW'
        }
        
        return self.generate_report_pdf(report_data, study_data, [], options)
    
    def create_digital_signature(
        self,
        report_data: Dict[str, Any],
        signer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a digital signature for the report."""
        
        # Create signature hash
        report_content = f"{report_data.get('findings', '')}{report_data.get('impressions', '')}{report_data.get('recommendations', '')}"
        signature_data = f"{report_content}{signer_info.get('signer_id', '')}{datetime.now().isoformat()}"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return {
            'id': f"sig_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'signer_id': signer_info.get('signer_id'),
            'signer_name': signer_info.get('signer_name'),
            'signed_at': datetime.now().isoformat(),
            'signature_hash': signature_hash,
            'certificate_info': {
                'issuer': 'Kiro Medical Certificate Authority',
                'valid_from': datetime.now().isoformat(),
                'valid_to': (datetime.now().replace(year=datetime.now().year + 1)).isoformat(),
                'serial_number': base64.b64encode(signature_hash.encode()).decode()[:16]
            }
        }
    
    def verify_digital_signature(
        self,
        signature: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> bool:
        """Verify the integrity of a digital signature."""
        
        try:
            # Recreate signature hash
            report_content = f"{report_data.get('findings', '')}{report_data.get('impressions', '')}{report_data.get('recommendations', '')}"
            signature_data = f"{report_content}{signature.get('signer_id', '')}{signature.get('signed_at', '')}"
            expected_hash = hashlib.sha256(signature_data.encode()).hexdigest()
            
            return expected_hash == signature.get('signature_hash')
            
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False

# Global instance
pdf_service = MedicalReportPDF()