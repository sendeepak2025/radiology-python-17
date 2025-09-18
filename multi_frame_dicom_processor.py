"""
Multi-frame DICOM processor - Extracts ALL frames from DICOM files
"""
import os
import json
from pathlib import Path
from datetime import datetime

class MultiFrameDicomProcessor:
    def __init__(self):
        self.uploads_dir = Path("uploads")
        self.processed_dir = Path("processed")
        self.processed_dir.mkdir(exist_ok=True)
        
    def process_dicom_file(self, file_path):
        """Process DICOM file and extract ALL frames"""
        try:
            import pydicom
            import numpy as np
            import SimpleITK as sitk
            from PIL import Image
            
            print(f"🔍 Processing multi-frame DICOM: {file_path}")
            
            # Read DICOM with pydicom
            ds = pydicom.dcmread(str(file_path))
            
            # Read with SimpleITK for advanced processing
            sitk_image = sitk.ReadImage(str(file_path))
            
            # Convert to numpy array
            pixel_array = sitk.GetArrayFromImage(sitk_image)
            
            print(f"📊 DICOM array shape: {pixel_array.shape}")
            
            # Extract metadata
            metadata = self.extract_dicom_metadata(ds, pixel_array)
            
            # Process ALL frames instead of just middle slice
            processed_frames = self.process_all_frames(pixel_array, ds)
            
            # Save all processed frames
            output_files = self.save_all_frames(file_path, processed_frames, metadata)
            
            return {
                'success': True,
                'metadata': metadata,
                'processed_files': output_files,
                'total_frames': len(processed_frames),
                'original_file': str(file_path)
            }
            
        except ImportError as e:
            return {
                'success': False,
                'error': f'Missing library: {e}',
                'suggestion': 'Install: pip install pydicom SimpleITK pillow numpy'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_dicom_metadata(self, ds, pixel_array):
        """Extract comprehensive DICOM metadata including frame info"""
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
        
        # Frame-specific metadata
        if len(pixel_array.shape) >= 3:
            metadata.update({
                'number_of_frames': pixel_array.shape[0],
                'frame_width': pixel_array.shape[2] if len(pixel_array.shape) > 2 else pixel_array.shape[1],
                'frame_height': pixel_array.shape[1] if len(pixel_array.shape) > 2 else pixel_array.shape[0],
                'is_multi_frame': True
            })
        else:
            metadata.update({
                'number_of_frames': 1,
                'frame_width': pixel_array.shape[1],
                'frame_height': pixel_array.shape[0],
                'is_multi_frame': False
            })
        
        # Image-specific metadata
        metadata.update({
            'rows': getattr(ds, 'Rows', None),
            'columns': getattr(ds, 'Columns', None),
            'bits_allocated': getattr(ds, 'BitsAllocated', None),
            'bits_stored': getattr(ds, 'BitsStored', None),
            'pixel_spacing': getattr(ds, 'PixelSpacing', None),
            'slice_thickness': getattr(ds, 'SliceThickness', None),
            'window_center': getattr(ds, 'WindowCenter', None),
            'window_width': getattr(ds, 'WindowWidth', None),
        })
        
        return metadata
    
    def process_all_frames(self, pixel_array, ds):
        """Process ALL frames from multi-frame DICOM"""
        import numpy as np
        
        processed_frames = []
        
        # Handle different array dimensions
        if len(pixel_array.shape) == 3:
            # Multi-frame volume - process ALL frames
            num_frames = pixel_array.shape[0]
            print(f"📚 Processing {num_frames} frames...")
            
            for frame_idx in range(num_frames):
                frame_2d = pixel_array[frame_idx]
                
                # Process this frame
                processed_frame = self.process_single_frame(frame_2d, ds, frame_idx)
                processed_frames.append(processed_frame)
                
                if (frame_idx + 1) % 10 == 0:
                    print(f"✅ Processed {frame_idx + 1}/{num_frames} frames")
                    
        elif len(pixel_array.shape) == 2:
            # Single frame
            processed_frame = self.process_single_frame(pixel_array, ds, 0)
            processed_frames.append(processed_frame)
        else:
            # Handle other dimensions
            frame_2d = np.squeeze(pixel_array)
            processed_frame = self.process_single_frame(frame_2d, ds, 0)
            processed_frames.append(processed_frame)
        
        print(f"🎯 Total frames processed: {len(processed_frames)}")
        return processed_frames
    
    def process_single_frame(self, frame_2d, ds, frame_index):
        """Process a single frame"""
        import numpy as np
        
        # Normalize to 0-255 range
        frame_normalized = self.normalize_image(frame_2d)
        
        processed = {
            'frame_index': frame_index,
            'normalized': frame_normalized,
            'original_shape': frame_2d.shape,
            'data_type': str(frame_2d.dtype)
        }
        
        # Apply windowing if available
        if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
            windowed = self.apply_windowing(frame_2d, ds.WindowCenter, ds.WindowWidth)
            processed['windowed'] = windowed
        
        # Create thumbnail for this frame
        thumbnail = self.create_thumbnail(frame_normalized, size=(256, 256))
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
        img_min = center - width // 2
        img_max = center + width // 2
        
        windowed = np.clip(image, img_min, img_max)
        windowed = ((windowed - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        
        return windowed
    
    def create_thumbnail(self, image, size=(256, 256)):
        """Create thumbnail of image"""
        from PIL import Image as PILImage
        import numpy as np
        
        # Convert to PIL Image
        pil_image = PILImage.fromarray(image)
        
        # Resize maintaining aspect ratio
        pil_image.thumbnail(size, PILImage.Resampling.LANCZOS)
        
        # Convert back to numpy
        thumbnail = np.array(pil_image)
        
        return thumbnail
    
    def save_all_frames(self, original_file_path, processed_frames, metadata):
        """Save all processed frames as individual images"""
        from PIL import Image as PILImage
        import numpy as np
        
        file_path = Path(original_file_path)
        base_name = file_path.stem
        patient_dir = file_path.parent
        
        output_files = {
            'frames': [],
            'metadata_file': None,
            'summary': None
        }
        
        # Save individual frames
        for i, frame_data in enumerate(processed_frames):
            frame_files = {}
            
            # Save normalized frame
            if 'normalized' in frame_data:
                normalized_path = patient_dir / f"{base_name}_frame_{i:03d}_normalized.png"
                PILImage.fromarray(frame_data['normalized']).save(normalized_path)
                frame_files['normalized'] = str(normalized_path)
            
            # Save windowed frame if available
            if 'windowed' in frame_data:
                windowed_path = patient_dir / f"{base_name}_frame_{i:03d}_windowed.png"
                PILImage.fromarray(frame_data['windowed']).save(windowed_path)
                frame_files['windowed'] = str(windowed_path)
            
            # Save thumbnail
            if 'thumbnail' in frame_data:
                thumbnail_path = patient_dir / f"{base_name}_frame_{i:03d}_thumbnail.png"
                PILImage.fromarray(frame_data['thumbnail']).save(thumbnail_path)
                frame_files['thumbnail'] = str(thumbnail_path)
            
            frame_files['frame_index'] = i
            output_files['frames'].append(frame_files)
        
        # Save metadata
        metadata_path = patient_dir / f"{base_name}_multiframe_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        output_files['metadata_file'] = str(metadata_path)
        
        # Create summary file with frame list
        summary = {
            'original_file': str(original_file_path),
            'total_frames': len(processed_frames),
            'processing_date': datetime.now().isoformat(),
            'frame_files': output_files['frames']
        }
        
        summary_path = patient_dir / f"{base_name}_frame_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        output_files['summary'] = str(summary_path)
        
        print(f"💾 Saved {len(processed_frames)} frames to {patient_dir}")
        return output_files

def process_multiframe_dicom(file_path):
    """Main function to process multi-frame DICOM"""
    processor = MultiFrameDicomProcessor()
    return processor.process_dicom_file(file_path)

if __name__ == "__main__":
    # Test with 0002.DCM
    test_file = "uploads/PAT001/0002.DCM"
    if os.path.exists(test_file):
        print(f"🧪 Testing multi-frame processing with {test_file}")
        result = process_multiframe_dicom(test_file)
        print(f"📊 Result: {result}")
    else:
        print(f"❌ Test file not found: {test_file}")