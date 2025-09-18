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
  const currentImageRef = useRef<HTMLImageElement | null>(null);
  const [showMetadata, setShowMetadata] = useState(false);

  // Image manipulation states
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  // URL building utility
  const buildUrl = (raw: string) => {
    if (!raw) return '';
    // Strip custom prefixes
    const cleaned = raw.replace(/^wadouri:/i, '').replace(/^dicom:/i, '').trim();
    if (/^https?:\/\//i.test(cleaned)) return cleaned;
    if (cleaned.startsWith('/')) return `http://localhost:8000${cleaned}`;
    return `http://localhost:8000/${cleaned}`;
  };

  const loadSmartDicomImage = async () => {
    try {
      setLoading(true);
      setError(null);
      setImageLoaded(false);
      currentImageRef.current = null;

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
        const fullUrl = buildUrl(option.url);
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
      let done = false;

      img.onload = () => {
        if (done) return;
        done = true;
        console.log(`✅ Successfully loaded ${type} image`);
        currentImageRef.current = img;
        drawImageToCanvas(img);
        setImageLoaded(true);
        setLoading(false);
        resolve(true);
      };

      img.onerror = () => {
        if (done) return;
        done = true;
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

    const maxSize = 512;
    let w = img.width;
    let h = img.height;
    const ratio = Math.min(1, maxSize / Math.max(w, h));
    w *= ratio;
    h *= ratio;

    const rad = (rotation * Math.PI) / 180;
    // Calculate bounding box after rotation and scale (zoom)
    const sin = Math.abs(Math.sin(rad));
    const cos = Math.abs(Math.cos(rad));
    const bboxW = Math.ceil((w * cos + h * sin) * zoom);
    const bboxH = Math.ceil((w * sin + h * cos) * zoom);

    canvas.width = bboxW;
    canvas.height = bboxH;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(canvas.width / 2 + pan.x, canvas.height / 2 + pan.y);
    ctx.scale(zoom, zoom);
    ctx.rotate(rad);
    ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
    ctx.drawImage(img, -w / 2, -h / 2, w, h);
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

    try {
      const link = document.createElement('a');
      link.download = `${study.original_filename || 'dicom_image'}_processed.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (err) {
      console.error('Download failed — canvas may be tainted by CORS', err);
      setError('Cannot download image: cross-origin restriction. Please enable CORS on the image server.');
    }
  };

  const getDicomMetadata = () => {
    const studyAny = study as any;
    return studyAny.dicom_metadata || {};
  };

  useEffect(() => {
    let active = true;
    loadSmartDicomImage();
    return () => {
      active = false;
    };
  }, [study]);

  useEffect(() => {
    if (currentImageRef.current && imageLoaded) {
      drawImageToCanvas(currentImageRef.current);
    }
  }, [zoom, rotation, brightness, contrast, pan, imageLoaded]);

  // Pan functionality
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    let dragging = false;
    let start = { x: 0, y: 0 };

    const onPointerDown = (e: PointerEvent) => {
      dragging = true;
      start = { x: e.clientX - pan.x, y: e.clientY - pan.y };
      canvas.setPointerCapture(e.pointerId);
    };
    
    const onPointerMove = (e: PointerEvent) => {
      if (!dragging) return;
      setPan({ x: e.clientX - start.x, y: e.clientY - start.y });
    };
    
    const onPointerUp = () => {
      dragging = false;
    };

    canvas.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    
    return () => {
      canvas.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, [pan]);

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
          tabIndex={0}
          role="img"
          aria-label={`DICOM image ${study.original_filename || ''}`}
          onWheel={(e) => {
            e.preventDefault();
            if (e.deltaY < 0) handleZoomIn(); else handleZoomOut();
          }}
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
            <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
              <Button
                variant="contained"
                onClick={loadSmartDicomImage}
              >
                Retry Loading
              </Button>
              {(study as any).dicom_url && (
                <Button
                  variant="outlined"
                  href={(study as any).dicom_url}
                  target="_blank"
                  startIcon={<Download />}
                >
                  Download DICOM
                </Button>
              )}
            </Box>
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
                    <TableCell>
                      {typeof value === 'object' ? (
                        <pre style={{whiteSpace:'pre-wrap', fontSize: '0.8rem'}}>
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      ) : (
                        String(value) || 'N/A'
                      )}
                    </TableCell>
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