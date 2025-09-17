#!/usr/bin/env python3
"""
Direct test of backend functionality
"""

import sqlite3
from pathlib import Path

def test_database():
    """Test database directly"""
    print("🗄️ Testing Database...")
    
    try:
        conn = sqlite3.connect('kiro_mini.db')
        cursor = conn.cursor()
        
        # Get patients
        cursor.execute("SELECT patient_id, first_name, last_name, active FROM patients")
        patients = cursor.fetchall()
        
        print(f"✅ Found {len(patients)} patients:")
        for p in patients:
            print(f"   - {p[0]}: {p[1]} {p[2]} (active: {p[3]})")
        
        conn.close()
        return len(patients) > 0
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_uploads():
    """Test uploads directory"""
    print("\n📁 Testing Uploads...")
    
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        dicom_files = []
        for patient_dir in uploads_dir.iterdir():
            if patient_dir.is_dir():
                for file_path in patient_dir.iterdir():
                    if file_path.suffix.lower() in ['.dcm', '.dicom']:
                        dicom_files.append(f"{patient_dir.name}/{file_path.name}")
        
        print(f"✅ Found {len(dicom_files)} DICOM files:")
        for f in dicom_files[:5]:  # Show first 5
            print(f"   - {f}")
        
        return len(dicom_files) > 0
    else:
        print("❌ No uploads directory")
        return False

def test_backend_import():
    """Test backend import"""
    print("\n🔧 Testing Backend Import...")
    
    try:
        from final_working_backend import app
        print("✅ Backend imports successfully")
        return True
    except Exception as e:
        print(f"❌ Backend import error: {e}")
        return False

def main():
    print("🏥 DIRECT SYSTEM TEST")
    print("=" * 30)
    
    db_ok = test_database()
    uploads_ok = test_uploads()
    backend_ok = test_backend_import()
    
    print(f"\n📊 Results:")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print(f"   Uploads: {'✅' if uploads_ok else '❌'}")
    print(f"   Backend: {'✅' if backend_ok else '❌'}")
    
    if db_ok and backend_ok:
        print(f"\n🎯 System components are working!")
        print(f"✅ You have patients in database")
        print(f"✅ Backend can be imported")
        if uploads_ok:
            print(f"✅ You have DICOM files for studies")
        
        print(f"\n🚀 Try starting with:")
        print(f"   python -m uvicorn final_working_backend:app --host 0.0.0.0 --port 8000 --reload")
    else:
        print(f"\n❌ System has issues that need fixing")

if __name__ == "__main__":
    main()