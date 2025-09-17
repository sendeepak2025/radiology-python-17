#!/usr/bin/env python3
"""
Complete upload fix - start backend and test uploads
"""

import subprocess
import time
import requests
import sys
import os
from pathlib import Path
import threading

def start_backend():
    """Start the fixed backend"""
    print("🚀 Starting fixed backend with upload support...")
    
    # Check if fixed backend exists
    if not os.path.exists("fixed_upload_backend.py"):
        print("❌ fixed_upload_backend.py not found!")
        return None
    
    # Start the backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return process

def wait_for_backend():
    """Wait for backend to be ready"""
    print("⏳ Waiting for backend to start...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i+1}/30)")
    
    print("❌ Backend failed to start within 30 seconds")
    return False

def test_upload_endpoints():
    """Test all upload functionality"""
    print("\n🔍 Testing upload endpoints...")
    
    # Test 1: Health check
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health: {health_data['status']} (v{health_data['version']})")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Patient endpoint
    try:
        response = requests.get("http://localhost:8000/patients?limit=100")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients: Found {data['total']} patients")
        else:
            print(f"❌ Patients endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Patients endpoint error: {e}")
    
    # Test 3: Create test DICOM file and upload
    print("\n📤 Testing DICOM upload...")
    
    test_file = Path("test_dicom_upload.dcm")
    try:
        # Create a realistic test DICOM file
        dicom_content = b"DICM" + b"\x00" * 128 + b"test dicom data for upload testing" * 100
        test_file.write_bytes(dicom_content)
        
        # Test upload
        with open(test_file, 'rb') as f:
            files = {'file': ('test_dicom_upload.dcm', f, 'application/dicom')}
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files,
                timeout=30
            )
        
        print(f"📤 Upload response: {response.status_code}")
        
        if response.status_code == 200:
            upload_data = response.json()
            print("✅ DICOM upload SUCCESS!")
            print(f"   File: {upload_data['filename']}")
            print(f"   Size: {upload_data['file_size']} bytes")
            print(f"   Type: {upload_data['file_type']}")
            print(f"   URL: {upload_data['file_url']}")
            
            # Test 4: Get patient files
            print("\n📁 Testing get patient files...")
            response = requests.get("http://localhost:8000/patients/PAT001/files")
            if response.status_code == 200:
                files_data = response.json()
                print(f"✅ Patient files: Found {files_data['total_files']} files")
                for file_info in files_data['files']:
                    print(f"   - {file_info['filename']} ({file_info['file_size']} bytes)")
            
            # Test 5: Serve uploaded file
            print("\n🌐 Testing file serving...")
            response = requests.get(f"http://localhost:8000{upload_data['file_url']}")
            if response.status_code == 200:
                print(f"✅ File serving: OK ({len(response.content)} bytes)")
            else:
                print(f"❌ File serving failed: {response.status_code}")
            
            return True
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False
    
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

def main():
    """Main function"""
    print("🏥 Complete Upload Fix & Test")
    print("=" * 40)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    try:
        # Wait for backend to be ready
        if not wait_for_backend():
            return
        
        # Test upload functionality
        success = test_upload_endpoints()
        
        if success:
            print("\n🎉 ALL UPLOAD TESTS PASSED!")
            print("✅ Your frontend uploads should now work perfectly!")
            print("\n🌐 Backend is running at: http://localhost:8000")
            print("📤 Upload endpoint: POST /patients/PAT001/upload/dicom")
            print("📖 API docs: http://localhost:8000/docs")
            
            print("\n⚠️  Keep this terminal open and try your frontend upload!")
            print("Press Ctrl+C to stop the backend...")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Stopping backend...")
        else:
            print("\n❌ Some upload tests failed!")
            print("Check the errors above for details.")
    
    finally:
        # Clean up
        if backend_process:
            backend_process.terminate()
            backend_process.wait()

if __name__ == "__main__":
    main()