#!/usr/bin/env python3
"""
Check if backend is working and patients are showing
"""

import subprocess
import time
import requests
import sys

def test_backend():
    print("🔍 Checking Backend & Patients...")
    print("=" * 40)
    
    # Start backend
    print("Starting backend...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(5)
    
    try:
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health: {health['status']} (v{health['version']})")
        else:
            print(f"❌ Health failed: {response.status_code}")
            return False
        
        # Test 2: Database debug
        print("\n2. Testing database debug...")
        response = requests.get("http://localhost:8000/debug/patients/count", timeout=5)
        if response.status_code == 200:
            debug = response.json()
            print(f"✅ Database: {debug['active_patients']} active patients, {debug['total_patients']} total")
        else:
            print(f"❌ Debug failed: {response.status_code}")
        
        # Test 3: Patients endpoint (your frontend format)
        print("\n3. Testing patients endpoint (limit=100)...")
        response = requests.get("http://localhost:8000/patients?limit=100", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients endpoint working!")
            print(f"   Total patients: {data['total']}")
            print(f"   Returned patients: {len(data['patients'])}")
            print(f"   Page: {data['page']}")
            print(f"   Per page: {data['per_page']}")
            
            if data['patients']:
                print("\n   Patient details:")
                for i, patient in enumerate(data['patients'][:3]):  # Show first 3
                    print(f"   {i+1}. {patient['patient_id']}: {patient['first_name']} {patient['last_name']}")
                    print(f"      DOB: {patient['date_of_birth']}, Gender: {patient['gender']}")
                    print(f"      Active: {patient['active']}")
            else:
                print("   ⚠️  No patients returned!")
        else:
            print(f"❌ Patients endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 4: Alternative patients format
        print("\n4. Testing patients endpoint (per_page format)...")
        response = requests.get("http://localhost:8000/patients?per_page=20&page=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alternative format: Found {data['total']} patients")
        else:
            print(f"❌ Alternative format failed: {response.status_code}")
        
        # Test 5: Check specific patient
        print("\n5. Testing specific patient (PAT001)...")
        response = requests.get("http://localhost:8000/patients/PAT001", timeout=5)
        if response.status_code == 200:
            patient = response.json()
            print(f"✅ PAT001 found: {patient['first_name']} {patient['last_name']}")
        else:
            print(f"❌ PAT001 not found: {response.status_code}")
        
        # Test 6: Check database directly
        print("\n6. Checking database directly...")
        try:
            import sqlite3
            conn = sqlite3.connect('kiro_mini.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM patients")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM patients WHERE active = 1")
            active = cursor.fetchone()[0]
            
            cursor.execute("SELECT patient_id, first_name, last_name, active FROM patients LIMIT 5")
            patients = cursor.fetchall()
            
            print(f"✅ Direct DB check: {total} total, {active} active patients")
            print("   Sample patients:")
            for p in patients:
                print(f"   - {p[0]}: {p[1]} {p[2]} (active: {p[3]})")
            
            conn.close()
        except Exception as e:
            print(f"❌ Direct DB check failed: {e}")
        
        print("\n🎯 Backend is ready! Try your frontend now.")
        print("Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 Stopping backend...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_backend()