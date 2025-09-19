#!/usr/bin/env python3
"""
Test the fixed parameters
"""

import requests
import base64

def test_fixed_params():
    """Test the fixed parameters without size constraints"""
    
    base_url = "http://localhost:8000"
    patient_id = "P001"
    filename = "0002.DCM"
    
    print("🔍 Testing Fixed Parameters...")
    print("=" * 40)
    
    process_url = f"{base_url}/dicom/process/{patient_id}/{filename}"
    params = {
        "output_format": "PNG",
        "enhancement": "clahe",
        "frame": "0"
    }
    
    try:
        response = requests.get(process_url, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                image_data = result.get('image_data', '')
                image_bytes = base64.b64decode(image_data)
                print(f"✅ Fixed: {len(image_bytes)} bytes")
                
                if len(image_bytes) > 50000:
                    print("✅ Image size looks good - should display properly")
                    print("✅ Black screen should be fixed")
                else:
                    print("❌ Image still too small")
                    
                # Test a different frame
                params['frame'] = '10'
                response2 = requests.get(process_url, params=params, timeout=10)
                if response2.status_code == 200:
                    result2 = response2.json()
                    if result2.get('success'):
                        image_data2 = result2.get('image_data', '')
                        if image_data2 != image_data:
                            print("✅ Different frames return different data")
                        else:
                            print("⚠️  Frames still returning same data")
                
            else:
                print(f"❌ Error: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_fixed_params()