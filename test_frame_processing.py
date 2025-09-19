#!/usr/bin/env python3
"""
Test frame-specific processing
"""

import requests
import json

def test_frame_processing():
    """Test if backend can process specific frames"""
    
    base_url = "http://localhost:8000"
    patient_id = "P001"
    filename = "0002.DCM"
    
    print("🔍 Testing Frame-Specific Processing...")
    print("=" * 60)
    
    # Test different frame requests
    test_frames = [0, 1, 5, 10, 50, 95]
    
    for frame_num in test_frames:
        print(f"\n📋 Testing Frame {frame_num}:")
        
        process_url = f"{base_url}/dicom/process/{patient_id}/{filename}"
        params = {
            "output_format": "PNG",
            "enhancement": "clahe",
            "frame": str(frame_num)
        }
        
        try:
            response = requests.get(process_url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    print(f"   ✅ Frame {frame_num} processed successfully")
                    print(f"   📊 Image data length: {len(result.get('image_data', ''))}")
                    
                    # Check if image data is different from frame 0
                    if frame_num == 0:
                        global frame_0_data
                        frame_0_data = result.get('image_data', '')
                    elif frame_num > 0 and 'frame_0_data' in globals():
                        current_data = result.get('image_data', '')
                        if current_data != frame_0_data:
                            print(f"   🎯 Frame {frame_num} data differs from frame 0 (good!)")
                        else:
                            print(f"   ⚠️  Frame {frame_num} data same as frame 0")
                    
                else:
                    print(f"   ❌ Frame {frame_num} processing failed: {result.get('error')}")
            else:
                print(f"   ❌ Frame {frame_num} HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Frame {frame_num} request failed: {e}")
    
    # Test without frame parameter (original behavior)
    print(f"\n📋 Testing without frame parameter:")
    
    process_url = f"{base_url}/dicom/process/{patient_id}/{filename}"
    params = {
        "output_format": "PNG",
        "enhancement": "clahe"
    }
    
    try:
        response = requests.get(process_url, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("   ✅ No frame parameter processed successfully")
                print(f"   📊 Image data length: {len(result.get('image_data', ''))}")
                
                # Check metadata for frame info
                metadata = result.get('metadata', {})
                if metadata:
                    print("   📊 Metadata:")
                    for key, value in metadata.items():
                        if 'frame' in key.lower() or 'number' in key.lower():
                            print(f"      {key}: {value}")
            else:
                print(f"   ❌ No frame processing failed: {result.get('error')}")
        else:
            print(f"   ❌ No frame HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ No frame request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Frame Processing Analysis:")
    print("- Check if frame-specific processing works")
    print("- Verify if different frames return different data")
    print("- Compare with no-frame processing")
    print("- Identify optimal frame extraction method")

if __name__ == "__main__":
    test_frame_processing()