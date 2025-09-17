#!/usr/bin/env python3
"""
Generate sample DICOM files for testing Kiro-mini system.
Requires pydicom library: pip install pydicom
"""

import os
import datetime
from pydicom import Dataset, FileDataset
from pydicom.uid import generate_uid, ImplicitVRLittleEndian
import numpy as np

def create_sample_dicom(exam_type="echo_complete", patient_id="TEST001"):
    """Create a sample DICOM file for testing."""
    
    # Create file meta information
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.6.1"  # Ultrasound Image Storage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.ImplementationClassUID = generate_uid()
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    
    # Create main dataset
    ds = FileDataset("sample.dcm", {}, file_meta=file_meta, preamble=b"\0" * 128)
    
    # Patient Information
    ds.PatientName = f"Test^Patient^{patient_id}"
    ds.PatientID = patient_id
    ds.PatientBirthDate = "19800101"
    ds.PatientSex = "M"
    
    # Study Information
    ds.StudyInstanceUID = generate_uid()
    ds.StudyID = "1"
    ds.StudyDate = datetime.datetime.now().strftime("%Y%m%d")
    ds.StudyTime = datetime.datetime.now().strftime("%H%M%S")
    ds.AccessionNumber = f"ACC{patient_id}"
    
    # Series Information
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesNumber = "1"
    ds.SeriesDate = ds.StudyDate
    ds.SeriesTime = ds.StudyTime
    
    # Instance Information
    ds.SOPInstanceUID = generate_uid()
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.InstanceNumber = "1"
    
    # Exam-specific information
    if exam_type == "echo_complete":
        ds.Modality = "US"
        ds.StudyDescription = "Echocardiogram Complete"
        ds.SeriesDescription = "Echo 2D Complete Study"
        ds.BodyPartExamined = "HEART"
        
    elif exam_type == "vascular_carotid":
        ds.Modality = "US"
        ds.StudyDescription = "Carotid Duplex Ultrasound"
        ds.SeriesDescription = "Carotid Artery Duplex"
        ds.BodyPartExamined = "NECK"
        
    elif exam_type == "ct_chest":
        ds.Modality = "CT"
        ds.StudyDescription = "CT Chest with Contrast"
        ds.SeriesDescription = "Chest CT Axial"
        ds.BodyPartExamined = "CHEST"
        
    else:
        ds.Modality = "US"
        ds.StudyDescription = "General Ultrasound"
        ds.SeriesDescription = "General US Study"
        ds.BodyPartExamined = "ABDOMEN"
    
    # Image Information
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 512
    ds.Columns = 512
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    
    # Create sample pixel data (simple gradient)
    pixel_array = np.zeros((512, 512), dtype=np.uint8)
    for i in range(512):
        for j in range(512):
            pixel_array[i, j] = (i + j) % 256
    
    ds.PixelData = pixel_array.tobytes()
    
    # Additional required fields
    ds.ImageType = ["ORIGINAL", "PRIMARY"]
    ds.ContentDate = ds.StudyDate
    ds.ContentTime = ds.StudyTime
    ds.AcquisitionDate = ds.StudyDate
    ds.AcquisitionTime = ds.StudyTime
    
    # Institution Information
    ds.InstitutionName = "Kiro Medical Center"
    ds.InstitutionAddress = "123 Medical Drive, Healthcare City, HC 12345"
    ds.ReferringPhysicianName = "Dr^Referring^Physician"
    ds.PerformingPhysicianName = "Dr^Performing^Physician"
    
    return ds

def save_sample_dicoms():
    """Generate and save sample DICOM files for testing."""
    
    # Create test_dicoms directory
    os.makedirs("test_dicoms", exist_ok=True)
    
    # Generate different exam types
    exam_types = [
        ("echo_complete", "ECHO001"),
        ("vascular_carotid", "CAROTID001"),
        ("ct_chest", "CT001"),
        ("general_us", "US001")
    ]
    
    for exam_type, patient_id in exam_types:
        ds = create_sample_dicom(exam_type, patient_id)
        filename = f"test_dicoms/{exam_type}_{patient_id}.dcm"
        ds.save_as(filename)
        print(f"Created: {filename}")
        print(f"  Study UID: {ds.StudyInstanceUID}")
        print(f"  Patient ID: {ds.PatientID}")
        print(f"  Modality: {ds.Modality}")
        print(f"  Description: {ds.StudyDescription}")
        print()

if __name__ == "__main__":
    try:
        save_sample_dicoms()
        print("Sample DICOM files generated successfully!")
        print("\nTo send to Orthanc, use:")
        print("storescu -aec KIRO-MINI -aet TEST_SCU localhost 4242 test_dicoms/")
    except ImportError:
        print("Error: pydicom library not found.")
        print("Install with: pip install pydicom numpy")
    except Exception as e:
        print(f"Error generating DICOM files: {e}")