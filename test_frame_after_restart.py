#!/usr/bin/env python3
"""
Test frame processing after backend restart
"""

import requests
import json
import time

def test_frame_after_restart():
    """Test frame processing after backend restart"""
    
    base_url = "http://localhost:8000"
    patient_id = "P001"
    filename = "0002.DCM"
    
    print("🔍 Testing Frame Processing After Backend Restart...")
    print("=" * 70)
    
    # Wait a moment for backend to be ready
    print("⏳ Waiting for backend to be ready...")
    time.sleep(2)
    
    # Test health first
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy and ready")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Test frame 0 vs frame 10 to see if they're different
    test_frames = [0, 10, 50]
    frame_data = {}
    
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
                    image_data = result.get('image_data', '')
                    frame_data[frame_num] = image_data
                    
                    print(f"   ✅ Frame {frame_num} processed successfully")
                    print(f"   📊 Image data length: {len(image_data)}")
                    
                    # Check metadata
                    metadata = result.get('metadata', {})
                    if 'NumberOfFrames' in metadata:
                        print(f"   🎯 Total frames detected: {metadata['NumberOfFrames']}")
                    if 'extracted_frame' in metadata:
                        print(f"   📋 Extracted frame: {metadata['extracted_frame']}")
                    
                else:
                    print(f"   ❌ Frame {frame_num} processing failed: {result.get('error')}")
            else:
                print(f"   ❌ Frame {frame_num} HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Frame {frame_num} request failed: {e}")
    
    # Compare frame data
    print(f"\n🔍 Comparing Frame Data:")
    if len(frame_data) >= 2:
        frames = list(frame_data.keys())
        for i in range(len(frames)):
            for j in range(i + 1, len(frames)):
                frame_a, frame_b = frames[i], frames[j]
                if frame_data[frame_a] == frame_data[frame_b]:
                    print(f"   ⚠️  Frame {frame_a} and Frame {frame_b} have identical data")
                else:
                    print(f"   ✅ Frame {frame_a} and Frame {frame_b} have different data")
    
    print("\n" + "=" * 70)
    print("🎯 Frame Processing Status:")
    if len(set(frame_data.values())) > 1:
        print("✅ Frame-specific processing is working!")
        print("✅ Different frames return different image data")
        print("✅ Multi-frame DICOM support confirmed")
    else:
        print("❌ Frame processing still not working")
        print("❌ All frames return identical data")
        print("❌ Backend changes may not be active")
    
    print("\n📖 Next Steps:")
    print("- If working: SimpleDicomViewer should show proper individual frames")
    print("- If not working: Backend restart may be needed")
    print("- Check console logs for frame extraction messages")

if __name__ == "__main__":
    test_frame_after_restart()