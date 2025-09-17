import React, { useEffect, useRef, useState } from 'react';
import { 
  Box, Typography, Paper, Alert, CircularProgress, Button, 
  Card, CardContent, Grid, Chip, IconButton, Tooltip,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import {
  ZoomIn, ZoomOut, RotateLeft, RotateRight, Brightness6,
  Contrast, Info, Download, Fullscreen, Share
} from '@mui/icons-material';
import type { Study } from '../../types';

interface SmartDicomViewerProps {
  study: Study;
  onError?: (error: string) => void;
}

const SmartDicomViewer: React.FC<SmartDicomViewerProps> = ({ study, onError }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [currentImage, setCurrentImage] = useState<HTMLImageElement | null>(null);
  const [showMetadata, setShowMetadata] = useState(false);
  
  // Image manipulation states
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  const loadSmartDicomImage = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🧠 Smart DICOM Viewer - Processing study:', study);

      const studyAny = study as any;
      
      // Smart image priority: processed images > previews > thumbnails > original
      const imageOptions = [
        { url: studyAny.processed_images?.preview, type: 'Processed Preview', quality: 'High' },
        { url: studyAny.processed_images?.normalized, type: 'Normalized', quality: 'High' },
        { url: studyAny.processed_images?.windowed, type: 'Windowed', quality: 'Medical' },
        { url: studyAny.preview_url, type: 'Preview', quality: 'Medium' },
        { url: studyAny.thumbnail_url, type: 'Thumbnail', quality: 'Low' },
        { url: studyAny.processed_images?.thumbnail, type: 'Processed Thumbnail', quality: 'Low' },
        // Fallback to direct DICOM file URL for basic display
        { url: studyAny.dicom_url, type: 'DICOM File', quality: 'Original' },
        // Try image URLs array
        ...(studyAny.image_urls || []).map((url: string, index: number) => ({
          url: url.replace('wadouri:', ''), // Remove WADO URI prefix
          type: `Image ${index + 1}`,
          quality: 'Original'
        }))
      ].filter(option => option.url);

      console.log('🎯 Available image options:', imageOptions);

      if (imageOptions.length === 0) {
        throw new Error('No viewable images available for this DICOM study');
      }

      // Try loading images in priority order
      for (const option of imageOptions) {
        const cleanUrl = option.url.startsWith('/') ? option.url : `/${option.url}`;
        const fullUrl = option.url.startsWith('http') ? option.url : `http://localhost:8000${cleanUrl}`;
        console.log(`🔍 Trying ${option.type} image:`, fullUrl);
        
        const success = await tryLoadImage(fullUrl, option.type);
        if (success) {
          return;
        }
      }

      // If no images could be loaded, show DICOM file info instead
      console.log('ℹ️ No images could be loaded, showing DICOM file info');
      showDicomFileInfo();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load DICOM image';
      console.error('❌ Smart DICOM loading error:', errorMessage);
      setError(errorMessage);
      setLoading(false);
      if (onError) {
        onError(errorMessage);
      }
    }
  };

  const tryLoadImage = (url: string, type: string): Promise<boolean> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = () => {
        console.log(`✅ Successfully loaded ${type} image`);
        setCurrentImage(img);
        drawImageToCanvas(img);
        setImageLoaded(true);
        setLoading(false);
        resolve(true);
      };

      img.onerror = () => {
        console.log(`❌ Failed to load ${type} image`);
        resolve(false);
      };

      img.src = url;
    });
  };

  const showDicomFileInfo = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = 512;
    canvas.height = 400;

    // Clear canvas
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw DICOM file info
    ctx.fillStyle = '#333333';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    
    const lines = [
      '📋 DICOM Study Information',
      '',
      `File: ${study.original_filename || 'Unknown'}`,
      `Patient: ${study.patient_id || 'Unknown'}`,
      `Modality: ${study.modality || 'Unknown'}`,
      `Date: ${study.study_date || 'Unknown'}`,
      `Size: ${study.file_size ? Math.round(study.file_size / 1024) + ' KB' : 'Unknown'}`,
      '',
      '🔍 DICOM Processing Status:',
      (study as any).processing_status || 'Not processed',
      '',
      'Preview images not yet generated.',
      'File is available for download below.'
    ];

    lines.forEach((line, index) => {
      const y = 40 + (index * 25);
      if (line.startsWith('📋') || line.startsWith('🔍')) {
        ctx.font = 'bold 18px Arial';
        ctx.fillStyle = '#1976d2';
      } else if (line === '') {
        return; // Skip empty lines
      } else {
        ctx.font = '14px Arial';
        ctx.fillStyle = '#333333';
      }
      ctx.fillText(line, canvas.width / 2, y);
    });

    setImageLoaded(true);
    setLoading(false);
  };

  const drawImageToCanvas = (img: HTMLImageElement) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Calculate canvas size
    const maxSize = 512;
    let { width, height } = img;
    
    if (width > maxSize || height > maxSize) {
      const ratio = Math.min(maxSize / width, maxSize / height);
      width *= ratio;
      height *= ratio;
    }

    canvas.width = width;
    canvas.height = height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Apply transformations
    ctx.save();
    
    // Move to center for transformations
    ctx.translate(canvas.width / 2, canvas.height / 2);
    
    // Apply zoom and rotation
    ctx.scale(zoom, zoom);
    ctx.rotate((rotation * Math.PI) / 180);
    
    // Apply brightness and contrast filters
    ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
    
    // Draw image centered
    ctx.drawImage(img, -width / 2, -height / 2, width, height);
    
    ctx.restore();
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 5));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.1));
  };

  const handleRotateLeft = () => {
    setRotation(prev => prev - 90);
  };

  const handleRotateRight = () => {
    setRotation(prev => prev + 90);
  };

  const handleReset = () => {
    setZoom(1);
    setRotation(0);
    setBrightness(100);
    setContrast(100);
    setPan({ x: 0, y: 0 });
  };

  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = `${study.original_filename || 'dicom_image'}_processed.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  const getDicomMetadata = () => {
    const studyAny = study as any;
    return studyAny.dicom_metadata || {};
  };

  useEffect(() => {
    loadSmartDicomImage();
  }, [study]);

  useEffect(() => {
    if (currentImage && imageLoaded) {
      drawImageToCanvas(currentImage);
    }
  }, [zoom, rotation, brightness, contrast, currentImage, imageLoaded]);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Smart Header */}
      <Paper sx={{ p: 2, mb: 1 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom>
              🧠 Smart DICOM Viewer
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip 
                label={study.modality || 'Unknown'} 
                color="primary" 
                size="small" 
              />
              <Chip 
                label={`${study.original_filename}`} 
                variant="outlined" 
                size="small" 
              />
              <Chip 
                label={study.study_date || 'No date'} 
                variant="outlined" 
                size="small" 
              />
              {(study as any).processing_status && (
                <Chip 
                  label={`Processing: ${(study as any).processing_status}`}
                  color={(study as any).processing_status === 'completed' ? 'success' : 'warning'}
                  size="small" 
                />
              )}
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <Button
                startIcon={<Info />}
                onClick={() => setShowMetadata(true)}
                size="small"
                variant="outlined"
              >
                Metadata
              </Button>
              <Button
                startIcon={<Download />}
                onClick={handleDownload}
                size="small"
                variant="outlined"
                disabled={!imageLoaded}
              >
                Download
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Image Controls */}
      {imageLoaded && (
        <Paper sx={{ p: 1, mb: 1 }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            <Tooltip title="Zoom In">
              <IconButton onClick={handleZoomIn} size="small">
                <ZoomIn />
              </IconButton>
            </Tooltip>
            <Tooltip title="Zoom Out">
              <IconButton onClick={handleZoomOut} size="small">
                <ZoomOut />
              </IconButton>
            </Tooltip>
            <Typography variant="caption" sx={{ mx: 1 }}>
              {Math.round(zoom * 100)}%
            </Typography>
            
            <Tooltip title="Rotate Left">
              <IconButton onClick={handleRotateLeft} size="small">
                <RotateLeft />
              </IconButton>
            </Tooltip>
            <Tooltip title="Rotate Right">
              <IconButton onClick={handleRotateRight} size="small">
                <RotateRight />
              </IconButton>
            </Tooltip>
            
            <Button onClick={handleReset} size="small" variant="text">
              Reset
            </Button>
          </Box>
        </Paper>
      )}

      {/* Main Image Display */}
      <Paper sx={{ flexGrow: 1, p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {loading && (
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography variant="body2">Loading smart DICOM image...</Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ maxWidth: 400 }}>
            <Typography variant="subtitle2" gutterBottom>
              Smart DICOM Viewer Error
            </Typography>
            {error}
          </Alert>
        )}

        <canvas
          ref={canvasRef}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            border: '1px solid #ccc',
            borderRadius: '4px',
            display: imageLoaded ? 'block' : 'none',
            cursor: 'crosshair'
          }}
        />

        {!loading && !error && !imageLoaded && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No DICOM Image Available
            </Typography>
            <Typography variant="body2" color="text.secondary">
              This study does not contain viewable medical images.
            </Typography>
            <Button
              variant="contained"
              onClick={loadSmartDicomImage}
              sx={{ mt: 2 }}
            >
              Retry Loading
            </Button>
          </Box>
        )}
      </Paper>

      {/* Metadata Dialog */}
      <Dialog 
        open={showMetadata} 
        onClose={() => setShowMetadata(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          📊 DICOM Metadata - {study.original_filename}
        </DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Property</strong></TableCell>
                  <TableCell><strong>Value</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(getDicomMetadata()).map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell>{key.replace(/_/g, ' ').toUpperCase()}</TableCell>
                    <TableCell>{String(value) || 'N/A'}</TableCell>
                  </TableRow>
                ))}
                <TableRow>
                  <TableCell>FILE SIZE</TableCell>
                  <TableCell>{study.file_size ? `${Math.round(study.file_size / 1024)} KB` : 'Unknown'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>UPLOAD DATE</TableCell>
                  <TableCell>{study.created_at || 'Unknown'}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowMetadata(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SmartDicomViewer;