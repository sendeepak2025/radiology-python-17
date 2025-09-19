"""
Enhanced DICOM Processor with image enhancement and conversion capabilities
"""

import os
import io
import numpy as np
import pydicom
from PIL import Image
import cv2
from typing import Optional, Tuple, Dict, Any, Union
import logging
from pathlib import Path
import base64

# Optional imports for advanced processing
try:
    import SimpleITK as sitk
    HAS_SIMPLEITK = True
except ImportError:
    HAS_SIMPLEITK = False

try:
    from skimage import exposure, filters, morphology
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False

from cache_manager import dicom_cache

logger = logging.getLogger(__name__)

class DicomProcessor:
    def __init__(self):
        self.supported_formats = ['PNG', 'JPEG', 'TIFF', 'BMP']
    
    def load_dicom(self, file_path: str, use_cache: bool = True) -> Optional[pydicom.Dataset]:
        """Load DICOM file with caching support"""
        if use_cache:
            cached_data = dicom_cache.get(file_path, "raw_dicom")
            if cached_data is not None:
                return cached_data
        
        try:
            dicom_data = pydicom.dcmread(file_path)
            
            if use_cache:
                dicom_cache.store(file_path, dicom_data, "raw_dicom")
            
            return dicom_data
        except Exception as e:
            logger.error(f"Failed to load DICOM file {file_path}: {e}")
            return None
    
    def extract_pixel_array(self, dicom_data: pydicom.Dataset) -> Optional[np.ndarray]:
        """Extract pixel array from DICOM data"""
        try:
            if not hasattr(dicom_data, 'pixel_array'):
                logger.error("DICOM file does not contain pixel data")
                return None
            
            pixel_array = dicom_data.pixel_array
            
            # Handle different photometric interpretations
            if hasattr(dicom_data, 'PhotometricInterpretation'):
                if dicom_data.PhotometricInterpretation == 'MONOCHROME1':
                    # Invert for MONOCHROME1
                    pixel_array = np.max(pixel_array) - pixel_array
            
            return pixel_array
        except Exception as e:
            logger.error(f"Failed to extract pixel array: {e}")
            return None
    
    def normalize_image(self, image: np.ndarray, 
                       window_center: Optional[float] = None,
                       window_width: Optional[float] = None) -> np.ndarray:
        """Normalize image with windowing"""
        try:
            if window_center is not None and window_width is not None:
                # Apply windowing
                img_min = window_center - window_width // 2
                img_max = window_center + window_width // 2
                image = np.clip(image, img_min, img_max)
            
            # Normalize to 0-255 range
            if image.dtype != np.uint8:
                image = image.astype(np.float64)
                image = (image - np.min(image)) / (np.max(image) - np.min(image))
                image = (image * 255).astype(np.uint8)
            
            return image
        except Exception as e:
            logger.error(f"Failed to normalize image: {e}")
            return image
    
    def enhance_image(self, image: np.ndarray, 
                     enhancement_type: str = "clahe") -> np.ndarray:
        """Apply image enhancement techniques"""
        try:
            if enhancement_type == "clahe" and len(image.shape) == 2:
                # Contrast Limited Adaptive Histogram Equalization
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                return clahe.apply(image)
            
            elif enhancement_type == "histogram_eq" and len(image.shape) == 2:
                # Standard histogram equalization
                return cv2.equalizeHist(image)
            
            elif enhancement_type == "gamma" and HAS_SKIMAGE:
                # Gamma correction
                return exposure.adjust_gamma(image, gamma=0.8)
            
            elif enhancement_type == "adaptive_eq" and HAS_SKIMAGE:
                # Adaptive equalization
                return exposure.equalize_adapthist(image)
            
            elif enhancement_type == "unsharp_mask" and HAS_SKIMAGE:
                # Unsharp masking for sharpening
                return filters.unsharp_mask(image, radius=1, amount=1)
            
            else:
                logger.warning(f"Enhancement type '{enhancement_type}' not supported")
                return image
                
        except Exception as e:
            logger.error(f"Failed to enhance image: {e}")
            return image
    
    def apply_filters(self, image: np.ndarray, filter_type: str = "gaussian") -> np.ndarray:
        """Apply various filters to the image"""
        try:
            if filter_type == "gaussian":
                return cv2.GaussianBlur(image, (5, 5), 0)
            
            elif filter_type == "median":
                return cv2.medianBlur(image, 5)
            
            elif filter_type == "bilateral":
                return cv2.bilateralFilter(image, 9, 75, 75)
            
            elif filter_type == "edge_enhance":
                kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                return cv2.filter2D(image, -1, kernel)
            
            else:
                logger.warning(f"Filter type '{filter_type}' not supported")
                return image
                
        except Exception as e:
            logger.error(f"Failed to apply filter: {e}")
            return image
    
    def resize_image(self, image: np.ndarray, 
                    target_size: Tuple[int, int],
                    maintain_aspect: bool = True) -> np.ndarray:
        """Resize image with optional aspect ratio maintenance"""
        try:
            if maintain_aspect:
                h, w = image.shape[:2]
                target_w, target_h = target_size
                
                # Calculate scaling factor
                scale = min(target_w / w, target_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                
                # Pad to target size if needed
                if new_w != target_w or new_h != target_h:
                    pad_w = (target_w - new_w) // 2
                    pad_h = (target_h - new_h) // 2
                    resized = cv2.copyMakeBorder(
                        resized, pad_h, target_h - new_h - pad_h,
                        pad_w, target_w - new_w - pad_w,
                        cv2.BORDER_CONSTANT, value=0
                    )
                
                return resized
            else:
                return cv2.resize(image, target_size, interpolation=cv2.INTER_LANCZOS4)
                
        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            return image
    
    def convert_to_format(self, image: np.ndarray, 
                         output_format: str = "PNG",
                         quality: int = 95) -> Optional[bytes]:
        """Convert image to specified format"""
        try:
            if output_format.upper() not in self.supported_formats:
                logger.error(f"Unsupported format: {output_format}")
                return None
            
            # Convert to PIL Image
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image, mode='L')
            else:
                pil_image = Image.fromarray(image, mode='RGB')
            
            # Save to bytes
            output_buffer = io.BytesIO()
            
            if output_format.upper() == 'JPEG':
                pil_image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            else:
                pil_image.save(output_buffer, format=output_format.upper())
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to convert image to {output_format}: {e}")
            return None
    
    def create_thumbnail(self, image: np.ndarray, 
                        size: Tuple[int, int] = (256, 256)) -> Optional[bytes]:
        """Create thumbnail image"""
        try:
            thumbnail = self.resize_image(image, size, maintain_aspect=True)
            return self.convert_to_format(thumbnail, "JPEG", quality=85)
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            return None
    
    def process_dicom_file(self, file_path: str,
                          enhancement: Optional[str] = None,
                          filter_type: Optional[str] = None,
                          output_format: str = "PNG",
                          target_size: Optional[Tuple[int, int]] = None,
                          frame: Optional[int] = None,
                          use_cache: bool = True) -> Dict[str, Any]:
        """Process DICOM file with various enhancements and conversions"""
        
        # Generate cache key for processed version
        cache_key_parts = [enhancement or "none", filter_type or "none", 
                          output_format, str(target_size or "original"), 
                          f"frame_{frame}" if frame is not None else "all_frames"]
        cache_operation = f"processed_{'_'.join(cache_key_parts)}"
        
        if use_cache:
            cached_result = dicom_cache.get(file_path, cache_operation)
            if cached_result is not None:
                return cached_result
        
        result = {
            'success': False,
            'error': None,
            'metadata': {},
            'image_data': None,
            'thumbnail': None
        }
        
        try:
            # Load DICOM
            dicom_data = self.load_dicom(file_path, use_cache)
            if dicom_data is None:
                result['error'] = "Failed to load DICOM file"
                return result
            
            # Extract metadata
            result['metadata'] = self._extract_metadata(dicom_data)
            
            # Extract pixel array
            pixel_array = self.extract_pixel_array(dicom_data)
            if pixel_array is None:
                result['error'] = "Failed to extract pixel data"
                return result
            
            # Handle multi-frame DICOM - extract specific frame if requested
            if len(pixel_array.shape) == 3 and pixel_array.shape[0] > 1:
                # Multi-frame DICOM detected
                total_frames = pixel_array.shape[0]
                result['metadata']['NumberOfFrames'] = total_frames
                
                if frame is not None:
                    # Extract specific frame
                    if 0 <= frame < total_frames:
                        pixel_array = pixel_array[frame]
                        result['metadata']['extracted_frame'] = frame
                        print(f"🎯 Extracted frame {frame} from {total_frames} total frames")
                    else:
                        result['error'] = f"Frame {frame} out of range (0-{total_frames-1})"
                        return result
                else:
                    # No specific frame requested - use first frame
                    pixel_array = pixel_array[0]
                    result['metadata']['extracted_frame'] = 0
                    print(f"🎯 Using first frame from {total_frames} total frames")
            else:
                # Single frame DICOM
                result['metadata']['NumberOfFrames'] = 1
                result['metadata']['extracted_frame'] = 0
            
            # Get windowing parameters from DICOM
            window_center = getattr(dicom_data, 'WindowCenter', None)
            window_width = getattr(dicom_data, 'WindowWidth', None)
            
            if isinstance(window_center, (list, tuple)):
                window_center = window_center[0]
            if isinstance(window_width, (list, tuple)):
                window_width = window_width[0]
            
            # Normalize image
            processed_image = self.normalize_image(pixel_array, window_center, window_width)
            
            # Apply enhancement
            if enhancement:
                processed_image = self.enhance_image(processed_image, enhancement)
            
            # Apply filter
            if filter_type:
                processed_image = self.apply_filters(processed_image, filter_type)
            
            # Resize if requested
            if target_size:
                processed_image = self.resize_image(processed_image, target_size)
            
            # Convert to output format
            image_bytes = self.convert_to_format(processed_image, output_format)
            if image_bytes is None:
                result['error'] = f"Failed to convert to {output_format}"
                return result
            
            result['image_data'] = base64.b64encode(image_bytes).decode('utf-8')
            
            # Create thumbnail
            thumbnail_bytes = self.create_thumbnail(processed_image)
            if thumbnail_bytes:
                result['thumbnail'] = base64.b64encode(thumbnail_bytes).decode('utf-8')
            
            result['success'] = True
            
            # Cache the result
            if use_cache:
                dicom_cache.store(file_path, result, cache_operation)
            
        except Exception as e:
            logger.error(f"Failed to process DICOM file: {e}")
            result['error'] = str(e)
        
        return result
    
    def _extract_metadata(self, dicom_data: pydicom.Dataset) -> Dict[str, Any]:
        """Extract relevant metadata from DICOM"""
        metadata = {}
        
        # Basic patient info
        metadata['patient_id'] = getattr(dicom_data, 'PatientID', 'Unknown')
        metadata['patient_name'] = str(getattr(dicom_data, 'PatientName', 'Unknown'))
        metadata['patient_birth_date'] = getattr(dicom_data, 'PatientBirthDate', 'Unknown')
        metadata['patient_sex'] = getattr(dicom_data, 'PatientSex', 'Unknown')
        
        # Study info
        metadata['study_date'] = getattr(dicom_data, 'StudyDate', 'Unknown')
        metadata['study_time'] = getattr(dicom_data, 'StudyTime', 'Unknown')
        metadata['study_description'] = getattr(dicom_data, 'StudyDescription', 'Unknown')
        metadata['modality'] = getattr(dicom_data, 'Modality', 'Unknown')
        
        # Image info
        metadata['rows'] = getattr(dicom_data, 'Rows', 0)
        metadata['columns'] = getattr(dicom_data, 'Columns', 0)
        metadata['pixel_spacing'] = getattr(dicom_data, 'PixelSpacing', [1.0, 1.0])
        metadata['slice_thickness'] = getattr(dicom_data, 'SliceThickness', 'Unknown')
        
        # Windowing
        metadata['window_center'] = getattr(dicom_data, 'WindowCenter', None)
        metadata['window_width'] = getattr(dicom_data, 'WindowWidth', None)
        
        return metadata

# Global processor instance
dicom_processor = DicomProcessor()