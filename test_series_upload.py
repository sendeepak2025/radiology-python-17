#!/usr/bin/env python3
"""
Test the series upload functionality
"""

import requests
import os

def test_series_upload():
    """Test uploading multiple files as a series"""
    
    print("🧪 Testing Series Upload")
    print("=" * 30)
    
    # Create test files
    test_files = []
    for i in range(3):
        content = b"DICM" + f"slice_{i+1}".encode() + b"\x00" * 100
        test_files.append(('files', (f'test_slice_{i+1}.dcm', content, 'application/dicom')))
    
    data = {
        'description': 'Test series upload'
    }
    
    try:
        print(f"🚀 Uploading {len(test_files)} files as series...")
        
        response = requests.post(
            "http://localhost:8000/patients/SERIESTEST/upload/dicom",
            files=test_files,
            data=data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Series upload successful!")
            print(f"   Series UID: {result.get('series_uid', 'N/A')}")
            print(f"   Total Files: {result.get('total_files', 'N/A')}")
            print(f"   Total Slices: {result.get('total_slices', 'N/A')}")
        else:
            print("❌ Series upload failed!")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw error: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_series_upload()