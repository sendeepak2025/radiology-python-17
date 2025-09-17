"""
Script to diagnose and fix the study UID mismatch issue
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_study_endpoints():
    print("🔍 Diagnosing Study UID Issue...")
    print("=" * 60)
    
    # 1. Check what studies are available
    try:
        response = requests.get(f"{BASE_URL}/debug/studies")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available Studies: {data['total_studies']}")
            for study in data['studies']:
                print(f"   📋 UID: {study['study_uid']}")
                print(f"      Patient: {study['patient_id']}")
                print(f"      File: {study['filename']}")
                print(f"      Description: {study['study_description']}")
                print()
        else:
            print(f"❌ Debug studies failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking studies: {e}")
    
    # 2. Check uploaded files
    try:
        response = requests.get(f"{BASE_URL}/debug/files")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Uploaded Files: {data['total_files']}")
            for file_info in data['files']:
                print(f"   📁 {file_info['patient_id']}/{file_info['filename']}")
                print(f"      Size: {file_info['file_size']} bytes")
                print(f"      Created: {file_info['created']}")
                print()
        else:
            print(f"❌ Debug files failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking files: {e}")
    
    # 3. Test the problematic study UID
    problematic_uid = "1.2.840.113619.2.5.1762583153.215519.978957063.78"
    print(f"🔍 Testing problematic UID: {problematic_uid}")
    try:
        response = requests.get(f"{BASE_URL}/studies/{problematic_uid}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found study: {data.get('study_description', 'No description')}")
        else:
            data = response.json()
            print(f"   ❌ Error: {data.get('error', 'Unknown error')}")
            if 'available_studies' in data:
                print(f"   Available studies: {data['available_studies']}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # 4. Test all studies endpoint
    print("\n🔍 Testing /studies endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/studies")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total']} studies")
            for study in data['studies']:
                print(f"      📋 {study['study_uid']} - {study['study_description']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🔧 Recommendations:")
    print("1. Upload a new DICOM file to generate proper study UID")
    print("2. Check if frontend is using correct study UIDs from /studies endpoint")
    print("3. Verify that study UIDs match between frontend and backend")

if __name__ == "__main__":
    test_study_endpoints()