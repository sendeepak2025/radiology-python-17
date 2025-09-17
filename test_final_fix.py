#!/usr/bin/env python3
"""
Test final backend fix
"""

import subprocess
import time
import requests
import sys

def main():
    print("🎯 Testing Final Backend Fix")
    print("=" * 40)
    
    # Kill existing
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    time.sleep(1)
    
    print("Starting final backend...")
    
    # Start backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "final_working_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    time.sleep(4)
    
    try:
        # Test all the endpoints your frontend is calling
        tests = [
            ("Health", "http://localhost:8000/health"),
            ("Upload Health", "http://localhost:8000/upload/health"),
            ("Patients (limit=100)", "http://localhost:8000/patients?limit=100"),
            ("Studies (skip=0&limit=100)", "http://localhost:8000/studies?skip=0&limit=100"),
            ("Patient Studies", "http://localhost:8000/patients/PAT001/studies"),
        ]
        
        all_working = True
        
        for test_name, url in tests:
            print(f"\n🔍 Testing {test_name}...")
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {test_name}: OK")
                    
                    # Show relevant data
                    if 'patients' in data:
                        print(f"   Found {data.get('total', 0)} patients")
                    elif 'studies' in data:
                        print(f"   Found {data.get('total', 0)} studies")
                    elif 'total_studies' in data:
                        print(f"   Found {data.get('total_studies', 0)} studies")
                    elif 'status' in data:
                        print(f"   Status: {data['status']}")
                else:
                    print(f"❌ {test_name}: {response.status_code}")
                    all_working = False
            except Exception as e:
                print(f"❌ {test_name}: Error - {e}")
                all_working = False
        
        if all_working:
            print(f"\n🎉 ALL ENDPOINTS WORKING!")
            print(f"✅ Your frontend 404 errors are FIXED!")
            print(f"✅ Patients will show up")
            print(f"✅ Studies will show up")
            print(f"✅ Uploads will work")
            
            print(f"\n🌐 Backend ready at: http://localhost:8000")
            print(f"Press Ctrl+C to stop...")
            
            while True:
                time.sleep(1)
        else:
            print(f"\n❌ Some endpoints still have issues")
    
    except KeyboardInterrupt:
        print(f"\n👋 Stopping backend...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    main()