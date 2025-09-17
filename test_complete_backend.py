"""
Test the complete backend with all functions
"""
import requests
import json
import sys
from pathlib import Path

def test_backend_functions():
    print("🧪 Testing Complete Backend Functions")
    print("=" * 50)
    
    BASE_URL = "http://localhost:8000"
    
    # Test 1: Health checks
    print("1. Testing health endpoints...")
    try:
        health = requests.get(f"{BASE_URL}/health")
        upload_health = requests.get(f"{BASE_URL}/upload/health")
        
        if health.status_code == 200 and upload_health.status_code == 200:
            print("   ✅ Health checks: PASSED")
            print(f"   📊 Version: {health.json().get('version')}")
        else:
            print("   ❌ Health checks: FAILED")
            return False
    except Exception as e:
        print(f"   ❌ Health checks: ERROR - {e}")
        return False
    
    # Test 2: Patient endpoints
    print("\n2. Testing patient endpoints...")
    try:
        patients = requests.get(f"{BASE_URL}/patients")
        if patients.status_code == 200:
            data = patients.json()
            print(f"   ✅ Patients endpoint: {data.get('total', 0)} patients found")
        else:
            print("   ❌ Patients endpoint: FAILED")
    except Exception as e:
        print(f"   ❌ Patients endpoint: ERROR - {e}")
    
    # Test 3: Studies endpoints
    print("\n3. Testing studies endpoints...")
    try:
        studies = requests.get(f"{BASE_URL}/studies")
        if studies.status_code == 200:
            data = studies.json()
            studies_list = data.get('studies', [])
            print(f"   ✅ Studies endpoint: {len(studies_list)} studies found")
            
            # Test individual study if available
            if studies_list:
                study_uid = studies_list[0]['study_uid']
                study_detail = requests.get(f"{BASE_URL}/studies/{study_uid}")
                if study_detail.status_code == 200:
                    print("   ✅ Individual study access: WORKING")
                    
                    # Check for processed images
                    study_data = study_detail.json()
                    has_processed = 'processed_images' in study_data
                    has_metadata = 'dicom_metadata' in study_data
                    print(f"   📊 Processed images: {'✅' if has_processed else '❌'}")
                    print(f"   📊 DICOM metadata: {'✅' if has_metadata else '❌'}")
                else:
                    print("   ❌ Individual study access: FAILED")
        else:
            print("   ❌ Studies endpoint: FAILED")
    except Exception as e:
        print(f"   ❌ Studies endpoint: ERROR - {e}")
    
    # Test 4: Debug endpoints
    print("\n4. Testing debug endpoints...")
    try:
        debug_studies = requests.get(f"{BASE_URL}/debug/studies")
        debug_files = requests.get(f"{BASE_URL}/debug/files")
        
        if debug_studies.status_code == 200 and debug_files.status_code == 200:
            print("   ✅ Debug endpoints: WORKING")
            
            studies_data = debug_studies.json()
            files_data = debug_files.json()
            print(f"   📊 Debug studies: {studies_data.get('total_studies', 0)}")
            print(f"   📊 Debug files: {files_data.get('total_files', 0)}")
        else:
            print("   ❌ Debug endpoints: FAILED")
    except Exception as e:
        print(f"   ❌ Debug endpoints: ERROR - {e}")
    
    # Test 5: DICOM processing capabilities
    print("\n5. Testing DICOM processing capabilities...")
    test_dicom_processing()
    
    return True

def test_dicom_processing():
    """Test DICOM processing functions"""
    try:
        # Test if advanced processor is available
        sys.path.append('.')
        from advanced_dicom_processor import AdvancedDicomProcessor
        
        processor = AdvancedDicomProcessor()
        libraries = processor.check_libraries()
        
        core_libs = ['pydicom', 'numpy', 'SimpleITK']
        core_available = all(libraries.get(lib) for lib in core_libs)
        
        if core_available:
            print("   ✅ Advanced DICOM processing: AVAILABLE")
            print("   📚 Libraries: pydicom, numpy, SimpleITK")
        else:
            print("   ⚠️  Advanced DICOM processing: PARTIAL")
            missing = [lib for lib in core_libs if not libraries.get(lib)]
            print(f"   📚 Missing: {', '.join(missing)}")
            
    except ImportError:
        print("   ❌ Advanced DICOM processing: NOT AVAILABLE")
        print("   💡 Run: COMPLETE_DICOM_SETUP.bat")
    
    # Test basic processing fallback
    try:
        import pydicom
        from PIL import Image
        import numpy as np
        print("   ✅ Basic DICOM processing: AVAILABLE")
    except ImportError:
        print("   ❌ Basic DICOM processing: NOT AVAILABLE")
        print("   💡 Run: pip install pydicom pillow numpy")

def check_file_structure():
    """Check if all required files are present"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        'final_working_backend.py',
        'advanced_dicom_processor.py',
        'check_dicom_libraries.py',
        'kiro_mini.db'
    ]
    
    optional_files = [
        'study_metadata.json',
        'uploads/',
        'processed/'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
    
    for file_path in optional_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️  {file_path} - Will be created")

def main():
    print("🚀 Complete Backend Test Suite")
    print("=" * 50)
    
    # Check file structure first
    check_file_structure()
    
    # Test backend functions
    print("\n🌐 Testing backend (make sure it's running on port 8000)...")
    success = test_backend_functions()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Backend test completed!")
        print("\n📋 Next steps:")
        print("1. Upload a DICOM file via frontend")
        print("2. Check if processing creates preview images")
        print("3. Verify study viewer displays images")
    else:
        print("⚠️  Some tests failed - check backend logs")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure backend is running: python final_working_backend.py")
        print("2. Install DICOM libraries: COMPLETE_DICOM_SETUP.bat")
        print("3. Check database exists: kiro_mini.db")

if __name__ == "__main__":
    main()