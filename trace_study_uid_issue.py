"""
Comprehensive trace to find where the wrong study UID is coming from
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def trace_study_uid_flow():
    print("🔍 Tracing Study UID Flow...")
    print("=" * 70)
    
    # 1. Check current metadata
    print("1. Current Backend Metadata:")
    try:
        response = requests.get(f"{BASE_URL}/debug/studies")
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Total Studies: {data['total_studies']}")
            for study in data['studies']:
                print(f"   📋 UID: {study['study_uid']}")
                print(f"      Patient: {study['patient_id']}")
                print(f"      File: {study['filename']}")
                print(f"      Created: {study['created_at']}")
                print()
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Test /studies endpoint
    print("2. Testing /studies endpoint:")
    try:
        response = requests.get(f"{BASE_URL}/studies")
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            print(f"   ✅ Found {len(studies)} studies")
            for i, study in enumerate(studies):
                print(f"   📋 Study {i+1}: {study.get('study_uid')}")
                print(f"      Description: {study.get('study_description')}")
                print(f"      Patient: {study.get('patient_id')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Test patient studies
    print("3. Testing patient studies:")
    for patient_id in ['PAT001', 'PAT002']:
        try:
            response = requests.get(f"{BASE_URL}/patients/{patient_id}/studies")
            if response.status_code == 200:
                data = response.json()
                studies = data.get('studies', [])
                print(f"   👤 {patient_id}: {len(studies)} studies")
                for study in studies:
                    print(f"      📋 {study.get('study_uid')}")
            else:
                print(f"   👤 {patient_id}: No studies or error")
        except Exception as e:
            print(f"   👤 {patient_id}: Error - {e}")
    
    # 4. Test the problematic UID directly
    problematic_uid = "1.2.840.113619.2.5.1762583153.215519.978957063.78"
    print(f"4. Testing problematic UID: {problematic_uid}")
    try:
        response = requests.get(f"{BASE_URL}/studies/{problematic_uid}")
        print(f"   Status: {response.status_code}")
        data = response.json()
        if 'error' in data:
            print(f"   ❌ Error: {data['error']}")
            if 'available_studies' in data:
                print(f"   📋 Available studies: {len(data['available_studies'])}")
                for uid in data['available_studies']:
                    print(f"      - {uid}")
        else:
            print(f"   ✅ Found study: {data.get('study_description')}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 Analysis:")
    print("The problematic UID '1.2.840.113619.2.5.1762583153.215519.978957063.78'")
    print("is NOT in the backend metadata. This suggests:")
    print("1. Frontend might be caching old data")
    print("2. Frontend might be generating UIDs differently")
    print("3. There might be a race condition in the upload/navigation flow")
    print("\n🔧 Recommendations:")
    print("1. Clear browser cache/localStorage")
    print("2. Check if frontend is using correct study UID from upload response")
    print("3. Verify navigation happens after upload completes")

if __name__ == "__main__":
    trace_study_uid_flow()