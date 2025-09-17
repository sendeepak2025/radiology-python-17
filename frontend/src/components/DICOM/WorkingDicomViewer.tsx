import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, Paper, Alert, CircularProgress, Button } from '@mui/material';
import type { Study } from '../../types';

interface WorkingDicomViewerProps {
  study: Study;
  onError?: (error: string) => void;
}

const WorkingDicomViewer: React.FC<WorkingDicomViewerProps> = ({ study, onError }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

  const loadDicomImage = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔍 Study data:', study);

      // Try processed images first (from advanced processor)
      const studyAny = study as any;
      
      // Priority order: normalized > windowed > thumbnail > preview > original
      const imageUrls = [
        studyAny.processed_images?.normalized,
        studyAny.processed_images?.windowed, 
        studyAny.processed_images?.thumbnail,
        studyAny.preview_url,
        studyAny.thumbnail_url
      ].filter(Boolean);

      if (imageUrls.length > 0) {
        for (const imageUrl of imageUrls) {
          const fullUrl = imageUrl.startsWith('http') ? imageUrl : `http://localhost:8000${imageUrl}`;
          console.log('🔍 Trying image URL:', fullUrl);
          
          const success = await tryLoadImage(fullUrl);
          if (success) {
            return;
          }
        }
      }

      // No processed images available, try DICOM file
      console.log('ℹ️ No processed images available, trying DICOM file...');
      loadDicomFile();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load DICOM image';
      console.error('❌ DICOM loading error:', errorMessage);
      setError(errorMessage);
      setLoading(false);
      if (onError) {
        onError(errorMessage);
      }
    }
  };

  const tryLoadImage = (url: string): Promise<boolean> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = () => {
        console.log('✅ Image loaded successfully from:', url);
        drawImageToCanvas(img);
        setImageLoaded(true);
        setLoading(false);
        resolve(true);
      };

      img.onerror = () => {
        console.log('❌ Failed to load image from:', url);
        resolve(false);
      };

      img.src = url;
    });
  };

  const loadDicomFile = async () => {
    const url = `http://localhost:8000${study.dicom_url}`;
    try {
      console.log('🔍 Fetching DICOM file...');
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch DICOM file: ${response.status}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      console.log('✅ DICOM file loaded, size:', arrayBuffer.byteLength);

      // For now, show file info instead of trying to parse DICOM
      // This avoids complex DICOM parsing libraries
      showDicomInfo(arrayBuffer);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load DICOM file';
      console.error('❌ DICOM file loading error:', errorMessage);
      setError(errorMessage);
      setLoading(false);
    }
  };

  const showDicomInfo = (arrayBuffer: ArrayBuffer) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = 512;
    canvas.height = 512;

    // Clear canvas
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw DICOM file info
    ctx.fillStyle = '#ffffff';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    
    const lines = [
      'DICOM File Loaded',
      `Size: ${Math.round(arrayBuffer.byteLength / 1024)} KB`,
      `File: ${study.original_filename}`,
      `Patient: ${study.patient_id}`,
      `Modality: ${study.modality}`,
      '',
      'DICOM image parsing requires',
      'specialized medical imaging libraries.',
      '',
      'File is available for download below.'
    ];

    lines.forEach((line, index) => {
      ctx.fillText(line, canvas.width / 2, 50 + (index * 25));
    });

    setImageLoaded(true);
    setLoading(false);
  };

  const drawImageToCanvas = (img: HTMLImageElement) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match image or max 512x512
    const maxSize = 512;
    let { width, height } = img;
    
    if (width > maxSize || height > maxSize) {
      const ratio = Math.min(maxSize / width, maxSize / height);
      width *= ratio;
      height *= ratio;
    }

    canvas.width = width;
    canvas.height = height;

    // Draw image
    ctx.drawImage(img, 0, 0, width, height);
  };

  useEffect(() => {
    loadDicomImage();
  }, [study]);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          DICOM Image Viewer
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {study.study_description} - {study.original_filename}
        </Typography>
      </Paper>

      <Paper sx={{ flexGrow: 1, p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        {loading && (
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography variant="body2">Loading DICOM image...</Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2, maxWidth: 400 }}>
            {error}
          </Alert>
        )}

        <canvas
          ref={canvasRef}
          style={{
            maxWidth: '100%',
            maxHeight: '400px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            display: imageLoaded ? 'block' : 'none'
          }}
        />

        {imageLoaded && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              DICOM File Information
            </Typography>
            <Typography variant="caption" display="block" gutterBottom>
              Patient: {study.patient_id} | Modality: {study.modality} | Date: {study.study_date}
            </Typography>
            <Typography variant="caption" display="block" gutterBottom>
              File Size: {study.file_size ? `${Math.round(study.file_size / 1024)} KB` : 'Unknown'}
            </Typography>
            
            <Button
              variant="outlined"
              size="small"
              sx={{ mt: 1 }}
              onClick={() => {
                const link = document.createElement('a');
                link.href = `http://localhost:8000${study.dicom_url}`;
                link.download = study.original_filename || 'dicom_file.dcm';
                link.click();
              }}
            >
              Download DICOM File
            </Button>
          </Box>
        )}

        {!loading && !error && !imageLoaded && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              No image data available
            </Typography>
            <Button
              variant="contained"
              onClick={loadDicomImage}
              sx={{ mt: 1 }}
            >
              Retry Loading
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default WorkingDicomViewer;