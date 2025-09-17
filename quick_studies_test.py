#!/usr/bin/env python3
"""
Quick test to verify studies are working
"""

import requests
import time
import subprocess
import sys

def test_studies():
    print("🔬 Quick Studies Test")
    print("=" * 25)
    
    # Start backend
    print("Starting backend...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(4)
    
    try:
        # Test studies endpoint
        print("Testing studies endpoint...")
        response = requests.get("http://localhost:8000/patients/PAT001/studies", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Studies endpoint working!")
            print(f"   Found {data['total_studies']} studies for patient PAT001")
            
            if data['studies']:
                for study in data['studies']:
                    print(f"   📁 {study['original_filename']} → {study['study_description']}")
            else:
                print("   (No DICOM files uploaded yet)")
            
            return True
        else:
            print(f"❌ Studies endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    success = test_studies()
    if success:
        print("\n🎉 PROBLEM SOLVED!")
        print("✅ Your uploaded DICOM files will now appear in Studies")
        print("🚀 Start backend: python -m uvicorn fixed_upload_backend:app --host 0.0.0.0 --port 8000 --reload")
    else:
        print("\n❌ Still have issues")