#!/usr/bin/env python3
"""
Check DICOM files in PAT002 directory for validity and properties
"""

import os
import sys
from pathlib import Path

try:
    import pydicom
    print("✅ pydicom is available")
except ImportError:
    print("❌ pydicom not available, installing...")
    os.system("pip install pydicom")
    import pydicom

def check_dicom_file(file_path):
    """Check if a file is a valid DICOM file and extract key properties"""
    try:
        print(f"\n🔍 Checking: {file_path}")
        
        # Try to read the DICOM file
        ds = pydicom.dcmread(file_path, force=True)
        
        print(f"✅ Valid DICOM file")
        print(f"   Patient Name: {getattr(ds, 'PatientName', 'N/A')}")
        print(f"   Patient ID: {getattr(ds, 'PatientID', 'N/A')}")
        print(f"   Study Date: {getattr(ds, 'StudyDate', 'N/A')}")
        print(f"   Modality: {getattr(ds, 'Modality', 'N/A')}")
        print(f"   Study Description: {getattr(ds, 'StudyDescription', 'N/A')}")
        print(f"   Series Description: {getattr(ds, 'SeriesDescription', 'N/A')}")
        
        # Check image properties
        if hasattr(ds, 'Rows') and hasattr(ds, 'Columns'):
            print(f"   Image Size: {ds.Rows} x {ds.Columns}")
        
        if hasattr(ds, 'NumberOfFrames'):
            print(f"   Number of Frames: {ds.NumberOfFrames}")
        else:
            print(f"   Number of Frames: 1 (single frame)")
            
        if hasattr(ds, 'PixelData'):
            print(f"   Has Pixel Data: Yes")
            print(f"   Pixel Data Size: {len(ds.PixelData)} bytes")
        else:
            print(f"   Has Pixel Data: No")
            
        # Check transfer syntax
        if hasattr(ds, 'file_meta') and hasattr(ds.file_meta, 'TransferSyntaxUID'):
            print(f"   Transfer Syntax: {ds.file_meta.TransferSyntaxUID}")
        
        return True, ds
        
    except Exception as e:
        print(f"❌ Error reading DICOM file: {str(e)}")
        return False, None

def main():
    print("🏥 DICOM File Checker for PAT002")
    print("=" * 50)
    
    pat002_dir = Path("uploads/PAT002")
    if not pat002_dir.exists():
        print(f"❌ Directory not found: {pat002_dir}")
        return
    
    # Find all DICOM files
    dicom_files = []
    for ext in ['*.DCM', '*.dcm', '*.DICOM', '*.dicom']:
        dicom_files.extend(pat002_dir.glob(ext))
    
    if not dicom_files:
        print("❌ No DICOM files found")
        return
    
    print(f"📋 Found {len(dicom_files)} DICOM files:")
    for f in dicom_files:
        print(f"   - {f.name}")
    
    valid_files = []
    invalid_files = []
    
    for dicom_file in dicom_files:
        is_valid, ds = check_dicom_file(dicom_file)
        if is_valid:
            valid_files.append((dicom_file, ds))
        else:
            invalid_files.append(dicom_file)
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Valid DICOM files: {len(valid_files)}")
    print(f"   ❌ Invalid files: {len(invalid_files)}")
    
    if invalid_files:
        print(f"\n❌ Invalid files:")
        for f in invalid_files:
            print(f"   - {f.name}")
    
    # Check if files are suitable for 3D rendering
    print(f"\n🎯 3D Rendering Compatibility:")
    if len(valid_files) >= 2:
        print(f"   ✅ Multiple slices available ({len(valid_files)} files)")
        print(f"   ✅ Suitable for 3D volume rendering")
        
        # Check if they're from the same series
        study_uids = set()
        series_uids = set()
        for file_path, ds in valid_files:
            if hasattr(ds, 'StudyInstanceUID'):
                study_uids.add(ds.StudyInstanceUID)
            if hasattr(ds, 'SeriesInstanceUID'):
                series_uids.add(ds.SeriesInstanceUID)
        
        print(f"   📋 Unique Studies: {len(study_uids)}")
        print(f"   📋 Unique Series: {len(series_uids)}")
        
        if len(series_uids) == 1:
            print(f"   ✅ All files from same series - Perfect for 3D!")
        else:
            print(f"   ⚠️  Files from different series - May affect 3D quality")
            
    elif len(valid_files) == 1:
        print(f"   ⚠️  Only one slice available")
        print(f"   ⚠️  3D rendering will be limited (single slice)")
    else:
        print(f"   ❌ No valid DICOM files for 3D rendering")

if __name__ == "__main__":
    main()