#!/usr/bin/env python3
"""
Test script to verify DICOM image loading from backend
"""

import requests
import json
from pathlib import Path

def test_backend_endpoints():
    """Test backend endpoints for image serving"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Backend Image Serving")
    print("=" * 50)
    
    # Test patient files endpoint
    try:
        response = requests.get(f"{base_url}/patients/PAT002/files")
        if response.status_code == 200:
            files_data = response.json()
            print(f"✅ Patient PAT002 files: {len(files_data.get('files', []))} files")
            
            for file_info in files_data.get('files', [])[:5]:  # Show first 5 files
                print(f"   📄 {file_info['filename']} ({file_info['file_size']} bytes)")
                
                # Test if file is accessible
                file_url = f"{base_url}{file_info['file_url']}"
                try:
                    file_response = requests.head(file_url)
                    status = "✅ Accessible" if file_response.status_code == 200 else f"❌ {file_response.status_code}"
                    print(f"      {status}: {file_url}")
                except Exception as e:
                    print(f"      ❌ Error: {e}")
        else:
            print(f"❌ Failed to get files: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing files endpoint: {e}")
    
    print()
    
    # Test specific image files
    test_images = [
        "/uploads/PAT002/16TEST_preview.png",
        "/uploads/PAT002/17TEST_preview.png", 
        "/uploads/PAT002/MRBRAIN_preview.png",
        "/uploads/PAT002/TEST12_preview.png",
        "/uploads/PAT002/16TEST_normalized.png",
        "/uploads/PAT002/MRBRAIN_normalized.png"
    ]
    
    print("🖼️ Testing Specific Image Files")
    print("=" * 50)
    
    for image_path in test_images:
        try:
            image_url = f"{base_url}{image_path}"
            response = requests.head(image_url)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'unknown')
                content_length = response.headers.get('content-length', 'unknown')
                print(f"✅ {image_path}")
                print(f"   Type: {content_type}, Size: {content_length} bytes")
            else:
                print(f"❌ {image_path} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {image_path} - Error: {e}")
    
    print()
    
    # Test studies endpoint
    try:
        response = requests.get(f"{base_url}/patients/PAT002/studies")
        if response.status_code == 200:
            studies_data = response.json()
            print(f"✅ Patient PAT002 studies: {len(studies_data.get('studies', []))} studies")
            
            for study in studies_data.get('studies', [])[:3]:  # Show first 3 studies
                print(f"   🔬 {study.get('study_description', 'Unknown')} - {study.get('original_filename', 'N/A')}")
                if 'dicom_url' in study:
                    print(f"      DICOM URL: {study['dicom_url']}")
        else:
            print(f"❌ Failed to get studies: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing studies endpoint: {e}")

def check_local_files():
    """Check what files actually exist locally"""
    print("\n📁 Local File System Check")
    print("=" * 50)
    
    uploads_dir = Path("uploads/PAT002")
    if uploads_dir.exists():
        files = list(uploads_dir.iterdir())
        print(f"✅ Found {len(files)} files in uploads/PAT002/")
        
        # Group by type
        preview_files = [f for f in files if 'preview' in f.name]
        normalized_files = [f for f in files if 'normalized' in f.name]
        thumbnail_files = [f for f in files if 'thumbnail' in f.name]
        dcm_files = [f for f in files if f.suffix.upper() == '.DCM']
        
        print(f"   🖼️ Preview images: {len(preview_files)}")
        for f in preview_files:
            size_kb = f.stat().st_size / 1024
            print(f"      {f.name} ({size_kb:.1f} KB)")
            
        print(f"   🔧 Normalized images: {len(normalized_files)}")
        for f in normalized_files:
            size_kb = f.stat().st_size / 1024
            print(f"      {f.name} ({size_kb:.1f} KB)")
            
        print(f"   📋 DICOM files: {len(dcm_files)}")
        for f in dcm_files:
            size_kb = f.stat().st_size / 1024
            print(f"      {f.name} ({size_kb:.1f} KB)")
    else:
        print("❌ uploads/PAT002/ directory not found")

if __name__ == "__main__":
    print("🏥 DICOM Image Loading Test")
    print("=" * 50)
    
    check_local_files()
    test_backend_endpoints()
    
    print("\n🎯 Summary:")
    print("If images are not loading in the frontend:")
    print("1. Check that backend is running on port 8000")
    print("2. Verify CORS is enabled for image serving")
    print("3. Check browser console for specific error messages")
    print("4. Ensure image files have correct permissions")