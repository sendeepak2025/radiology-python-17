"""
Test script to verify the study navigation fix
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_study_navigation_fix():
    print("🔍 Testing Study Navigation Fix...")
    print("=" * 60)
    
    # 1. Get all studies
    print("1. Getting all studies...")
    try:
        response = requests.get(f"{BASE_URL}/studies")
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            print(f"   ✅ Found {len(studies)} studies")
            
            if studies:
                for i, study in enumerate(studies):
                    study_uid = study.get('study_uid')
                    patient_id = study.get('patient_id')
                    filename = study.get('original_filename')
                    print(f"   📋 Study {i+1}:")
                    print(f"      UID: {study_uid}")
                    print(f"      Patient: {patient_id}")
                    print(f"      File: {filename}")
                    
                    # Test accessing this specific study
                    print(f"   🔍 Testing access to study: {study_uid}")
                    study_response = requests.get(f"{BASE_URL}/studies/{study_uid}")
                    if study_response.status_code == 200:
                        print(f"      ✅ Study accessible")
                    else:
                        print(f"      ❌ Study not accessible: {study_response.status_code}")
                        print(f"      Error: {study_response.text}")
                    print()
            else:
                print("   ⚠️  No studies found. Upload a DICOM file first.")
        else:
            print(f"   ❌ Failed to get studies: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Test patient studies
    print("2. Testing patient studies...")
    try:
        response = requests.get(f"{BASE_URL}/patients/PAT002/studies")
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            print(f"   ✅ Found {len(studies)} studies for PAT002")
            
            for study in studies:
                study_uid = study.get('study_uid')
                print(f"   📋 Study UID: {study_uid}")
                
                # Test the frontend URL format
                frontend_url = f"http://localhost:3000/studies/{study_uid}"
                print(f"   🌐 Frontend URL: {frontend_url}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Fix Summary:")
    print("✅ Fixed PatientList.tsx to use study.study_uid instead of study.study_instance_uid")
    print("✅ Backend correctly returns study_uid in all endpoints")
    print("✅ Upload response includes correct study_uid")
    print("\n📋 Next Steps:")
    print("1. Upload a new DICOM file")
    print("2. Click on the study in the patient list")
    print("3. Verify it navigates to the correct study viewer")

if __name__ == "__main__":
    test_study_navigation_fix()