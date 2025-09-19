#!/usr/bin/env python3
"""
Check what the backend processing is actually returning
"""

import requests
import json

def check_backend_processing():
    """Check the backend DICOM processing output"""
    
    base_url = "http://localhost:8000"
    patient_id = "P001"
    filename = "0002.DCM"
    
    print("🔍 Checking Backend DICOM Processing Output...")
    print("=" * 60)
    
    process_url = f"{base_url}/dicom/process/{patient_id}/{filename}"
    params = {
        "output_format": "PNG",
        "enhancement": "clahe"
    }
    
    print(f"📋 Testing: {process_url}")
    print(f"   Parameters: {params}")
    
    try:
        response = requests.get(process_url, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Backend processing successful")
                print(f"   Image data length: {len(result.get('image_data', ''))}")
                
                metadata = result.get('metadata', {})
                print("\n📊 DICOM Metadata:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
                
                # Check dimensions
                if 'rows' in metadata and 'columns' in metadata:
                    expected_dims = f"{metadata['columns']}x{metadata['rows']}"
                    print(f"\n📐 Expected dimensions: {expected_dims}")
                
                # Check if this is a multi-frame issue
                if 'NumberOfFrames' in metadata:
                    frames = metadata['NumberOfFrames']
                    print(f"🎯 Multi-frame detected: {frames} frames")
                else:
                    print("ℹ️  No NumberOfFrames in metadata")
                
                # Test without enhancement to see raw output
                print(f"\n🔄 Testing without enhancement...")
                raw_params = {"output_format": "PNG"}
                raw_response = requests.get(process_url, params=raw_params, timeout=30)
                
                if raw_response.status_code == 200:
                    raw_result = raw_response.json()
                    if raw_result.get('success'):
                        print("✅ Raw processing also successful")
                        print(f"   Raw image data length: {len(raw_result.get('image_data', ''))}")
                    else:
                        print(f"❌ Raw processing failed: {raw_result.get('error')}")
                
            else:
                print(f"❌ Backend processing failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Also test the metadata endpoint
    print(f"\n📋 Testing metadata endpoint...")
    try:
        metadata_url = f"{base_url}/dicom/metadata/{patient_id}/{filename}"
        response = requests.get(metadata_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Metadata endpoint working")
                metadata = result.get('metadata', {})
                print("📊 Direct metadata:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ Metadata failed: {result.get('error')}")
        else:
            print(f"❌ Metadata HTTP error: {response.status_code}")
    except Exception as e:
        print(f"❌ Metadata request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Analysis:")
    print("- Check if dimensions match expected DICOM size")
    print("- Verify if multi-frame is being handled correctly")
    print("- Compare enhanced vs raw processing")
    print("- Ensure proper frame extraction")

if __name__ == "__main__":
    check_backend_processing()