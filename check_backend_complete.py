#!/usr/bin/env python3
"""
Complete backend check - patients, database, and all endpoints
"""

import subprocess
import time
import requests
import sys
import sqlite3

def check_database_directly():
    """Check database directly"""
    print("🗄️ Checking database directly...")
    
    try:
        conn = sqlite3.connect('kiro_mini.db')
        cursor = conn.cursor()
        
        # Check if patients table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Patients table exists")
            
            # Check total patients
            cursor.execute("SELECT COUNT(*) FROM patients")
            total = cursor.fetchone()[0]
            print(f"   Total patients in DB: {total}")
            
            # Check active patients
            cursor.execute("SELECT COUNT(*) FROM patients WHERE active = 1")
            active = cursor.fetchone()[0]
            print(f"   Active patients in DB: {active}")
            
            # Show sample patients
            cursor.execute("SELECT patient_id, first_name, last_name, active, date_of_birth, gender FROM patients LIMIT 5")
            patients = cursor.fetchall()
            
            print("   Sample patients:")
            for p in patients:
                print(f"     - {p[0]}: {p[1]} {p[2]} (active: {p[3]}, DOB: {p[4]}, gender: {p[5]})")
            
            return active > 0
        else:
            print("❌ Patients table does not exist!")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        conn.close()

def test_backend_endpoints():
    """Test all backend endpoints"""
    print("\n🌐 Testing backend endpoints...")
    
    # Start backend
    print("Starting backend...")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "fixed_upload_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(6)
    
    try:
        # Test 1: Health check
        print("\n1. Health check...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health: {health['status']} (v{health['version']})")
        else:
            print(f"❌ Health failed: {response.status_code}")
            return False
        
        # Test 2: Debug endpoint
        print("\n2. Debug endpoint...")
        response = requests.get("http://localhost:8000/debug/patients/count", timeout=5)
        if response.status_code == 200:
            debug = response.json()
            print(f"✅ Debug: {debug['active_patients']} active, {debug['total_patients']} total")
        else:
            print(f"❌ Debug failed: {response.status_code}")
        
        # Test 3: Patients endpoint (your frontend format)
        print("\n3. Patients endpoint (limit=100)...")
        response = requests.get("http://localhost:8000/patients?limit=100", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Patients API working!")
            print(f"   Total: {data.get('total', 'missing')}")
            print(f"   Returned: {len(data.get('patients', []))}")
            print(f"   Page: {data.get('page', 'missing')}")
            print(f"   Per page: {data.get('per_page', 'missing')}")
            
            if data.get('patients'):
                print("\n   Patient details:")
                for i, patient in enumerate(data['patients'][:3]):
                    print(f"   {i+1}. ID: {patient.get('patient_id', 'missing')}")
                    print(f"      Name: {patient.get('first_name', 'missing')} {patient.get('last_name', 'missing')}")
                    print(f"      Active: {patient.get('active', 'missing')}")
                    print(f"      DOB: {patient.get('date_of_birth', 'missing')}")
            else:
                print("   ⚠️  No patients in response!")
                print(f"   Raw response: {data}")
        else:
            print(f"❌ Patients endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 4: Alternative format
        print("\n4. Patients endpoint (per_page format)...")
        response = requests.get("http://localhost:8000/patients?per_page=20&page=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alternative format: {data.get('total', 0)} patients")
        else:
            print(f"❌ Alternative format failed: {response.status_code}")
        
        # Test 5: Specific patient
        print("\n5. Specific patient (PAT001)...")
        response = requests.get("http://localhost:8000/patients/PAT001", timeout=5)
        if response.status_code == 200:
            patient = response.json()
            print(f"✅ PAT001 found: {patient.get('first_name', 'missing')} {patient.get('last_name', 'missing')}")
        else:
            print(f"❌ PAT001 not found: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test 6: Studies
        print("\n6. Studies endpoint...")
        response = requests.get("http://localhost:8000/patients/PAT001/studies", timeout=5)
        if response.status_code == 200:
            studies = response.json()
            print(f"✅ Studies: {studies.get('total_studies', 0)} found")
        else:
            print(f"❌ Studies failed: {response.status_code}")
        
        print("\n🎯 Backend check complete!")
        print("Press Ctrl+C to stop backend...")
        
        # Keep running for testing
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 Stopping backend...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        process.terminate()
        process.wait()

def main():
    print("🏥 COMPLETE BACKEND CHECK")
    print("=" * 50)
    
    # Check database first
    db_has_patients = check_database_directly()
    
    if not db_has_patients:
        print("\n❌ No patients in database!")
        print("Let me add a test patient...")
        
        try:
            conn = sqlite3.connect('kiro_mini.db')
            cursor = conn.cursor()
            
            # Add test patient
            cursor.execute("""
                INSERT OR REPLACE INTO patients 
                (id, patient_id, first_name, last_name, date_of_birth, gender, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'test-id-001',
                'PAT001', 
                'John', 
                'Doe', 
                '1985-05-15', 
                'M', 
                1, 
                '2025-09-17 10:00:00'
            ))
            
            conn.commit()
            conn.close()
            
            print("✅ Added test patient PAT001")
            
        except Exception as e:
            print(f"❌ Failed to add test patient: {e}")
    
    # Test backend
    test_backend_endpoints()

if __name__ == "__main__":
    main()