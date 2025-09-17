"""
Simple DICOM to image preview converter
"""
import os
from pathlib import Path

def convert_dicom_to_preview():
    """Convert DICOM files to preview images"""
    try:
        import pydicom
        from PIL import Image
        import numpy as np
        print("✅ Required libraries available")
    except ImportError:
        print("❌ Missing libraries. Install with:")
        print("pip install pydicom pillow numpy")
        return

    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ No uploads directory found")
        return

    converted_count = 0
    
    for patient_dir in uploads_dir.iterdir():
        if patient_dir.is_dir():
            for file_path in patient_dir.iterdir():
                if file_path.suffix.lower() in ['.dcm', '.dicom']:
                    try:
                        print(f"🔍 Processing: {file_path}")
                        
                        # Read DICOM file
                        ds = pydicom.dcmread(str(file_path))
                        
                        # Get pixel data
                        if hasattr(ds, 'pixel_array'):
                            pixel_array = ds.pixel_array
                            
                            # Normalize to 0-255
                            if pixel_array.max() > 255:
                                pixel_array = ((pixel_array - pixel_array.min()) / 
                                             (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
                            
                            # Create PIL image
                            if len(pixel_array.shape) == 2:  # Grayscale
                                img = Image.fromarray(pixel_array, mode='L')
                            else:  # RGB
                                img = Image.fromarray(pixel_array)
                            
                            # Save as PNG preview
                            preview_path = file_path.with_suffix('.png')
                            img.save(preview_path)
                            
                            print(f"✅ Created preview: {preview_path}")
                            converted_count += 1
                        else:
                            print(f"⚠️ No pixel data in: {file_path}")
                            
                    except Exception as e:
                        print(f"❌ Error processing {file_path}: {e}")
    
    print(f"\n🎉 Converted {converted_count} DICOM files to previews")
    print("Preview images can now be displayed in the web viewer")

if __name__ == "__main__":
    convert_dicom_to_preview()