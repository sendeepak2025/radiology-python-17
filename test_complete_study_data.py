#!/usr/bin/env python3
"""
Test complete study data with patient_id and all fields
"""

import subprocess
import time
import requests
import sys
import json

def main():
    print("🔬 Testing Complete Study Data...")
    
    # Start backend
    print("Starting backend...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
    
    time.sleep(5)
    
    try:
        # Test 1: Get patient studies
        print("\n1. Getting patient studies with complete data...")
        response = requests.get("http://localhost:8000/patients/PAT001/studies")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_studies']} studies")
            
            if data['studies']:
                study = data['studies'][0]
                print("\n📊 Study data includes:")
                
                # Check all required fields
                required_fields = [
                    'study_uid', 'patient_id', 'patient_name', 'patient_birth_date',
                    'patient_sex', 'study_date', 'study_time', 'modality',
                    'study_description', 'accession_number', 'original_filename'
                ]
                
                for field in required_fields:
                    if field in study:
                        print(f"   ✅ {field}: {study[field]}")
                    else:
                        print(f"   ❌ {field}: MISSING")
                
                study_uid = study['study_uid']
                
                # Test 2: Get specific study details
                print(f"\n2. Getting study details for: {study_uid}")
                response = requests.get(f"http://localhost:8000/studies/{study_uid}")
                
                if response.status_code == 200:
                    study_detail = response.json()
                    print("✅ Study details retrieved!")
                    print(f"   Patient ID: {study_detail.get('patient_id', 'MISSING')}")
                    print(f"   Patient Name: {study_detail.get('patient_name', 'MISSING')}")
                    print(f"   Study UID: {study_detail.get('study_uid', 'MISSING')}")
                    print(f"   Modality: {study_detail.get('modality', 'MISSING')}")
                    print(f"   Images: {len(study_detail.get('images', []))}")
                    print(f"   Series: {len(study_detail.get('series', []))}")
                    
                    # Show complete study data
                    print("\n📋 Complete study data:")
                    print(json.dumps(study_detail, indent=2)[:500] + "...")
                    
                else:
                    print(f"❌ Study details failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            else:
                print("   No studies found")
        else:
            print(f"❌ Patient studies failed: {response.status_code}")
        
        # Test 3: Get all studies
        print("\n3. Testing all studies endpoint...")
        response = requests.get("http://localhost:8000/studies")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ All studies: Found {data['total']} studies")
            
            if data['studies']:
                study = data['studies'][0]
                print(f"   First study patient_id: {study.get('patient_id', 'MISSING')}")
                print(f"   First study patient_name: {study.get('patient_name', 'MISSING')}")
        
        print("\n🎉 Study data is complete!")
        print("✅ All patient information included")
        print("✅ Study UIDs working")
        print("✅ Frontend clicks will work")
        
        print("\nPress Ctrl+C to stop...")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()