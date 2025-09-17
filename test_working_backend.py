#!/usr/bin/env python3
"""
Test the working backend
"""

import subprocess
import time
import requests
import sys
import threading

def test_full_backend():
    """Test the complete backend functionality"""
    print("🚀 Testing Complete Backend...")
    
    # Start the backend
    print("Starting backend on port 8003...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_backend:app",
        "--host", "127.0.0.1",
        "--port", "8003",
        "--log-level", "info"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    print("⏳ Waiting for backend to start...")
    time.sleep(8)
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8003/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: OK")
            health_data = response.json()
            print(f"   Status: {health_data['status']}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test patients endpoint (the one that was failing)
        print("🔍 Testing patients endpoint with limit=100...")
        response = requests.get("http://127.0.0.1:8003/patients/?limit=100", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients endpoint: OK")
            print(f"   Total patients: {data['total']}")
            print(f"   Returned patients: {len(data['patients'])}")
            print(f"   Page: {data['page']}")
            print(f"   Per page: {data['per_page']}")
            
            if data['patients']:
                patient = data['patients'][0]
                print(f"   First patient: {patient['patient_id']} - {patient['first_name']} {patient['last_name']}")
        else:
            print(f"❌ Patients endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Test patients endpoint with per_page format
        print("🔍 Testing patients endpoint with per_page format...")
        response = requests.get("http://127.0.0.1:8003/patients?per_page=10&page=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Per_page format: OK")
            print(f"   Total patients: {data['total']}")
        else:
            print(f"❌ Per_page format failed: {response.status_code}")
        
        # Test specific patient
        print("🔍 Testing specific patient endpoint...")
        response = requests.get("http://127.0.0.1:8003/patients/PAT001", timeout=5)
        if response.status_code == 200:
            patient = response.json()
            print(f"✅ Specific patient: OK")
            print(f"   Patient: {patient['patient_id']} - {patient['first_name']} {patient['last_name']}")
        else:
            print(f"❌ Specific patient failed: {response.status_code}")
        
        # Test debug endpoint
        print("🔍 Testing debug endpoint...")
        response = requests.get("http://127.0.0.1:8003/debug/patients/count", timeout=5)
        if response.status_code == 200:
            debug_data = response.json()
            print(f"✅ Debug endpoint: OK")
            print(f"   Total patients: {debug_data['total_patients']}")
            print(f"   Active patients: {debug_data['active_patients']}")
        else:
            print(f"❌ Debug endpoint failed: {response.status_code}")
        
        print("\n🎉 All tests passed! Backend is working perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    
    finally:
        # Clean up
        print("🛑 Stopping test backend...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("🏥 Complete Backend Test")
    print("=" * 30)
    
    success = test_full_backend()
    
    if success:
        print("\n✅ Backend is working perfectly!")
        print("🚀 Ready to start with: python start_backend_now.py")
        print("🌐 Your frontend should work with: http://localhost:8000/patients/?limit=100")
    else:
        print("\n❌ Backend has issues")