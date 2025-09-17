#!/usr/bin/env python3
"""
Simple backend test to find the issue
"""

import subprocess
import time
import requests
import sys

def main():
    print("🔍 Simple Backend Test")
    print("=" * 30)
    
    # Kill any existing processes
    try:
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
        time.sleep(2)
    except:
        pass
    
    print("Starting backend...")
    
    # Start backend with minimal logging
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ])
    
    # Wait longer for startup
    print("Waiting for startup...")
    time.sleep(8)
    
    try:
        # Simple health test
        print("Testing health...")
        response = requests.get("http://127.0.0.1:8000/health", timeout=10)
        
        if response.status_code == 200:
            print("✅ Backend is running!")
            health = response.json()
            print(f"   Version: {health['version']}")
            
            # Test patients
            print("\nTesting patients...")
            response = requests.get("http://127.0.0.1:8000/patients?limit=100", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Patients working! Found {data['total']} patients")
                
                if data['patients']:
                    for patient in data['patients']:
                        print(f"   - {patient['patient_id']}: {patient['first_name']} {patient['last_name']}")
                else:
                    print("   No patients in response")
            else:
                print(f"❌ Patients failed: {response.status_code}")
                print(f"   Error: {response.text}")
        else:
            print(f"❌ Health failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        print("\nStopping backend...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()