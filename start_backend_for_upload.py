#!/usr/bin/env python3
"""
Start backend and keep it running for uploads
"""

import subprocess
import sys
import time
import requests

def main():
    print("🚀 Starting Backend for Upload...")
    print("=" * 40)
    
    # Kill any existing processes
    try:
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                      capture_output=True, check=False)
        time.sleep(1)
    except:
        pass
    
    print("Starting fixed backend on port 8000...")
    
    # Start the backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
    
    # Wait for startup
    print("⏳ Waiting for backend to start...")
    time.sleep(5)
    
    # Test if it's working
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and ready!")
            print("🌐 API: http://localhost:8000")
            print("📤 Upload: http://localhost:8000/patients/PAT001/upload/dicom")
            print("📖 Docs: http://localhost:8000/docs")
            print("\n🎯 Your frontend can now upload files!")
            print("Try uploading your 0002 (1).DCM file now.")
            print("\nPress Ctrl+C to stop the backend...")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not responding: {e}")
        return
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping backend...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()