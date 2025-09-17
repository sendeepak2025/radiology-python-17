#!/usr/bin/env python3
"""
Quick test for the backend
"""

import requests
import time
import json

def test_backend():
    """Test the backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing backend...")
    
    # Test health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check: OK")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test patients endpoint with limit (your frontend format)
    try:
        response = requests.get(f"{base_url}/patients/?limit=100", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients endpoint: Found {data['total']} patients")
            if data['patients']:
                patient = data['patients'][0]
                print(f"   First patient: {patient['patient_id']} - {patient['first_name']} {patient['last_name']}")
            return True
        else:
            print(f"❌ Patients endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Patients endpoint error: {e}")
        return False

def wait_for_server(timeout=30):
    """Wait for server to start"""
    print("⏳ Waiting for server to start...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\n❌ Server failed to start within timeout")
    return False

if __name__ == "__main__":
    if wait_for_server():
        test_backend()
    else:
        print("Please start the backend first with: python start_now.py")