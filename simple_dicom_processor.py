"""
Simple and robust DICOM processor
"""
import os
import json
from pathlib import Path
from datetime import datetime

def process_dicom_file_simple(file_path):
    """Simple DICOM processing with error handling"""
    try:
        import pydicom
        from PIL import Image
        import numpy as np
        
        print(f"🔍 Processing: {file_path}")
        
        # Read DICOM file
        ds = pydicom.dcmread(str(file_path), force=True)
        
        # Extract basic metadata
        metadata = {
            'patient_name': str(getattr(ds, 'PatientName', 'Unknown')),
            'patient_id': str(getattr(ds, 'PatientID', 'Unknown')),
            'study_date': str(getattr(ds, 'StudyDate', '')),
            'study_time': str(getattr(ds, 'StudyTime', '')),
            'modality': str(getattr(ds, 'Modality', 'Unknown')),
            'study_description': str(getattr(ds, 'StudyDescription', '')),
            'series_description': str(getattr(ds, 'SeriesDescription', '')),
        }
        
        processed_files = {}
        
        # Try to extract and process pixel data
        try:
            if hasattr(ds, 'pixel_array'):
                pixel_array = ds.pixel_array
                print(f"   📊 Image shape: {pixel_array.shape}")
                
                # Handle different array dimensions
                if len(pixel_array.shape) == 3:
                    # Multi-slice - take middle slice
                    image_2d = pixel_array[pixel_array.shape[0] // 2]
                elif len(pixel_array.shape) == 2:
                    # Single slice
                    image_2d = pixel_array
                else:
                    # Squeeze to 2D
                    image_2d = np.squeeze(pixel_array)
                
                # Normalize to 0-255
                if image_2d.max() > image_2d.min():
                    normalized = ((image_2d - image_2d.min()) / 
                                (image_2d.max() - image_2d.min()) * 255).astype(np.uint8)
                else:
                    normalized = np.zeros_like(image_2d, dtype=np.uint8)
                
                # Save as PNG
                base_name = file_path.stem
                preview_path = file_path.parent / f"{base_name}_preview.png"
                
                img = Image.fromarray(normalized)
                img.save(preview_path)
                
                processed_files['preview'] = str(preview_path)
                print(f"   ✅ Created preview: {preview_path}")
                
                # Create thumbnail
                thumbnail_path = file_path.parent / f"{base_name}_thumbnail.png"
                img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                img.save(thumbnail_path)
                
                processed_files['thumbnail'] = str(thumbnail_path)
                print(f"   ✅ Created thumbnail: {thumbnail_path}")
                
            else:
                print("   ⚠️ No pixel data found")
                
        except Exception as e:
            print(f"   ❌ Pixel processing failed: {e}")
        
        # Save metadata
        metadata_path = file_path.parent / f"{file_path.stem}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        processed_files['metadata'] = str(metadata_path)
        
        return {
            'success': True,
            'metadata': metadata,
            'processed_files': processed_files,
            'original_file': str(file_path),
            'processing_type': 'simple'
        }
        
    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'original_file': str(file_path)
        }

def process_all_dicom_files():
    """Process all DICOM files in uploads directory"""
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ No uploads directory found")
        return []
    
    results = []
    processed_count = 0
    
    for patient_dir in uploads_dir.iterdir():
        if patient_dir.is_dir():
            print(f"\n👤 Processing patient: {patient_dir.name}")
            for file_path in patient_dir.iterdir():
                if file_path.suffix.lower() in ['.dcm', '.dicom']:
                    result = process_dicom_file_simple(file_path)
                    results.append(result)
                    
                    if result['success']:
                        processed_count += 1
    
    print(f"\n🎉 Successfully processed {processed_count} DICOM files")
    return results

if __name__ == "__main__":
    print("🏥 Simple DICOM Processor")
    print("=" * 40)
    
    results = process_all_dicom_files()
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n📊 Processing Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    if failed > 0:
        print(f"\n❌ Failed files:")
        for result in results:
            if not result['success']:
                print(f"   - {result['original_file']}: {result['error']}")