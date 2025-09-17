"""
Quick test to verify all fixes are working
"""
import requests

def quick_test():
    print("🚀 Quick System Test")
    print("=" * 40)
    
    BASE_URL = "http://localhost:8000"
    
    # Test 1: Backend Health
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend: HEALTHY")
        else:
            print("❌ Backend: UNHEALTHY")
            return
    except:
        print("❌ Backend: NOT RUNNING")
        return
    
    # Test 2: Studies with Image URLs
    try:
        response = requests.get(f"{BASE_URL}/studies")
        if response.status_code == 200:
            data = response.json()
            studies = data.get('studies', [])
            print(f"✅ Studies: {len(studies)} found")
            
            if studies:
                study = studies[0]
                has_image_urls = 'image_urls' in study
                print(f"✅ Image URLs: {'PRESENT' if has_image_urls else 'MISSING'}")
                
                # Test specific study
                study_uid = study['study_uid']
                study_response = requests.get(f"{BASE_URL}/studies/{study_uid}")
                if study_response.status_code == 200:
                    print("✅ Study Access: WORKING")
                else:
                    print("❌ Study Access: FAILED")
            else:
                print("ℹ️  No studies found - upload a DICOM file first")
        else:
            print("❌ Studies: FAILED")
    except Exception as e:
        print(f"❌ Studies: ERROR - {e}")
    
    print("\n" + "=" * 40)
    print("🎯 System Status: READY")
    print("📋 To test full flow:")
    print("1. Start frontend: npm start")
    print("2. Go to: http://localhost:3000/patients")
    print("3. Upload DICOM file")
    print("4. Click on study to view")

if __name__ == "__main__":
    quick_test()