#!/usr/bin/env python3
"""
Debug the black screen issue
"""

import requests
import base64

def debug_black_screen():
    """Debug why the screen is black"""
    
    base_url = "http://localhost:8000"
    patient_id = "P001"
    filename = "0002.DCM"
    
    print("🔍 Debugging Black Screen Issue...")
    print("=" * 50)
    
    # Test frame 0 with size constraints
    process_url = f"{base_url}/dicom/process/{patient_id}/{filename}"
    params = {
        "output_format": "PNG",
        "enhancement": "clahe",
        "frame": "0",
        "width": "512",
        "height": "512"
    }
    
    try:
        response = requests.get(process_url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                image_data = result.get('image_data', '')
                print(f"✅ Backend working: {len(image_data)} chars")
                
                # Check if image data is valid base64
                try:
                    image_bytes = base64.b64decode(image_data)
                    print(f"✅ Valid base64: {len(image_bytes)} bytes")
                    
                    if image_bytes.startswith(b'\x89PNG'):
                        print("✅ Valid PNG header")
                        
                        # Check if image is not empty/black
                        if len(image_bytes) > 1000:  # Reasonable size for 512x512
                            print("✅ Image has reasonable size")
                        else:
                            print("⚠️  Image seems very small")
                            
                    else:
                        print("❌ Invalid PNG header")
                        print(f"   First 10 bytes: {image_bytes[:10]}")
                        
                except Exception as e:
                    print(f"❌ Invalid base64: {e}")
                
                # Check metadata
                metadata = result.get('metadata', {})
                print(f"\n📊 Metadata:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
                    
            else:
                print(f"❌ Backend error: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test without size constraints
    print(f"\n🔄 Testing without size constraints...")
    params_no_size = {
        "output_format": "PNG",
        "enhancement": "clahe",
        "frame": "0"
    }
    
    try:
        response = requests.get(process_url, params=params_no_size, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                image_data = result.get('image_data', '')
                print(f"✅ No size constraints: {len(image_data)} chars")
                
                try:
                    image_bytes = base64.b64decode(image_data)
                    print(f"✅ Image size: {len(image_bytes)} bytes")
                except:
                    print("❌ Invalid base64")
            else:
                print(f"❌ Error: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    debug_black_screen()