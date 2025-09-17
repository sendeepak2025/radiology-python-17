#!/usr/bin/env python3
"""
Quick test to check patients are working
"""

import subprocess
import time
import requests
import sys
import sqlite3

def check_database():
    """Check database has patients"""
    print("🗄️ Checking database...")
    try:
        conn = sqlite3.connect('kiro_mini.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE active = 1")
        count = cursor.fetchone()[0]
        print(f"✅ Database has {count} active patients")
        
        cursor.execute("SELECT patient_id, first_name, last_name FROM patients WHERE active = 1 LIMIT 3")
        patients = cursor.fetchall()
        for p in patients:
            print(f"   - {p[0]}: {p[1]} {p[2]}")
        
        conn.close()
        return count > 0
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_backend():
    """Test backend quickly"""
    print("\n🚀 Testing backend...")
    
    # Kill existing
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    time.sleep(1)
    
    # Start minimal backend
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "minimal_working_backend:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    time.sleep(4)
    
    try:
        # Quick test
        response = requests.get("http://localhost:8000/patients?limit=100", timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend working! Found {data['total']} patients")
            
            if data['patients']:
                for p in data['patients']:
                    print(f"   - {p['patient_id']}: {p['first_name']} {p['last_name']}")
                
                print(f"\n🎉 PATIENTS ARE WORKING!")
                print(f"✅ Database: {data['total']} patients")
                print(f"✅ API: Returning patient data")
                print(f"✅ Frontend can now connect to: http://localhost:8000/patients?limit=100")
                
                print("\nPress Ctrl+C to stop...")
                while True:
                    time.sleep(1)
            else:
                print("❌ No patients in API response")
        else:
            print(f"❌ API failed: {response.status_code}")
    
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        process.terminate()

def main():
    print("🏥 QUICK PATIENT TEST")
    print("=" * 30)
    
    # Check database first
    if check_database():
        test_backend()
    else:
        print("❌ No patients in database!")

if __name__ == "__main__":
    main()