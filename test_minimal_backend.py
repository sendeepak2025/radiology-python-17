#!/usr/bin/env python3
"""
Test minimal backend
"""

import subprocess
import time
import requests
import sys

def main():
    print("🔍 Testing Minimal Backend")
    print("=" * 30)
    
    # Kill existing processes
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    time.sleep(1)
    
    print("Starting minimal backend...")
    
    # Start minimal backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "minimal_working_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    time.sleep(5)
    
    try:
        # Test health
        print("Testing health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Health OK")
            
            # Test debug
            print("Testing debug...")
            response = requests.get("http://localhost:8000/debug/patients/count", timeout=5)
            if response.status_code == 200:
                debug = response.json()
                print(f"✅ Debug: {debug['active_patients']} active patients")
            
            # Test patients
            print("Testing patients...")
            response = requests.get("http://localhost:8000/patients?limit=100", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Patients: {data['total']} total")
                
                if data['patients']:
                    print("   Patient list:")
                    for p in data['patients']:
                        print(f"   - {p['patient_id']}: {p['first_name']} {p['last_name']}")
                else:
                    print("   No patients returned")
                    print(f"   Raw data: {data}")
            else:
                print(f"❌ Patients failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print(f"❌ Health failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        print("Stopping backend...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()