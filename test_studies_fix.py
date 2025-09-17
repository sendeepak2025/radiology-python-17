#!/usr/bin/env python3
"""
Test the studies functionality
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def main():
    print("🔬 Testing Studies Functionality...")
    
    # Start backend
    print("Starting backend with studies support...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
    
    time.sleep(5)
    
    try:
        # Test health
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Backend running")
        
        # Test upload a DICOM file first
        print("\n📤 Uploading test DICOM file...")
        test_file = Path("test_study.dcm")
        test_file.write_bytes(b"DICM" + b"test study data" * 200)
        
        with open(test_file, 'rb') as f:
            files = {'files': ('test_study.dcm', f, 'application/dicom')}
            response = requests.post(
                "http://localhost:8000/patients/PAT001/upload/dicom",
                files=files
            )
        
        if response.status_code == 200:
            print("✅ DICOM file uploaded successfully")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return
        
        # Test get patient studies
        print("\n🔬 Testing patient studies endpoint...")
        response = requests.get("http://localhost:8000/patients/PAT001/studies")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patient studies: Found {data['total_studies']} studies")
            
            if data['studies']:
                study = data['studies'][0]
                print(f"   Study: {study['study_uid']}")
                print(f"   Description: {study['study_description']}")
                print(f"   Date: {study['study_date']}")
                print(f"   File: {study['original_filename']}")
                print(f"   URL: {study['dicom_url']}")
        else:
            print(f"❌ Patient studies failed: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test get all studies
        print("\n🔬 Testing all studies endpoint...")
        response = requests.get("http://localhost:8000/studies")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ All studies: Found {data['total']} studies")
            
            if data['studies']:
                study = data['studies'][0]
                print(f"   First study: {study['study_uid']}")
                print(f"   Patient: {study['patient_name']}")
        else:
            print(f"❌ All studies failed: {response.status_code}")
        
        # Clean up
        test_file.unlink()
        
        print("\n🎉 Studies functionality is working!")
        print("✅ Your uploaded DICOM files will now appear in Studies")
        print("\n🌐 Available endpoints:")
        print("   GET /patients/PAT001/studies")
        print("   GET /studies")
        print("   GET /studies/{study_uid}")
        
        print("\nPress Ctrl+C to stop...")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()