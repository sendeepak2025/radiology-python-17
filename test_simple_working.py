#!/usr/bin/env python3
"""
Test simple working backend
"""

import subprocess
import time
import requests
import sys

def main():
    print("🔍 Testing Simple Working Backend")
    print("=" * 40)
    
    # Kill existing
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    time.sleep(1)
    
    print("Starting simple backend...")
    
    # Start simple backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "working_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    time.sleep(3)
    
    try:
        # Test health
        print("Testing health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Health OK")
            
            # Test patients
            print("Testing patients...")
            response = requests.get("http://localhost:8000/patients?limit=100", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS! Found {data['total']} patients")
                
                if data['patients']:
                    print("\n👥 Patient List:")
                    for p in data['patients']:
                        print(f"   - {p['patient_id']}: {p['first_name']} {p['last_name']}")
                        print(f"     DOB: {p['date_of_birth']}, Gender: {p['gender']}")
                    
                    print(f"\n🎉 PATIENTS ARE WORKING!")
                    print(f"🌐 Your frontend can connect to: http://localhost:8000/patients?limit=100")
                    print(f"📊 API Response: {data['total']} patients returned")
                    
                    print("\nBackend is ready! Press Ctrl+C to stop...")
                    while True:
                        time.sleep(1)
                else:
                    print("❌ No patients in response")
                    print(f"Response: {data}")
            else:
                print(f"❌ Patients failed: {response.status_code}")
                print(f"Response: {response.text}")
        else:
            print(f"❌ Health failed: {response.status_code}")
    
    except KeyboardInterrupt:
        print("\n👋 Stopping backend...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()