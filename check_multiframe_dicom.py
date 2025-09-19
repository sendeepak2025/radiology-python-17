#!/usr/bin/env python3
"""
Check if DICOM file is multi-frame
"""

import pydicom
import os
import numpy as np

def check_dicom_frames(dicom_path):
    """Check DICOM file for multi-frame information"""
    
    if not os.path.exists(dicom_path):
        print(f"File not found: {dicom_path}")
        return
    
    try:
        print(f"Reading DICOM file: {dicom_path}")
        ds = pydicom.dcmread(dicom_path)
        
        print(f"SOP Class UID: {getattr(ds, 'SOPClassUID', 'Not found')}")
        print(f"Number of Frames: {getattr(ds, 'NumberOfFrames', 'Not found')}")
        print(f"Rows: {getattr(ds, 'Rows', 'Not found')}")
        print(f"Columns: {getattr(ds, 'Columns', 'Not found')}")
        print(f"Samples Per Pixel: {getattr(ds, 'SamplesPerPixel', 'Not found')}")
        print(f"Photometric Interpretation: {getattr(ds, 'PhotometricInterpretation', 'Not found')}")
        
        # Check pixel data
        if hasattr(ds, 'pixel_array'):
            pixel_array = ds.pixel_array
            print(f"Pixel Array Shape: {pixel_array.shape}")
            print(f"Pixel Array Dtype: {pixel_array.dtype}")
            print(f"Pixel Array Min/Max: {pixel_array.min()}/{pixel_array.max()}")
            
            if len(pixel_array.shape) == 3:
                num_frames = pixel_array.shape[0]
                print(f"✅ Multi-frame detected: {num_frames} frames")
                print(f"   Frame size: {pixel_array.shape[1]} x {pixel_array.shape[2]}")
                return num_frames
            else:
                print("❌ Single frame detected")
                return 1
        else:
            print("❌ No pixel data found")
            return 0
            
    except Exception as e:
        print(f"Error reading DICOM: {e}")
        return 0

if __name__ == "__main__":
    # Check the specific file
    dicom_path = "uploads/P001/0002.DCM"
    frames = check_dicom_frames(dicom_path)
    
    print(f"\n🎯 Result: {frames} frames detected")
    
    if frames > 1:
        print("✅ This is a multi-frame DICOM that needs proper handling!")
    elif frames == 1:
        print("ℹ️  This is a single-frame DICOM")
    else:
        print("❌ Could not determine frame count")