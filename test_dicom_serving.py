#!/usr/bin/env python3
"""
Test script to verify DICOM file serving from the backend
"""

import requests
import os
from pathlib import Path

def test_dicom_serving():
    """Test if DICOM files are being served correctly"""
    
    base_url = "http://localhost:8000"
    
    # Test cases - files we know exist
    test_files = [
        ("P001", "0002.DCM"),
        ("P001", "MRBRAIN.DCM"),
        ("PAT001", "0002.DCM"),
        ("PAT001", "16TEST.DCM"),
    ]
    
    print("🔍 Testing DICOM file serving...")
    print("=" * 50)
    
    for patient_id, filename in test_files:
        # Test direct file access
        file_path = Path("uploads") / patient_id / filename
        if file_path.exists():
            print(f"\n📁 File exists locally: {file_path}")
            print(f"   Size: {file_path.stat().st_size} bytes")
            
            # Test URL access
            url = f"{base_url}/uploads/{patient_id}/{filename}"
            print(f"🌐 Testing URL: {url}")
            
            try:
                response = requests.head(url, timeout=10)
                print(f"   Status: {response.status_code}")
                print(f"   Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print("   ✅ SUCCESS - File accessible via HTTP")
                else:
                    print(f"   ❌ FAILED - HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ FAILED - Request error: {e}")
        else:
            print(f"\n❌ File not found locally: {file_path}")
    
    print("\n" + "=" * 50)
    print("🏥 Testing backend health...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
    
    print("\n🔍 Testing patient studies endpoint...")
    try:
        response = requests.get(f"{base_url}/patients/P001/studies", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Patient studies endpoint working")
            print(f"   Found {data.get('total_studies', 0)} studies")
            
            # Show first study details
            if data.get('studies'):
                study = data['studies'][0]
                print(f"   First study: {study.get('original_filename')}")
                print(f"   DICOM URL: {study.get('dicom_url')}")
        else:
            print(f"❌ Patient studies failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Patient studies request failed: {e}")

if __name__ == "__main__":
    test_dicom_serving()