#!/usr/bin/env python3
"""
Quick test for backend
"""

import requests
import time

def test_backend():
    """Quick test"""
    print("🔍 Testing backend...")
    
    try:
        # Test health
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health: OK")
        else:
            print(f"❌ Health: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health error: {e}")
        return False
    
    try:
        # Test patients
        response = requests.get("http://localhost:8000/patients/?limit=100", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients: Found {data['total']} patients")
            return True
        else:
            print(f"❌ Patients: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Patients error: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Quick Backend Test")
    print("=" * 20)
    
    # Wait for server
    print("⏳ Waiting for server...")
    time.sleep(3)
    
    if test_backend():
        print("🎉 Backend is working!")
    else:
        print("❌ Backend has issues")
        print("Make sure to start: python start_backend_now.py")