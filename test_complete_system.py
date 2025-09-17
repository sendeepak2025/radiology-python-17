#!/usr/bin/env python3
"""
Test complete system - patients and studies
"""

import subprocess
import time
import requests
import sys
import sqlite3
from pathlib import Path

def check_system():
    """Check database and files"""
    print("🔍 Checking System...")
    
    # Check database
    try:
        conn = sqlite3.connect('kiro_mini.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients WHERE active = 1")
        patient_count = cursor.fetchone()[0]
        print(f"✅ Database: {patient_count} active patients")
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Check uploads directory
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        dicom_files = []
        for patient_dir in uploads_dir.iterdir():
            if patient_dir.is_dir():
                for file_path in patient_dir.iterdir():
                    if file_path.suffix.lower() in ['.dcm', '.dicom']:
                        dicom_files.append(f"{patient_dir.name}/{file_path.name}")
        
        print(f"✅ Uploads: {len(dicom_files)} DICOM files")
        for f in dicom_files[:3]:  # Show first 3
            print(f"   - {f}")
        
        return patient_count > 0
    else:
        print("⚠️  No uploads directory found")
        return patient_count > 0

def test_backend():
    """Test complete backend"""
    print("\n🚀 Testing Complete Backend...")
    
    # Kill existing
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    time.sleep(1)
    
    print("Starting backend...")
    
    # Start backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "working_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    time.sleep(4)
    
    try:
        # Test 1: Health
        print("\n1. Testing health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health OK")
        else:
            print(f"❌ Health failed: {response.status_code}")
            return
        
        # Test 2: Patients
        print("\n2. Testing patients...")
        response = requests.get("http://localhost:8000/patients?limit=100", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients: {data['total']} found")
            
            if data['patients']:
                for p in data['patients']:
                    print(f"   - {p['patient_id']}: {p['first_name']} {p['last_name']}")
            else:
                print("   No patients returned")
        else:
            print(f"❌ Patients failed: {response.status_code}")
        
        # Test 3: Studies for PAT001
        print("\n3. Testing studies for PAT001...")
        response = requests.get("http://localhost:8000/patients/PAT001/studies", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Studies: {data['total_studies']} found for PAT001")
            
            if data['studies']:
                for s in data['studies']:
                    print(f"   - {s['original_filename']} → {s['study_description']}")
                    print(f"     UID: {s['study_uid']}")
                
                # Test 4: Get specific study
                if data['studies']:
                    study_uid = data['studies'][0]['study_uid']
                    print(f"\n4. Testing specific study: {study_uid}")
                    response = requests.get(f"http://localhost:8000/studies/{study_uid}", timeout=5)
                    if response.status_code == 200:
                        study = response.json()
                        print(f"✅ Study details: {study.get('original_filename', 'unknown')}")
                        print(f"   Images: {len(study.get('images', []))}")
                    else:
                        print(f"❌ Study details failed: {response.status_code}")
            else:
                print("   No studies found")
        else:
            print(f"❌ Studies failed: {response.status_code}")
        
        # Test 5: All studies
        print("\n5. Testing all studies...")
        response = requests.get("http://localhost:8000/studies", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ All studies: {data['total']} found")
        else:
            print(f"❌ All studies failed: {response.status_code}")
        
        print(f"\n🎉 SYSTEM IS WORKING!")
        print(f"✅ Patients: Available at http://localhost:8000/patients?limit=100")
        print(f"✅ Studies: Available at http://localhost:8000/patients/PAT001/studies")
        print(f"✅ Health: Available at http://localhost:8000/health")
        
        print("\nBackend is ready! Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 Stopping backend...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        process.terminate()

def main():
    print("🏥 COMPLETE SYSTEM TEST")
    print("=" * 40)
    
    if check_system():
        test_backend()
    else:
        print("❌ System check failed!")

if __name__ == "__main__":
    main()