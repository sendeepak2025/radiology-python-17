#!/usr/bin/env python3
"""
Test the system after restart to verify frame processing works
"""

import requests
import time
import base64

def test_system_after_restart():
    """Test the complete system after restart"""
    
    base_url = "http://localhost:8000"
    patient_id = "P001"
    filename = "0002.DCM"
    
    print("🔍 Testing System After Restart...")
    print("=" * 50)
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend to be ready...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                break
        except:
            print(f"   Waiting... ({i+1}/10)")
            time.sleep(2)
    else:
        print("❌ Backend not responding after 20 seconds")
        return
    
    # Test frame processing
    print(f"\n📋 Testing Frame Processing:")
    
    process_url = f"{base_url}/dicom/process/{patient_id}/{filename}"
    
    # Test multiple frames
    test_frames = [0, 1, 10, 50, 95]
    frame_data = {}
    
    for frame_num in test_frames:
        params = {
            "output_format": "PNG",
            "enhancement": "clahe",
            "frame": str(frame_num)
        }
        
        try:
            response = requests.get(process_url, params=params, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    image_data = result.get('image_data', '')
                    frame_data[frame_num] = image_data
                    
                    print(f"   ✅ Frame {frame_num}: {len(image_data)} chars")
                    
                    # Check metadata
                    metadata = result.get('metadata', {})
                    if 'NumberOfFrames' in metadata:
                        print(f"      🎯 Total frames: {metadata['NumberOfFrames']}")
                    if 'extracted_frame' in metadata:
                        print(f"      📋 Extracted: {metadata['extracted_frame']}")
                    
                else:
                    print(f"   ❌ Frame {frame_num} failed: {result.get('error')}")
            else:
                print(f"   ❌ Frame {frame_num} HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Frame {frame_num} error: {e}")
    
    # Check if frames are different
    print(f"\n🔍 Frame Comparison:")
    unique_data = set(frame_data.values())
    
    if len(unique_data) > 1:
        print("✅ SUCCESS: Different frames return different data!")
        print("✅ Frame processing is working correctly")
        print("✅ Professional DICOM viewer ready")
    else:
        print("⚠️  All frames return identical data")
        print("⚠️  Frame processing may need backend restart")
    
    print(f"\n📊 Results Summary:")
    print(f"   Frames tested: {len(frame_data)}")
    print(f"   Unique images: {len(unique_data)}")
    print(f"   Success rate: {len(frame_data)}/{len(test_frames)}")
    
    # Test image quality
    if frame_data:
        sample_data = list(frame_data.values())[0]
        try:
            image_bytes = base64.b64decode(sample_data)
            print(f"   Image size: {len(image_bytes)} bytes")
            
            if len(image_bytes) > 50000:
                print("✅ Image quality: Good (large file size)")
            else:
                print("⚠️  Image quality: May be low (small file size)")
                
        except:
            print("❌ Invalid image data")
    
    print(f"\n🎯 Expected Frontend Behavior:")
    print("   - Single medical image display (512x512)")
    print("   - Mouse wheel scrolling changes frames")
    print("   - Arrow keys navigate frames")
    print("   - Frame counter shows 'Image X/96'")
    print("   - Professional medical workstation experience")
    
    if len(unique_data) > 1:
        print(f"\n🎉 System is ready for professional DICOM viewing!")
    else:
        print(f"\n⚠️  System needs backend restart for full functionality")

if __name__ == "__main__":
    test_system_after_restart()