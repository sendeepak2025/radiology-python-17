"""
Test script to verify the final backend is working properly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, description):
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"✅ {description}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if endpoint == "/patients":
                print(f"   Found {data.get('total', 0)} patients")
            elif endpoint == "/studies":
                print(f"   Found {data.get('total', 0)} studies")
        return True
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False

def main():
    print("Testing Final Backend Endpoints...")
    print("=" * 50)
    
    # Test all endpoints
    tests = [
        ("/health", "Health Check"),
        ("/upload/health", "Upload Health Check"),
        ("/patients", "Get All Patients"),
        ("/patients/PAT001", "Get Specific Patient"),
        ("/studies", "Get All Studies"),
        ("/patients/PAT001/studies", "Get Patient Studies")
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, description in tests:
        if test_endpoint(endpoint, description):
            passed += 1
    
    print("=" * 50)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check the backend server.")

if __name__ == "__main__":
    main()