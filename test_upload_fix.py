#!/usr/bin/env python3
"""
Test and fix upload issue
"""

import subprocess
import time
import requests
import sys
import os
from pathlib import Path

def start_and_test_backend():
    """Start backend and test upload endpoint"""
    print("🚀 Starting backend with uploads...")
    
    # Start the backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend_with_uploads:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    print("⏳ Waiting for backend to start...")
    time.sleep(5)
    
    try:
        # Test health
        print("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running on port 8000")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test the exact endpoint your frontend is calling
        print("🔍 Testing DICOM upload endpoint...")
        
        # Create a test DICOM file
        test_file = Path("test.dcm")
        test_file.write_bytes(b"DICM" + b"test dicom data" * 100)  # Fake DICOM data
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': ('test.dcm', f, 'application/dicom')}
                response = requests.post(
                    "http://localhost:8000/patients/PAT001/upload/dicom",
                    files=files,
                    timeout=10
                )
            
            print(f"📤 Upload response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("✅ DICOM upload working!")
                print(f"   File: {data['filename']}")
                print(f"   Size: {data['file_size']} bytes")
                print(f"   Type: {data['file_type']}")
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        except Exception as e:
            print(f"❌ Upload test error: {e}")
        
        finally:
            if test_file.exists():
                test_file.unlink()
        
        # Test get all endpoints
        print("🔍 Testing all endpoints...")
        endpoints = [
            "/patients?limit=100",
            "/patients/PAT001",
            "/patients/PAT001/files",
            "/debug/patients/count"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                status = "✅" if response.status_code == 200 else "❌"
                print(f"   {status} {endpoint} → {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint} → Error: {e}")
        
        print("\n🎉 Backend is ready for your frontend!")
        print("🌐 Your frontend can now upload to:")
        print("   http://localhost:8000/patients/PAT001/upload/dicom")
        
        # Keep running
        print("\n⚠️  Keep this running and try your upload again!")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopping backend...")
        
        return True
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("🏥 Upload Fix - Starting Backend")
    print("=" * 35)
    start_and_test_backend()