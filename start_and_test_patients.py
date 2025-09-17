#!/usr/bin/env python3
"""
Start backend and test patients endpoint
"""

import subprocess
import time
import requests
import sys

def main():
    print("🚀 Starting fixed backend and testing patients...")
    
    # Start backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])
    
    # Wait for startup
    time.sleep(4)
    
    try:
        # Test health
        print("🔍 Testing health...")
        r = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Health: {r.status_code}")
        
        # Test patients endpoint (your frontend format)
        print("🔍 Testing patients endpoint...")
        r = requests.get("http://localhost:8000/patients?limit=100", timeout=10)
        print(f"Patients status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Found {data['total']} patients")
            print(f"   Returned: {len(data['patients'])} patients")
            
            for patient in data['patients']:
                print(f"   - {patient['patient_id']}: {patient['first_name']} {patient['last_name']}")
        else:
            print(f"❌ Error: {r.text}")
        
        # Test debug endpoint
        print("🔍 Testing debug endpoint...")
        r = requests.get("http://localhost:8000/debug/patients/count", timeout=5)
        if r.status_code == 200:
            debug = r.json()
            print(f"Debug: {debug['active_patients']} active patients")
        
        print("\n✅ Backend is ready!")
        print("🌐 Your frontend should now show patients at: http://localhost:8000/patients?limit=100")
        print("\nPress Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()