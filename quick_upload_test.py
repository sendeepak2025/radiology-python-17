#!/usr/bin/env python3
"""
Quick test to verify current upload system
"""

import requests
import json

def test_upload_system():
    """Test the current upload system end-to-end"""
    
    print("🧪 Testing Current Upload System")
    print("=" * 40)
    
    # 1. Test backend health
    try:
        health = requests.get("http://localhost:8000/health")
        print(f"✅ Backend Health: {health.status_code}")
        print(f"   Version: {health.json().get('version', 'unknown')}")
    except Exception as e:
        print(f"❌ Backend Health Failed: {e}")
        return
    
    # 2. Test upload endpoint with correct parameters
    test_content = b"DICM" + b"\x00" * 200  # Larger test file
    
    files = {
        'files': ('test_upload.dcm', test_content, 'application/dicom')
    }
    
    data = {
        'description': 'Quick test upload'
    }
    
    try:
        print("\n🚀 Testing Upload...")
        response = requests.post(
            "http://localhost:8000/patients/QUICKTEST/upload/dicom",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Upload Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload Successful!")
            print(f"   Study UID: {result.get('study_uid', 'N/A')}")
            print(f"   File Size: {result.get('file_size', 'N/A')} bytes")
            print(f"   Processing: {'Success' if result.get('processing_result', {}).get('success') else 'Failed'}")
            
            # 3. Test getting studies
            try:
                studies = requests.get("http://localhost:8000/patients/QUICKTEST/studies")
                if studies.status_code == 200:
                    study_data = studies.json()
                    print(f"✅ Studies Retrieved: {len(study_data.get('studies', []))} studies found")
                else:
                    print(f"⚠️ Studies Retrieval: {studies.status_code}")
            except Exception as e:
                print(f"❌ Studies Retrieval Failed: {e}")
                
        else:
            print("❌ Upload Failed!")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Upload Request Failed: {e}")
    
    print("\n" + "=" * 40)
    print("🏁 Test Complete")

if __name__ == "__main__":
    test_upload_system()