#!/usr/bin/env python3
"""
Analyze the study data from the API response
"""

import json
import requests

def analyze_study_data():
    print("🔍 Study Data Analysis for PAT002")
    print("=" * 60)
    
    try:
        # Get study data from API
        response = requests.get("http://localhost:8000/patients/PAT002/studies")
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            return
        
        data = response.json()
        studies = data.get('studies', [])
        
        print(f"📋 Found {len(studies)} studies for PAT002:")
        
        for i, study in enumerate(studies):
            print(f"\n🔍 Study {i+1}:")
            print(f"   Study UID: {study.get('study_uid', 'N/A')}")
            print(f"   Original Filename: {study.get('original_filename', 'N/A')}")
            print(f"   Status: {study.get('status', 'N/A')}")
            print(f"   Processing Status: {study.get('processing_status', 'N/A')}")
            print(f"   Modality: {study.get('modality', 'N/A')}")
            print(f"   File Size: {study.get('file_size', 'N/A')} bytes")
            
            # Check processing error
            if study.get('processing_error'):
                print(f"   ❌ Processing Error: {study['processing_error']}")
            
            # Check image URLs
            image_urls = study.get('image_urls', [])
            print(f"   📷 Image URLs ({len(image_urls)}):")
            for j, url in enumerate(image_urls):
                print(f"     {j+1}. {url}")
            
            # Check DICOM metadata
            metadata = study.get('dicom_metadata', {})
            if metadata:
                print(f"   📋 DICOM Metadata:")
                print(f"     - Patient Name: {metadata.get('patient_name', 'N/A')}")
                print(f"     - Modality: {metadata.get('modality', 'N/A')}")
                print(f"     - Study Description: {metadata.get('study_description', 'N/A')}")
                print(f"     - Series Description: {metadata.get('series_description', 'N/A')}")
            
            # Check if suitable for 3D
            is_valid = study.get('processing_status') == 'completed'
            has_pixel_data = study.get('file_size', 0) > 1000  # Rough check
            
            print(f"   🎯 3D Compatibility:")
            print(f"     - Valid DICOM: {'✅' if is_valid else '❌'}")
            print(f"     - Has Pixel Data: {'✅' if has_pixel_data else '❌'}")
            print(f"     - Suitable for 3D: {'✅' if is_valid and has_pixel_data else '❌'}")
        
        # Summary for 3D rendering
        valid_studies = [s for s in studies if s.get('processing_status') == 'completed' and s.get('file_size', 0) > 1000]
        print(f"\n🎯 3D Rendering Summary:")
        print(f"   ✅ Valid studies for 3D: {len(valid_studies)}")
        
        if len(valid_studies) >= 2:
            print(f"   ✅ Multiple slices available - Good for 3D volume rendering")
        elif len(valid_studies) == 1:
            print(f"   ⚠️  Only one valid slice - Limited 3D rendering")
        else:
            print(f"   ❌ No valid studies for 3D rendering")
        
        # Check if they're from the same series
        if len(valid_studies) > 1:
            series_descriptions = set()
            for study in valid_studies:
                metadata = study.get('dicom_metadata', {})
                series_desc = metadata.get('series_description', '')
                if series_desc:
                    series_descriptions.add(series_desc)
            
            print(f"   📋 Unique Series: {len(series_descriptions)}")
            if len(series_descriptions) == 1:
                print(f"   ✅ All from same series - Perfect for 3D!")
            else:
                print(f"   ⚠️  Different series - May affect 3D quality")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    analyze_study_data()