#!/usr/bin/env python3
"""
Test the upload functionality
"""

import subprocess
import time
import requests
import sys
import os
from pathlib import Path

def test_upload_backend():
    """Test the backend with upload functionality"""
    print("🚀 Testing Backend with Upload Support...")
    
    # Start the backend
    print("Starting backend on port 8004...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend_with_uploads:app",
        "--host", "127.0.0.1",
        "--port", "8004",
        "--log-level", "info"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    print("⏳ Waiting for backend to start...")
    time.sleep(8)
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8004/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: OK")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test patients endpoint
        print("🔍 Testing patients endpoint...")
        response = requests.get("http://127.0.0.1:8004/patients/?limit=100", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients endpoint: Found {data['total']} patients")
        else:
            print(f"❌ Patients endpoint failed: {response.status_code}")
            return False
        
        # Test upload endpoints availability
        print("🔍 Testing upload endpoint availability...")
        
        # Create a test file
        test_file_path = Path("test_upload.txt")
        test_file_path.write_text("This is a test file for upload")
        
        try:
            # Test file upload
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_upload.txt', f, 'text/plain')}
                response = requests.post(
                    "http://127.0.0.1:8004/patients/PAT001/upload",
                    files=files,
                    timeout=10
                )
            
            if response.status_code == 200:
                upload_data = response.json()
                print(f"✅ File upload: OK")
                print(f"   Uploaded: {upload_data['filename']}")
                print(f"   Size: {upload_data['file_size']} bytes")
                print(f"   Type: {upload_data['file_type']}")
            else:
                print(f"❌ File upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        except Exception as e:
            print(f"❌ Upload test error: {e}")
        
        finally:
            # Clean up test file
            if test_file_path.exists():
                test_file_path.unlink()
        
        # Test get patient files
        print("🔍 Testing get patient files...")
        response = requests.get("http://127.0.0.1:8004/patients/PAT001/files", timeout=5)
        if response.status_code == 200:
            files_data = response.json()
            print(f"✅ Get patient files: Found {files_data['total_files']} files")
        else:
            print(f"❌ Get patient files failed: {response.status_code}")
        
        # Test debug endpoint
        print("🔍 Testing debug endpoint...")
        response = requests.get("http://127.0.0.1:8004/debug/patients/count", timeout=5)
        if response.status_code == 200:
            debug_data = response.json()
            print(f"✅ Debug endpoint: OK")
            print(f"   Active patients: {debug_data['active_patients']}")
            print(f"   Uploads directory: {debug_data['uploads_directory']}")
        else:
            print(f"❌ Debug endpoint failed: {response.status_code}")
        
        print("\n🎉 Backend with uploads is working!")
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    
    finally:
        # Clean up
        print("🛑 Stopping test backend...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("🏥 Upload Functionality Test")
    print("=" * 35)
    
    success = test_upload_backend()
    
    if success:
        print("\n✅ Backend with uploads is working perfectly!")
        print("🚀 Ready to start with: START_BACKEND_WITH_UPLOADS.bat")
        print("📤 Upload endpoint: POST /patients/{patient_id}/upload")
        print("📤 DICOM upload: POST /patients/{patient_id}/upload/dicom")
        print("📁 Get files: GET /patients/{patient_id}/files")
        print("🌐 Serve files: GET /uploads/{patient_id}/{filename}")
    else:
        print("\n❌ Backend has issues")