import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  IconButton,
  Tooltip,
  Slider,
  Grid,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  RotateLeft as RotateLeftIcon,
  RotateRight as RotateRightIcon,
  Refresh as ResetIcon,
  Fullscreen as FullscreenIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
} from '@mui/icons-material';

interface Study {
  study_uid: string;
  patient_id: string;
  patient_name?: string;
  study_date: string;
  modality: string;
  exam_type: string;
  study_description: string;
  image_urls?: string[];
  dicom_url?: string;
}

interface WorkingDicomViewerProps {
  study: Study;
  onError?: (error: string) => void;
}

const WorkingDicomViewer: React.FC<WorkingDicomViewerProps> = ({
  study,
  onError,
}) => {
  const viewerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState('Initializing viewer...');
  const [loadingProgress, setLoadingProgress] = useState(0);
  
  // Viewer state
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [totalImages, setTotalImages] = useState(0);
  const [windowWidth, setWindowWidth] = useState(400);
  const [windowCenter, setWindowCenter] = useState(40);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Mock image data for demonstration
  const [imageData, setImageData] = useState<any>(null);

  const initializeViewer = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      setLoadingMessage('Loading study data...');
      setLoadingProgress(20);

      // Simulate loading delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setLoadingMessage('Processing DICOM images...');
      setLoadingProgress(50);

      // Mock image processing
      const mockImageData = {
        width: 512,
        height: 512,
        pixelData: new Uint16Array(512 * 512).fill(0).map((_, i) => {
          // Create a simple test pattern
          const x = i % 512;
          const y = Math.floor(i / 512);
          const centerX = 256;
          const centerY = 256;
          const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
          return Math.floor(Math.sin(distance / 20) * 1000 + 2000);
        }),
        windowWidth: 400,
        windowCenter: 40,
      };

      setImageData(mockImageData);
      setTotalImages(study.image_urls?.length || 1);
      setLoadingProgress(80);
      
      setLoadingMessage('Rendering image...');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setLoadingProgress(100);
      setLoadingMessage('Complete!');
      
      setTimeout(() => {
        setIsLoading(false);
      }, 200);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load DICOM study';
      setError(errorMessage);
      onError?.(errorMessage);
      setIsLoading(false);
    }
  }, [study, onError]);

  useEffect(() => {
    initializeViewer();
  }, [initializeViewer]);

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
    setWindowWidth(400);
    setWindowCenter(40);
  };

  const handleWindowWidthChange = (_: Event, value: number | number[]) => {
    setWindowWidth(Array.isArray(value) ? value[0] : value);
  };

  const handleWindowCenterChange = (_: Event, value: number | number[]) => {
    setWindowCenter(Array.isArray(value) ? value[0] : value);
  };

  const handleImageNavigation = (direction: 'prev' | 'next') => {
    if (direction === 'prev' && currentImageIndex > 0) {
      setCurrentImageIndex(prev => prev - 1);
    } else if (direction === 'next' && currentImageIndex < totalImages - 1) {
      setCurrentImageIndex(prev => prev + 1);
    }
  };

  const togglePlayback = () => {
    setIsPlaying(prev => !prev);
  };

  // Auto-play functionality
  useEffect(() => {
    if (isPlaying && totalImages > 1) {
      const interval = setInterval(() => {
        setCurrentImageIndex(prev => {
          if (prev >= totalImages - 1) {
            return 0; // Loop back to first image
          }
          return prev + 1;
        });
      }, 500); // Change image every 500ms

      return () => clearInterval(interval);
    }
  }, [isPlaying, totalImages]);

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          minHeight: 400,
          p: 3,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {loadingMessage}
        </Typography>
        <Box sx={{ width: '100%', maxWidth: 300, mt: 2 }}>
          <LinearProgress variant="determinate" value={loadingProgress} />
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
            {loadingProgress}%
          </Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        sx={{ m: 2 }}
        action={
          <IconButton color="inherit" size="small" onClick={initializeViewer}>
            <ResetIcon />
          </IconButton>
        }
      >
        <Typography variant="subtitle1" gutterBottom>
          DICOM Viewer Error
        </Typography>
        <Typography variant="body2">
          {error}
        </Typography>
      </Alert>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Study Information Header */}
      <Paper sx={{ p: 2, mb: 1 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom>
              {study.patient_name || `Patient ${study.patient_id}`}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {study.study_description} • {study.modality} • {study.study_date}
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="body2" align="right">
              Image {currentImageIndex + 1} of {totalImages}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ display: 'flex', flex: 1, gap: 1 }}>
        {/* Main Viewer */}
        <Paper sx={{ flex: 1, position: 'relative', minHeight: 400 }}>
          {/* Toolbar */}
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              left: 8,
              zIndex: 10,
              display: 'flex',
              gap: 1,
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
              borderRadius: 1,
              p: 0.5,
            }}
          >
            <Tooltip title="Zoom In">
              <IconButton size="small" onClick={handleZoomIn} sx={{ color: 'white' }}>
                <ZoomInIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Zoom Out">
              <IconButton size="small" onClick={handleZoomOut} sx={{ color: 'white' }}>
                <ZoomOutIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Rotate Left">
              <IconButton size="small" onClick={handleRotateLeft} sx={{ color: 'white' }}>
                <RotateLeftIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Rotate Right">
              <IconButton size="small" onClick={handleRotateRight} sx={{ color: 'white' }}>
                <RotateRightIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Reset View">
              <IconButton size="small" onClick={handleReset} sx={{ color: 'white' }}>
                <ResetIcon />
              </IconButton>
            </Tooltip>
            {totalImages > 1 && (
              <Tooltip title={isPlaying ? "Pause" : "Play"}>
                <IconButton size="small" onClick={togglePlayback} sx={{ color: 'white' }}>
                  {isPlaying ? <PauseIcon /> : <PlayIcon />}
                </IconButton>
              </Tooltip>
            )}
          </Box>

          {/* Image Display Area */}
          <Box
            ref={viewerRef}
            sx={{
              width: '100%',
              height: '100%',
              minHeight: 400,
              backgroundColor: '#000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Mock DICOM Image Display */}
            <Box
              sx={{
                width: 400,
                height: 400,
                backgroundColor: '#333',
                border: '2px solid #666',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transform: `scale(${zoom}) rotate(${rotation}deg)`,
                transition: 'transform 0.2s ease',
                backgroundImage: `
                  radial-gradient(circle at 50% 50%, 
                    rgba(255,255,255,0.8) 0%, 
                    rgba(255,255,255,0.4) 30%, 
                    rgba(255,255,255,0.1) 60%, 
                    rgba(0,0,0,0.2) 100%
                  )
                `,
              }}
            >
              <Typography variant="h4" sx={{ color: '#888', textAlign: 'center' }}>
                DICOM<br />
                {study.modality}<br />
                <Typography variant="body2" component="span">
                  {currentImageIndex + 1}/{totalImages}
                </Typography>
              </Typography>
            </Box>
          </Box>

          {/* Navigation Controls */}
          {totalImages > 1 && (
            <Box
              sx={{
                position: 'absolute',
                bottom: 8,
                left: '50%',
                transform: 'translateX(-50%)',
                display: 'flex',
                gap: 1,
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                borderRadius: 1,
                p: 0.5,
              }}
            >
              <IconButton
                size="small"
                onClick={() => handleImageNavigation('prev')}
                disabled={currentImageIndex === 0}
                sx={{ color: 'white' }}
              >
                ←
              </IconButton>
              <Typography variant="body2" sx={{ color: 'white', px: 1, py: 0.5 }}>
                {currentImageIndex + 1} / {totalImages}
              </Typography>
              <IconButton
                size="small"
                onClick={() => handleImageNavigation('next')}
                disabled={currentImageIndex === totalImages - 1}
                sx={{ color: 'white' }}
              >
                →
              </IconButton>
            </Box>
          )}
        </Paper>

        {/* Controls Panel */}
        <Paper sx={{ width: 300, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Image Controls
          </Typography>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Window/Level
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Width: {windowWidth}
                </Typography>
                <Slider
                  value={windowWidth}
                  onChange={handleWindowWidthChange}
                  min={1}
                  max={2000}
                  size="small"
                />
              </Box>
              <Box>
                <Typography variant="body2" gutterBottom>
                  Center: {windowCenter}
                </Typography>
                <Slider
                  value={windowCenter}
                  onChange={handleWindowCenterChange}
                  min={-1000}
                  max={1000}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Transform
              </Typography>
              <Typography variant="body2">
                Zoom: {zoom.toFixed(2)}x
              </Typography>
              <Typography variant="body2">
                Rotation: {rotation}°
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                Study Info
              </Typography>
              <Typography variant="body2">
                Modality: {study.modality}
              </Typography>
              <Typography variant="body2">
                Date: {study.study_date}
              </Typography>
              <Typography variant="body2">
                Images: {totalImages}
              </Typography>
            </CardContent>
          </Card>
        </Paper>
      </Box>
    </Box>
  );
};

export default WorkingDicomViewer;