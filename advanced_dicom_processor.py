"""
Advanced DICOM processor using professional medical imaging libraries
"""
import os
import json
from pathlib import Path
from datetime import datetime

class AdvancedDicomProcessor:
    def __init__(self):
        self.uploads_dir = Path("uploads")
        self.processed_dir = Path("processed")
        self.processed_dir.mkdir(exist_ok=True)
        
    def check_libraries(self):
        """Check if all required libraries are available"""
        required = ['pydicom', 'numpy', 'SimpleITK']
        optional = ['dicom_numpy', 'matplotlib', 'cv2']
        
        available = {}
        for lib in required + optional:
            try:
                if lib == 'cv2':
                    import cv2
                    available[lib] = cv2.__version__
                elif lib == 'dicom_numpy':
                    import dicom_numpy
                    available[lib] = getattr(dicom_numpy, '__version__', 'available')
                else:
                    module = __import__(lib)
                    available[lib] = getattr(module, '__version__', 'available')
            except ImportError:
                available[lib] = None
        
        return available
    
    def process_dicom_file(self, file_path):
        """Process DICOM file with advanced libraries"""
        try:
            import pydicom
            import numpy as np
            import SimpleITK as sitk
            from PIL import Image
            
            print(f"🔍 Processing DICOM: {file_path}")
            
            # Read DICOM with pydicom
            ds = pydicom.dcmread(str(file_path))
            
            # Extract metadata
            metadata = self.extract_dicom_metadata(ds)
            
            # Read with SimpleITK for advanced processing
            sitk_image = sitk.ReadImage(str(file_path))
            
            # Convert to numpy array
            pixel_array = sitk.GetArrayFromImage(sitk_image)
            
            # Process image data
            processed_images = self.process_image_data(pixel_array, ds)
            
            # Save processed images
            output_files = self.save_processed_images(file_path, processed_images, metadata)
            
            return {
                'success': True,
                'metadata': metadata,
                'processed_files': output_files,
                'original_file': str(file_path)
            }
            
        except ImportError as e:
            return {
                'success': False,
                'error': f'Missing library: {e}',
                'suggestion': 'Run install_dicom_libraries.bat'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_dicom_metadata(self, ds):
        """Extract comprehensive DICOM metadata"""
        metadata = {
            'patient_name': str(getattr(ds, 'PatientName', 'Unknown')),
            'patient_id': str(getattr(ds, 'PatientID', 'Unknown')),
            'study_date': str(getattr(ds, 'StudyDate', '')),
            'study_time': str(getattr(ds, 'StudyTime', '')),
            'modality': str(getattr(ds, 'Modality', 'Unknown')),
            'study_description': str(getattr(ds, 'StudyDescription', '')),
            'series_description': str(getattr(ds, 'SeriesDescription', '')),
            'institution_name': str(getattr(ds, 'InstitutionName', '')),
            'manufacturer': str(getattr(ds, 'Manufacturer', '')),
            'model_name': str(getattr(ds, 'ManufacturerModelName', '')),
        }
        
        # Image-specific metadata
        if hasattr(ds, 'pixel_array'):
            metadata.update({
                'image_shape': list(ds.pixel_array.shape),
                'bits_allocated': getattr(ds, 'BitsAllocated', None),
                'bits_stored': getattr(ds, 'BitsStored', None),
                'pixel_spacing': getattr(ds, 'PixelSpacing', None),
                'slice_thickness': getattr(ds, 'SliceThickness', None),
                'window_center': getattr(ds, 'WindowCenter', None),
                'window_width': getattr(ds, 'WindowWidth', None),
            })
        
        return metadata
    
    def process_image_data(self, pixel_array, ds):
        """Process image data with multiple techniques"""
        import numpy as np
        
        processed = {}
        
        # Handle different array dimensions
        if len(pixel_array.shape) == 3:
            # Multi-slice volume - take middle slice
            middle_slice = pixel_array.shape[0] // 2
            image_2d = pixel_array[middle_slice]
        elif len(pixel_array.shape) == 2:
            # Single slice
            image_2d = pixel_array
        else:
            # Handle other dimensions
            image_2d = np.squeeze(pixel_array)
        
        # Normalize to 0-255 range
        image_normalized = self.normalize_image(image_2d)
        processed['normalized'] = image_normalized
        
        # Apply windowing if available
        if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
            windowed = self.apply_windowing(image_2d, ds.WindowCenter, ds.WindowWidth)
            processed['windowed'] = windowed
        
        # Create thumbnail
        thumbnail = self.create_thumbnail(image_normalized, size=(256, 256))
        processed['thumbnail'] = thumbnail
        
        return processed
    
    def normalize_image(self, image):
        """Normalize image to 0-255 range"""
        import numpy as np
        
        # Handle different data types
        if image.dtype == np.uint8:
            return image
        
        # Normalize to 0-255
        image_min, image_max = image.min(), image.max()
        if image_max > image_min:
            normalized = ((image - image_min) / (image_max - image_min) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(image, dtype=np.uint8)
        
        return normalized
    
    def apply_windowing(self, image, center, width):
        """Apply DICOM windowing"""
        import numpy as np
        
        # Handle multiple values
        if isinstance(center, (list, tuple)):
            center = center[0]
        if isinstance(width, (list, tuple)):
            width = width[0]
        
        # Apply windowing
        min_val = center - width // 2
        max_val = center + width // 2
        
        windowed = np.clip(image, min_val, max_val)
        windowed = ((windowed - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        
        return windowed
    
    def create_thumbnail(self, image, size=(256, 256)):
        """Create thumbnail image"""
        from PIL import Image
        import numpy as np
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image)
        
        # Create thumbnail
        pil_image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert back to numpy
        return np.array(pil_image)
    
    def save_processed_images(self, original_path, processed_images, metadata):
        """Save processed images"""
        from PIL import Image
        
        output_files = {}
        base_name = original_path.stem
        patient_dir = original_path.parent
        
        for process_type, image_data in processed_images.items():
            # Save as PNG
            output_path = patient_dir / f"{base_name}_{process_type}.png"
            
            pil_image = Image.fromarray(image_data)
            pil_image.save(output_path)
            
            output_files[process_type] = str(output_path.relative_to(Path.cwd()))
            print(f"✅ Saved {process_type}: {output_path}")
        
        # Save metadata
        metadata_path = patient_dir / f"{base_name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        output_files['metadata'] = str(metadata_path.relative_to(Path.cwd()))
        
        return output_files
    
    def process_all_dicom_files(self):
        """Process all DICOM files in uploads directory"""
        if not self.uploads_dir.exists():
            print("❌ No uploads directory found")
            return
        
        results = []
        processed_count = 0
        
        for patient_dir in self.uploads_dir.iterdir():
            if patient_dir.is_dir():
                for file_path in patient_dir.iterdir():
                    if file_path.suffix.lower() in ['.dcm', '.dicom']:
                        result = self.process_dicom_file(file_path)
                        results.append(result)
                        
                        if result['success']:
                            processed_count += 1
        
        print(f"\n🎉 Processed {processed_count} DICOM files")
        return results

def main():
    print("🏥 Advanced DICOM Processor")
    print("=" * 40)
    
    processor = AdvancedDicomProcessor()
    
    # Check libraries
    libraries = processor.check_libraries()
    print("📚 Library Status:")
    for lib, version in libraries.items():
        status = f"✅ v{version}" if version else "❌ missing"
        print(f"   {lib}: {status}")
    
    # Check if core libraries are available
    core_available = all(libraries[lib] for lib in ['pydicom', 'numpy', 'SimpleITK'])
    
    if not core_available:
        print("\n⚠️  Core libraries missing. Run: install_dicom_libraries.bat")
        return
    
    print("\n🔄 Processing DICOM files...")
    results = processor.process_all_dicom_files()
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n📊 Processing Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    if successful > 0:
        print(f"\n🎯 Generated images:")
        print(f"   - Normalized images for web viewing")
        print(f"   - Windowed images (if applicable)")
        print(f"   - Thumbnail previews")
        print(f"   - Comprehensive metadata")

if __name__ == "__main__":
    main()