"""
Update existing studies with processed image information
"""
import json
from pathlib import Path

def update_existing_studies():
    """Update existing studies with processed image URLs"""
    metadata_file = Path("study_metadata.json")
    
    if not metadata_file.exists():
        print("❌ No study metadata file found")
        return
    
    # Load existing metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"🔍 Found {len(metadata)} studies to update")
    
    updated_count = 0
    
    for study_uid, study_data in metadata.items():
        patient_id = study_data.get('patient_id')
        original_filename = study_data.get('original_filename')
        
        if not patient_id or not original_filename:
            continue
        
        # Check for processed images
        patient_dir = Path("uploads") / patient_id
        if not patient_dir.exists():
            continue
        
        base_name = Path(original_filename).stem
        
        # Look for processed images
        processed_files = {}
        preview_path = patient_dir / f"{base_name}_preview.png"
        thumbnail_path = patient_dir / f"{base_name}_thumbnail.png"
        metadata_path = patient_dir / f"{base_name}_metadata.json"
        
        if preview_path.exists():
            processed_files['preview'] = str(preview_path)
            study_data['preview_url'] = f"/uploads/{patient_id}/{preview_path.name}"
        
        if thumbnail_path.exists():
            processed_files['thumbnail'] = str(thumbnail_path)
            study_data['thumbnail_url'] = f"/uploads/{patient_id}/{thumbnail_path.name}"
        
        if metadata_path.exists():
            processed_files['metadata'] = str(metadata_path)
            
            # Load DICOM metadata
            try:
                with open(metadata_path, 'r') as f:
                    dicom_metadata = json.load(f)
                study_data['dicom_metadata'] = dicom_metadata
            except:
                pass
        
        if processed_files:
            study_data['processed_images'] = processed_files
            study_data['processing_status'] = 'completed'
            updated_count += 1
            print(f"✅ Updated study: {original_filename} ({len(processed_files)} processed files)")
        else:
            study_data['processing_status'] = 'no_images'
            print(f"⚠️  No processed images for: {original_filename}")
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n🎉 Updated {updated_count} studies with processed image information")
    print("✅ Study metadata updated successfully")

if __name__ == "__main__":
    update_existing_studies()