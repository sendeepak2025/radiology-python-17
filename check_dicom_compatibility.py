#!/usr/bin/env python3
"""
DICOM Compatibility Checker for Kiro-mini Viewer
Checks if DICOM files are compatible with the current viewer implementation
"""

import os
import json
import pydicom
import requests
from pathlib import Path
import traceback
from typing import Dict, List, Any

def check_viewer_compatibility(file_path: str) -> Dict[str, Any]:
    """Check if DICOM file is compatible with the current viewer"""
    result = {
        'file_path': file_path,
        'file_name': os.path.basename(file_path),
        'viewer_compatible': False,
        'web_accessible': False,
        'can_convert_to_png': False,
        'supports_multiframe': False,
        'transfer_syntax_supported': False,
        'pixel_data_accessible': False,
        'metadata_complete': False,
        'compatibility_score': 0,
        'issues': [],
        'recommendations': []
    }
    
    try:
        # Read DICOM file
        ds = pydicom.dcmread(file_path, force=True)
        
        # Check required metadata for viewer
        required_fields = ['StudyInstanceUID', 'SeriesInstanceUID', 'SOPInstanceUID', 'PatientID']
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(ds, field) or getattr(ds, field) is None:
                missing_fields.append(field)
        
        if not missing_fields:
            result['metadata_complete'] = True
            result['compatibility_score'] += 25
        else:
            result['issues'].append(f'Missing required metadata: {", ".join(missing_fields)}')
        
        # Check pixel data accessibility
        if hasattr(ds, 'PixelData'):
            try:
                pixel_array = ds.pixel_array
                if pixel_array is not None and pixel_array.size > 0:
                    result['pixel_data_accessible'] = True
                    result['compatibility_score'] += 25
                else:
                    result['issues'].append('Pixel data exists but cannot be converted to array')
            except Exception as e:
                result['issues'].append(f'Cannot access pixel data: {str(e)}')
        else:
            result['issues'].append('No pixel data found')
        
        # Check transfer syntax compatibility
        supported_syntaxes = [
            '1.2.840.10008.1.2',      # Implicit VR Little Endian
            '1.2.840.10008.1.2.1',    # Explicit VR Little Endian
            '1.2.840.10008.1.2.2',    # Explicit VR Big Endian
            '1.2.840.10008.1.2.4.50', # JPEG Baseline
            '1.2.840.10008.1.2.4.51', # JPEG Extended
            '1.2.840.10008.1.2.4.57', # JPEG Lossless
            '1.2.840.10008.1.2.4.70'  # JPEG Lossless SV1
        ]
        
        if hasattr(ds, 'file_meta') and hasattr(ds.file_meta, 'TransferSyntaxUID'):
            transfer_syntax = str(ds.file_meta.TransferSyntaxUID)
            if transfer_syntax in supported_syntaxes:
                result['transfer_syntax_supported'] = True
                result['compatibility_score'] += 25
            else:
                result['issues'].append(f'Unsupported transfer syntax: {transfer_syntax}')
                result['recommendations'].append('Convert to supported transfer syntax')
        
        # Check multiframe support
        if hasattr(ds, 'NumberOfFrames') and ds.NumberOfFrames > 1:
            result['supports_multiframe'] = True
            result['compatibility_score'] += 15
            
            # Additional multiframe checks
            if ds.NumberOfFrames > 100:
                result['recommendations'].append('Large multiframe file - may impact performance')
        else:
            result['compatibility_score'] += 10  # Single frame is easier to handle
        
        # Check if file can be converted to PNG (for web display)
        try:
            if result['pixel_data_accessible']:
                # Try to normalize pixel data for PNG conversion
                pixel_array = ds.pixel_array
                
                # Handle different bit depths
                if hasattr(ds, 'BitsAllocated'):
                    if ds.BitsAllocated in [8, 16]:
                        result['can_convert_to_png'] = True
                        result['compatibility_score'] += 10
                    else:
                        result['issues'].append(f'Unusual bit depth: {ds.BitsAllocated}')
                else:
                    result['issues'].append('Missing BitsAllocated information')
        except Exception as e:
            result['issues'].append(f'Cannot test PNG conversion: {str(e)}')
        
        # Overall compatibility assessment
        if result['compatibility_score'] >= 80:
            result['viewer_compatible'] = True
        
        # Check web accessibility (if file is in uploads and has been processed)
        relative_path = file_path.replace('uploads\\', '').replace('uploads/', '')
        web_url = f'http://localhost:8000/uploads/{relative_path}'
        
        try:
            response = requests.head(web_url, timeout=5)
            if response.status_code == 200:
                result['web_accessible'] = True
                result['compatibility_score'] += 5
        except:
            result['issues'].append('File not accessible via web server')
        
    except Exception as e:
        result['issues'].append(f'Error processing file: {str(e)}')
    
    return result

