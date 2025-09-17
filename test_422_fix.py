#!/usr/bin/env python3
"""
Test the 422 fix
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def main():
    print("🔧 Testing 422 Fix...")
    
    # Start backend
    print("Starting fixed backend...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
    
    time.sleep(5)
    
    try:
        # Test with the exact format your frontend uses
        print("📤 Testing with 'files' field (frontend format)...")
        
        test_file = Path("test_422.dcm")
        test_file.write_bytes(b"DICM" + b"test" * 100)
        
        with open(test_file, 'rb') as f:
            # This matches your frontend: formData.append('files', file)
            files = {'files': ('test_422.dcm', f, 'application/dicom')}
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files,
                timeout=10
            )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ 422 ERROR FIXED!")
            print("Your frontend uploads will now work!")
            data = response.json()
            print(f"Uploaded: {data['filename']} ({data['file_size']} bytes)")
        else:
            print(f"❌ Still getting error: {response.status_code}")
            print(f"Response: {response.text}")
        
        test_file.unlink()
        
        if response.status_code == 200:
            print("\n🎯 Backend is ready! Try your upload now!")
            print("Press Ctrl+C to stop...")
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()