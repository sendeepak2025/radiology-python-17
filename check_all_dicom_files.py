#!/usr/bin/env python3
"""
Comprehensive DICOM File Validation Script
Checks all DICOM files in the uploads directory for correctness and support
"""

import os
import json
import pydicom
from pathlib import Path
import traceback
from typing import Dict, List, Any

def check_dicom_file(file_path: str) -> Dict[str, Any]:
    """Check a single DICOM file for validity and extract key information"""
    result = {
        'file_path': file_path,
        'file_name': os.path.basename(file_path),
        'file_size': 0,
        'is_valid_dicom': False,
        'is_readable': False,
        'has_pixel_data': False,
        'is_multiframe': False,
        'frame_count': 0,
        'modality': None,
        'study_uid': None,
        'series_uid': None,
        'instance_uid': None,
        'patient_id': None,
        'study_date': None,
        'image_dimensions': None,
        'transfer_syntax': None,
        'compression': None,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Check if file exists and get size
        if not os.path.exists(file_path):
            result['errors'].append('File does not exist')
            return result
            
        result['file_size'] = os.path.getsize(file_path)
        
        if result['file_size'] == 0:
            result['errors'].append('File is empty (0 bytes)')
            return result
        
        # Try to read as DICOM
        try:
            ds = pydicom.dcmread(file_path, force=True)
            result['is_valid_dicom'] = True
            result['is_readable'] = True
            
            # Extract basic DICOM information
            result['modality'] = getattr(ds, 'Modality', None)
            result['study_uid'] = getattr(ds, 'StudyInstanceUID', None)
            result['series_uid'] = getattr(ds, 'SeriesInstanceUID', None)
            result['instance_uid'] = getattr(ds, 'SOPInstanceUID', None)
            result['patient_id'] = getattr(ds, 'PatientID', None)
            result['study_date'] = getattr(ds, 'StudyDate', None)
            
            # Check for pixel data
            if hasattr(ds, 'PixelData'):
                result['has_pixel_data'] = True
                
                # Get image dimensions
                if hasattr(ds, 'Rows') and hasattr(ds, 'Columns'):
                    result['image_dimensions'] = {
                        'rows': ds.Rows,
                        'columns': ds.Columns,
                        'samples_per_pixel': getattr(ds, 'SamplesPerPixel', 1),
                        'bits_allocated': getattr(ds, 'BitsAllocated', None),
                        'bits_stored': getattr(ds, 'BitsStored', None)
                    }
                
                # Check if multiframe
                if hasattr(ds, 'NumberOfFrames'):
                    result['is_multiframe'] = True
                    result['frame_count'] = ds.NumberOfFrames
                else:
                    result['frame_count'] = 1
            
            # Transfer syntax information
            if hasattr(ds, 'file_meta') and hasattr(ds.file_meta, 'TransferSyntaxUID'):
                result['transfer_syntax'] = str(ds.file_meta.TransferSyntaxUID)
                
                # Common transfer syntaxes
                transfer_syntaxes = {
                    '1.2.840.10008.1.2': 'Implicit VR Little Endian',
                    '1.2.840.10008.1.2.1': 'Explicit VR Little Endian',
                    '1.2.840.10008.1.2.2': 'Explicit VR Big Endian',
                    '1.2.840.10008.1.2.4.50': 'JPEG Baseline',
                    '1.2.840.10008.1.2.4.51': 'JPEG Extended',
                    '1.2.840.10008.1.2.4.57': 'JPEG Lossless',
                    '1.2.840.10008.1.2.4.70': 'JPEG Lossless SV1',
                    '1.2.840.10008.1.2.4.80': 'JPEG-LS Lossless',
                    '1.2.840.10008.1.2.4.81': 'JPEG-LS Near Lossless',
                    '1.2.840.10008.1.2.4.90': 'JPEG 2000 Lossless',
                    '1.2.840.10008.1.2.4.91': 'JPEG 2000',
                    '1.2.840.10008.1.2.5': 'RLE Lossless'
                }
                
                syntax_name = transfer_syntaxes.get(result['transfer_syntax'], 'Unknown')
                result['compression'] = syntax_name
                
                # Check for compressed formats
                if 'JPEG' in syntax_name or 'RLE' in syntax_name:
                    result['warnings'].append(f'Compressed format: {syntax_name}')
            
            # Validate required DICOM elements
            required_elements = ['StudyInstanceUID', 'SeriesInstanceUID', 'SOPInstanceUID']
            missing_elements = []
            for element in required_elements:
                if not hasattr(ds, element) or getattr(ds, element) is None:
                    missing_elements.append(element)
            
            if missing_elements:
                result['warnings'].append(f'Missing required elements: {", ".join(missing_elements)}')
            
            # Check for common issues
            if result['has_pixel_data']:
                try:
                    # Try to access pixel array to verify it's readable
                    pixel_array = ds.pixel_array
                    if pixel_array is None:
                        result['warnings'].append('Pixel data exists but cannot be read as array')
                    elif pixel_array.size == 0:
                        result['warnings'].append('Pixel array is empty')
                except Exception as e:
                    result['warnings'].append(f'Cannot access pixel array: {str(e)}')
            else:
                result['warnings'].append('No pixel data found')
                
        except pydicom.errors.InvalidDicomError as e:
            result['errors'].append(f'Invalid DICOM format: {str(e)}')
        except Exception as e:
            result['errors'].append(f'Error reading DICOM: {str(e)}')
            
    except Exception as e:
        result['errors'].append(f'Unexpected error: {str(e)}')
        result['errors'].append(f'Traceback: {traceback.format_exc()}')
    
    return result

def scan_directory_for_dicom(directory: str) -> List[Dict[str, Any]]:
    """Scan directory recursively for DICOM files"""
    dicom_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.upper().endswith('.DCM') or file.upper().endswith('.DICOM'):
                file_path = os.path.join(root, file)
                dicom_files.append(file_path)
    
    return dicom_files

def main():
    """Main function to check all DICOM files"""
    uploads_dir = "uploads"
    
    print("🔍 DICOM File Validation Report")
    print("=" * 50)
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Uploads directory '{uploads_dir}' not found!")
        return
    
    # Find all DICOM files
    dicom_files = scan_directory_for_dicom(uploads_dir)
    
    if not dicom_files:
        print("❌ No DICOM files found in uploads directory!")
        return
    
    print(f"📁 Found {len(dicom_files)} DICOM files")
    print()
    
    # Check each file
    results = []
    valid_files = 0
    invalid_files = 0
    multiframe_files = 0
    compressed_files = 0
    
    for i, file_path in enumerate(dicom_files, 1):
        print(f"🔍 Checking file {i}/{len(dicom_files)}: {os.path.basename(file_path)}")
        
        result = check_dicom_file(file_path)
        results.append(result)
        
        if result['is_valid_dicom']:
            valid_files += 1
            print(f"  ✅ Valid DICOM file")
            
            if result['is_multiframe']:
                multiframe_files += 1
                print(f"  📊 Multi-frame: {result['frame_count']} frames")
            
            if result['compression'] and 'JPEG' in result['compression']:
                compressed_files += 1
                print(f"  🗜️ Compressed: {result['compression']}")
            
            if result['modality']:
                print(f"  🏥 Modality: {result['modality']}")
            
            if result['image_dimensions']:
                dims = result['image_dimensions']
                print(f"  📐 Dimensions: {dims['rows']}x{dims['columns']}")
        else:
            invalid_files += 1
            print(f"  ❌ Invalid DICOM file")
        
        if result['errors']:
            for error in result['errors']:
                print(f"  🚨 Error: {error}")
        
        if result['warnings']:
            for warning in result['warnings']:
                print(f"  ⚠️ Warning: {warning}")
        
        print()
    
    # Summary
    print("📊 VALIDATION SUMMARY")
    print("=" * 30)
    print(f"Total files checked: {len(dicom_files)}")
    print(f"Valid DICOM files: {valid_files}")
    print(f"Invalid files: {invalid_files}")
    print(f"Multi-frame files: {multiframe_files}")
    print(f"Compressed files: {compressed_files}")
    print()
    
    # Detailed results by patient
    patients = {}
    for result in results:
        if result['is_valid_dicom'] and result['patient_id']:
            patient_id = result['patient_id']
            if patient_id not in patients:
                patients[patient_id] = []
            patients[patient_id].append(result)
    
    if patients:
        print("👥 RESULTS BY PATIENT")
        print("=" * 25)
        for patient_id, patient_files in patients.items():
            print(f"Patient {patient_id}: {len(patient_files)} files")
            for file_result in patient_files:
                status = "✅" if file_result['is_valid_dicom'] else "❌"
                frames = f" ({file_result['frame_count']} frames)" if file_result['is_multiframe'] else ""
                print(f"  {status} {file_result['file_name']}{frames}")
        print()
    
    # Save detailed results
    output_file = "dicom_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"💾 Detailed results saved to: {output_file}")
    
    # Overall assessment
    if invalid_files == 0:
        print("🎉 ALL DICOM FILES ARE VALID AND SUPPORTED!")
    elif valid_files > invalid_files:
        print("✅ Most DICOM files are valid, but some issues found.")
    else:
        print("⚠️ Significant issues found with DICOM files.")

if __name__ == "__main__":
    main()