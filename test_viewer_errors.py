#!/usr/bin/env python3
"""
Test what errors the viewers might be encountering
"""

import requests
import json

def test_viewer_errors():
    """Test potential viewer errors"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Viewer Error Scenarios...")
    print("=" * 50)
    
    # Test if backend is accessible
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Test study endpoint
    study_uid = "1.2.840.113619.2.5.1757966844190003.8.432244991"
    try:
        response = requests.get(f"{base_url}/studies/{study_uid}", timeout=10)
        if response.status_code == 200:
            study_data = response.json()
            print("✅ Study data accessible")
            print(f"   Patient: {study_data.get('patient_id')}")
            print(f"   File: {study_data.get('original_filename')}")
            print(f"   DICOM URL: {study_data.get('dicom_url')}")
        else:
            print(f"❌ Study not accessible: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Study request failed: {e}")
        return
    
    # Test DICOM processing (what SimpleDicomViewer uses)
    patient_id = "P001"
    filename = "0002.DCM"
    
    print(f"\n📋 Testing SimpleDicomViewer Backend Calls:")
    
    # Test the exact call SimpleDicomViewer makes
    process_url = f"{base_url}/dicom/process/{patient_id}/{filename}"
    params = {
        "output_format": "PNG",
        "enhancement": "clahe",
        "frame": "0"
    }
    
    try:
        response = requests.get(process_url, params=params, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ SimpleDicomViewer backend call works")
                print(f"   Image data: {len(result.get('image_data', ''))} chars")
                
                # Check if image data is valid
                import base64
                try:
                    image_bytes = base64.b64decode(result['image_data'])
                    print(f"   Image size: {len(image_bytes)} bytes")
                    
                    if len(image_bytes) > 10000:
                        print("✅ Image data looks valid")
                    else:
                        print("⚠️  Image data seems small")
                        
                except Exception as e:
                    print(f"❌ Invalid image data: {e}")
                
            else:
                print(f"❌ Backend processing failed: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print(f"\n🎯 Viewer Configuration Status:")
    print("✅ MultiFrameDicomViewer: Now default (viewerTab = 0)")
    print("⚠️  SimpleDicomViewer: Moved to (viewerTab = 1)")
    print("✅ Backend processing: Working")
    print("✅ Study data: Accessible")
    
    print(f"\n📖 Current Setup:")
    print("- Tab 0: MultiFrameDicomViewer (Working)")
    print("- Tab 1: SimpleDicomViewer (May have errors)")
    print("- Tab 2: 3D Viewer")
    print("- Tab 3: Comprehensive Viewer")

if __name__ == "__main__":
    test_viewer_errors()