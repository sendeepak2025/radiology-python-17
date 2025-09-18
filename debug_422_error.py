#!/usr/bin/env python3
"""
Debug the 422 error that's still happening
"""

import requests
import os

def test_backend_endpoint():
    """Test what's causing the 422 error"""
    
    # Test with a dummy DICOM-like file
    test_content = b"DICM" + b"\x00" * 100
    
    url = "http://localhost:8001/patients/PAT002/upload/dicom"
    
    files = {
        'files': ('sdfga.dcm', test_content, 'application/dicom')
    }
    
    data = {
        'description': 'Test DICOM upload'
    }
    
    try:
        print(f"🧪 Testing upload: {url}")
        print(f"📁 File: sdfga.dcm")
        print(f"📊 Content-Type: application/dicom")
        
        response = requests.post(url, files=files, data=data)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        print(f"📄 Response text: {response.text}")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"📋 Error details: {error_data}")
            except:
                print("❌ Could not parse error response as JSON")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8001/health")
        print(f"✅ Backend health: {response.status_code}")
        print(f"📋 Health response: {response.json()}")
    except Exception as e:
        print(f"❌ Backend not responding: {e}")

if __name__ == "__main__":
    print("🔍 Debugging 422 error...")
    
    # Check backend health first
    check_backend_health()
    
    # Test the problematic upload
    test_backend_endpoint()