"""
Test the smart viewer functionality
"""
import requests
import json

def test_smart_viewer():
    print("🧠 Testing Smart DICOM Viewer")
    print("=" * 50)
    
    BASE_URL = "http://localhost:8000"
    
    # Test study UID
    study_uid = "1.2.840.113619.2.5.95594641c7683290cdfbb9e55066652f"
    
    print(f"🔍 Testing study: {study_uid}")
    
    try:
        response = requests.get(f"{BASE_URL}/studies/{study_uid}")
        
        if response.status_code == 200:
            study_data = response.json()
            
            print("✅ Study data retrieved successfully")
            print(f"📋 Study: {study_data.get('original_filename')}")
            print(f"👤 Patient: {study_data.get('patient_id')}")
            print(f"🔄 Processing Status: {study_data.get('processing_status')}")
            
            # Check for image URLs
            image_sources = []
            
            if study_data.get('preview_url'):
                image_sources.append(f"Preview: {study_data['preview_url']}")
            
            if study_data.get('thumbnail_url'):
                image_sources.append(f"Thumbnail: {study_data['thumbnail_url']}")
            
            if study_data.get('processed_images'):
                for key, path in study_data['processed_images'].items():
                    if key in ['preview', 'thumbnail']:
                        image_sources.append(f"Processed {key}: /{path.replace(chr(92), '/')}")
            
            if study_data.get('image_urls'):
                for url in study_data['image_urls']:
                    image_sources.append(f"Original: {url}")
            
            print(f"\n🖼️  Available Image Sources ({len(image_sources)}):")
            for source in image_sources:
                print(f"   - {source}")
            
            # Test image accessibility
            print(f"\n🔍 Testing Image Accessibility:")
            
            if study_data.get('preview_url'):
                preview_url = f"{BASE_URL}{study_data['preview_url']}"
                try:
                    img_response = requests.head(preview_url)
                    if img_response.status_code == 200:
                        print(f"   ✅ Preview image accessible: {preview_url}")
                    else:
                        print(f"   ❌ Preview image not accessible: {img_response.status_code}")
                except Exception as e:
                    print(f"   ❌ Preview image error: {e}")
            
            if study_data.get('thumbnail_url'):
                thumbnail_url = f"{BASE_URL}{study_data['thumbnail_url']}"
                try:
                    img_response = requests.head(thumbnail_url)
                    if img_response.status_code == 200:
                        print(f"   ✅ Thumbnail image accessible: {thumbnail_url}")
                    else:
                        print(f"   ❌ Thumbnail image not accessible: {img_response.status_code}")
                except Exception as e:
                    print(f"   ❌ Thumbnail image error: {e}")
            
            # Check metadata
            if study_data.get('dicom_metadata'):
                metadata = study_data['dicom_metadata']
                print(f"\n📊 DICOM Metadata:")
                print(f"   Patient Name: {metadata.get('patient_name', 'Unknown')}")
                print(f"   Modality: {metadata.get('modality', 'Unknown')}")
                print(f"   Study Date: {metadata.get('study_date', 'Unknown')}")
                print(f"   Study Description: {metadata.get('study_description', 'Unknown')}")
            
            print(f"\n🎯 Smart Viewer Status:")
            if len(image_sources) > 0:
                print("   ✅ Smart viewer should work - images available")
                print("   🖼️  Frontend will display processed medical images")
            else:
                print("   ⚠️  No images available - will show file info")
                
        else:
            print(f"❌ Failed to retrieve study: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing smart viewer: {e}")
    
    print("\n" + "=" * 50)
    print("🌐 Frontend URLs to test:")
    print(f"   Study Viewer: http://localhost:3000/studies/{study_uid}")
    print(f"   Patient Dashboard: http://localhost:3000/patients")
    print(f"   Smart Dashboard: http://localhost:3000/dashboard")

if __name__ == "__main__":
    test_smart_viewer()