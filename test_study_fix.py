"""
Test script to verify study UID fix
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_upload_and_retrieve():
    print("Testing Upload and Study Retrieval Fix...")
    print("=" * 50)
    
    # Test 1: Check health
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health Check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Version: {data.get('version', 'unknown')}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return
    
    # Test 2: Get patients
    try:
        response = requests.get(f"{BASE_URL}/patients")
        print(f"✅ Get Patients: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            patients = data.get('patients', [])
            print(f"   Found {len(patients)} patients")
            if patients:
                patient_id = patients[0]['patient_id']
                print(f"   Using patient: {patient_id}")
            else:
                print("   No patients found!")
                return
    except Exception as e:
        print(f"❌ Get Patients Failed: {e}")
        return
    
    # Test 3: Get all studies
    try:
        response = requests.get(f"{BASE_URL}/studies")
        print(f"✅ Get All Studies: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            print(f"   Found {len(studies)} studies")
            
            # Test specific study if available
            if studies:
                study_uid = studies[0]['study_uid']
                print(f"   Testing study UID: {study_uid}")
                
                # Test 4: Get specific study
                study_response = requests.get(f"{BASE_URL}/studies/{study_uid}")
                print(f"✅ Get Specific Study: {study_response.status_code}")
                if study_response.status_code == 200:
                    study_data = study_response.json()
                    print(f"   Study found: {study_data.get('study_description', 'No description')}")
                else:
                    print(f"   Study response: {study_response.text}")
            else:
                print("   No studies found - upload a DICOM file first")
                
    except Exception as e:
        print(f"❌ Get Studies Failed: {e}")
    
    # Test 5: Get patient studies
    try:
        response = requests.get(f"{BASE_URL}/patients/{patient_id}/studies")
        print(f"✅ Get Patient Studies: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            print(f"   Found {len(studies)} studies for patient {patient_id}")
    except Exception as e:
        print(f"❌ Get Patient Studies Failed: {e}")
    
    print("=" * 50)
    print("Test completed!")
    print("\nTo test upload:")
    print("1. Go to frontend")
    print("2. Upload a DICOM file")
    print("3. Check if study appears in list")
    print("4. Click on study to verify it loads")

if __name__ == "__main__":
    test_upload_and_retrieve()