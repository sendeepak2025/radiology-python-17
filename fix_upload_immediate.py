#!/usr/bin/env python3
"""
Fix upload issue immediately
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def main():
    print("🚀 Starting backend and testing upload...")
    
    # Start backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "backend_with_uploads:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
    
    # Wait for startup
    time.sleep(3)
    
    try:
        # Test upload immediately
        print("📤 Testing DICOM upload...")
        
        # Create test file
        test_file = Path("test_dicom.dcm")
        test_file.write_text("DICM test data")
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_dicom.dcm', f, 'application/dicom')}
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files,
                timeout=10
            )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Upload working!")
            print(response.json())
        else:
            print(f"❌ Upload failed: {response.text}")
        
        test_file.unlink()
        
        print("\n🎯 Backend is ready! Try your frontend upload now.")
        print("Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()