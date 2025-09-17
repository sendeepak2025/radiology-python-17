#!/usr/bin/env python3
"""
Debug the 422 upload error
"""

import requests
from pathlib import Path

def test_upload_formats():
    """Test different upload formats to fix 422 error"""
    
    # Create a test DICOM file
    test_file = Path("test_upload.dcm")
    test_file.write_bytes(b"DICM" + b"test data" * 50)
    
    print("🔍 Testing different upload formats...")
    
    # Test 1: Basic file upload
    print("\n1. Testing basic file upload...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files,
                timeout=10
            )
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: With proper filename and content type
    print("\n2. Testing with filename and content type...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_upload.dcm', f, 'application/dicom')}
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files,
                timeout=10
            )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ SUCCESS!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: With form data
    print("\n3. Testing with form data...")
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_upload.dcm', f, 'application/dicom')}
            data = {'description': 'Test DICOM upload'}
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files,
                data=data,
                timeout=10
            )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ SUCCESS!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 4: Check what the endpoint expects
    print("\n4. Checking endpoint documentation...")
    try:
        response = requests.get("http://localhost:8000/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            upload_endpoint = openapi['paths']['/patients/{patient_id}/upload/dicom']['post']
            print("   Expected parameters:")
            if 'requestBody' in upload_endpoint:
                print(f"   {upload_endpoint['requestBody']}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Clean up
    test_file.unlink()

if __name__ == "__main__":
    print("🏥 Debugging 422 Upload Error")
    print("=" * 35)
    test_upload_formats()