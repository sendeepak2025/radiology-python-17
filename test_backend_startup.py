#!/usr/bin/env python3
"""
Test if backend can start and respond properly
"""

import subprocess
import time
import requests
import threading
import sys
import os

def test_backend_import():
    """Test if backend can be imported"""
    try:
        print("🔍 Testing backend import...")
        result = subprocess.run([
            sys.executable, "-c", 
            "from fixed_backend import app; print('✅ Backend import successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Backend import: OK")
            return True
        else:
            print(f"❌ Backend import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Backend import error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        print("🔍 Testing database connection...")
        result = subprocess.run([
            sys.executable, "-c", 
            """
import sqlite3
conn = sqlite3.connect('kiro_mini.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM patients WHERE active = 1')
count = cursor.fetchone()[0]
print(f'Active patients: {count}')
conn.close()
"""
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ Database: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Database error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_uvicorn_start():
    """Test if uvicorn can start the backend"""
    try:
        print("🔍 Testing uvicorn startup...")
        
        # Start uvicorn in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "fixed_backend:app",
            "--host", "127.0.0.1",
            "--port", "8001",  # Use different port for testing
            "--log-level", "error"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        time.sleep(5)
        
        # Test if server responds
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ Uvicorn startup: OK")
                success = True
            else:
                print(f"❌ Server responded with: {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Server not responding: {e}")
            success = False
        
        # Kill the test process
        process.terminate()
        process.wait()
        
        return success
        
    except Exception as e:
        print(f"❌ Uvicorn test error: {e}")
        return False

def test_patients_endpoint():
    """Test the specific patients endpoint that was failing"""
    try:
        print("🔍 Testing patients endpoint...")
        
        # Start uvicorn in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "fixed_backend:app",
            "--host", "127.0.0.1",
            "--port", "8002",  # Use different port for testing
            "--log-level", "error"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        time.sleep(5)
        
        # Test the specific endpoint that was failing
        try:
            response = requests.get("http://127.0.0.1:8002/patients/?limit=100", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Patients endpoint: Found {data['total']} patients")
                success = True
            else:
                print(f"❌ Patients endpoint failed: {response.status_code}")
                print(f"Response: {response.text}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Patients endpoint error: {e}")
            success = False
        
        # Kill the test process
        process.terminate()
        process.wait()
        
        return success
        
    except Exception as e:
        print(f"❌ Patients endpoint test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🏥 Backend System Check")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Backend Import", test_backend_import),
        ("Uvicorn Startup", test_uvicorn_start),
        ("Patients Endpoint", test_patients_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 System is working perfectly!")
        print("✅ Ready to start with: python start_backend_now.py")
    else:
        print("⚠️  Some issues found. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()