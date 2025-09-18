#!/usr/bin/env python3
"""
Test the current working backend upload functionality
"""

import requests
import os

def test_current_backend():
    """Test the current backend upload"""
    
    # Test health first
    try:
        health_response = requests.get("http://localhost:8000/health")
        print(f"✅ Backend health: {health_response.status_code}")
        print(f"📋 Version: {health_response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test upload endpoint
    test_content = b"DICM" + b"\x00" * 100
    
    # Try both parameter names to see which works
    for param_name in ['file', 'files']:
        print(f"\n🧪 Testing with parameter: {param_name}")
        
        files = {
            param_name: ('test.dcm', test_content, 'application/dicom')
        }
        
        data = {
            'description': 'Test upload'
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files,
                data=data
            )
            
            print(f"📊 Status: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print(f"✅ SUCCESS with parameter: {param_name}")
                break
            else:
                print(f"❌ Failed with parameter: {param_name}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_current_backend()