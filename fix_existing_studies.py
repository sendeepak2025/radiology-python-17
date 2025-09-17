"""
Fix existing studies to add image_urls field
"""
import json
from pathlib import Path

def fix_existing_studies():
    metadata_file = Path("study_metadata.json")
    
    if not metadata_file.exists():
        print("No metadata file found")
        return
    
    # Load existing metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"Found {len(metadata)} studies to fix...")
    
    # Fix each study
    for study_uid, study_data in metadata.items():
        if 'image_urls' not in study_data:
            patient_id = study_data.get('patient_id')
            filename = study_data.get('original_filename')
            
            if patient_id and filename:
                # Add image_urls field
                study_data['image_urls'] = [
                    f"wadouri:http://localhost:8000/uploads/{patient_id}/{filename}"
                ]
                print(f"✅ Fixed study {study_uid[:20]}... - Added image_urls")
            else:
                print(f"❌ Cannot fix study {study_uid[:20]}... - Missing patient_id or filename")
        else:
            print(f"✅ Study {study_uid[:20]}... already has image_urls")
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n🎉 Fixed {len(metadata)} studies!")
    print("All studies now have image_urls field")

if __name__ == "__main__":
    fix_existing_studies()