def check_frontend_support():
    """Check if frontend components support current DICOM files"""
    print("🖥️ FRONTEND COMPATIBILITY CHECK")
    print("=" * 35)
    
    # Check if MultiFrameDicomViewer exists and is properly configured
    viewer_path = "frontend/src/components/DICOM/MultiFrameDicomViewer.tsx"
    if os.path.exists(viewer_path):
        print("✅ MultiFrameDicomViewer component found")
        
        # Check for key features in the viewer
        with open(viewer_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        features = {
            'buildImageUrl': 'buildImageUrl' in content,
            'multiframe_support': 'NumberOfFrames' in content or 'frame' in content.lower(),
            'error_handling': 'try' in content and 'catch' in content,
            'loading_states': 'loading' in content.lower(),
            'zoom_controls': 'zoom' in content.lower(),
            'frame_navigation': 'currentSlice' in content or 'frame' in content
        }
        
        for feature, supported in features.items():
            status = "✅" if supported else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}: {supported}")
    else:
        print("❌ MultiFrameDicomViewer component not found")
    
    print()

def main():
    """Main function to check DICOM compatibility"""
    uploads_dir = "uploads"
    
    print("🔍 DICOM COMPATIBILITY ANALYSIS")
    print("=" * 40)
    
    # Check frontend support first
    check_frontend_support()
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Uploads directory '{uploads_dir}' not found!")
        return
    
    # Find all DICOM files
    dicom_files = []
    for root, dirs, files in os.walk(uploads_dir):
        for file in files:
            if file.upper().endswith('.DCM') or file.upper().endswith('.DICOM'):
                file_path = os.path.join(root, file)
                dicom_files.append(file_path)
    
    if not dicom_files:
        print("❌ No DICOM files found!")
        return
    
    print(f"📁 Analyzing {len(dicom_files)} DICOM files for viewer compatibility")
    print()
    
    # Check each file
    results = []
    compatible_files = 0
    web_accessible_files = 0
    multiframe_files = 0
    
    for i, file_path in enumerate(dicom_files, 1):
        print(f"🔍 Checking compatibility {i}/{len(dicom_files)}: {os.path.basename(file_path)}")
        
        result = check_viewer_compatibility(file_path)
        results.append(result)
        
        if result['viewer_compatible']:
            compatible_files += 1
            print(f"  ✅ Viewer Compatible (Score: {result['compatibility_score']}/100)")
        else:
            print(f"  ❌ Not Compatible (Score: {result['compatibility_score']}/100)")
        
        if result['web_accessible']:
            web_accessible_files += 1
            print(f"  🌐 Web Accessible")
        
        if result['supports_multiframe']:
            multiframe_files += 1
            print(f"  📊 Multi-frame Support")
        
        if result['issues']:
            for issue in result['issues'][:3]:  # Show first 3 issues
                print(f"  ⚠️ {issue}")
        
        if result['recommendations']:
            for rec in result['recommendations'][:2]:  # Show first 2 recommendations
                print(f"  💡 {rec}")
        
        print()
    
    # Summary
    print("📊 COMPATIBILITY SUMMARY")
    print("=" * 30)
    print(f"Total files analyzed: {len(dicom_files)}")
    print(f"Viewer compatible: {compatible_files}")
    print(f"Web accessible: {web_accessible_files}")
    print(f"Multi-frame supported: {multiframe_files}")
    print(f"Compatibility rate: {(compatible_files/len(dicom_files)*100):.1f}%")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("=" * 20)
    
    if compatible_files == len(dicom_files):
        print("🎉 All DICOM files are compatible with the current viewer!")
    elif compatible_files > len(dicom_files) * 0.8:
        print("✅ Most files are compatible. Address specific issues for remaining files.")
    else:
        print("⚠️ Significant compatibility issues found. Consider:")
        print("  - Updating viewer to support more transfer syntaxes")
        print("  - Converting problematic files to supported formats")
        print("  - Adding fallback mechanisms for unsupported files")
    
    if web_accessible_files < compatible_files:
        print("🌐 Some compatible files are not web accessible. Check:")
        print("  - Backend file serving configuration")
        print("  - File permissions and paths")
        print("  - URL routing in the web server")
    
    # Save results
    output_file = "dicom_compatibility_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed compatibility results saved to: {output_file}")

if __name__ == "__main__":
    main()