import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
    Box, Typography, Paper, IconButton, Tooltip, 
    Grid, Chip, Button, Alert, LinearProgress,
    Stack, useMediaQuery, useTheme, Slider
} from '@mui/material';
import {
    ZoomIn, ZoomOut, RotateLeft, RotateRight, 
    RestartAlt, Fullscreen, PlayArrow, 
    Pause, SkipNext, SkipPrevious, Speed
} from '@mui/icons-material';
import type { Study } from '../../types';

interface MultiFrameDicomViewerProps {
    study: Study;
    onError?: (error: string) => void;
}

const MultiFrameDicomViewer: React.FC<MultiFrameDicomViewerProps> = ({ study, onError }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const currentImageRef = useRef<HTMLImageElement | null>(null);
    
    // Responsive design
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    
    // Core states
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [imageLoaded, setImageLoaded] = useState(false);
    
    // Image manipulation
    const [zoom, setZoom] = useState(1);
    const [rotation, setRotation] = useState(0);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    
    // Multi-slice support (updated to match AdvancedMedicalDicomViewer)
    const [loadedImages, setLoadedImages] = useState<HTMLImageElement[]>([]);
    const [currentSlice, setCurrentSlice] = useState(0);
    const [totalSlices, setTotalSlices] = useState(1);
    const [isPlaying, setIsPlaying] = useState(false);
    const [playSpeed, setPlaySpeed] = useState(2); // Slices per second
    const [autoScroll, setAutoScroll] = useState(false);
    
    // Build image URL properly with debugging
    const buildImageUrl = useCallback((filename: string) => {
        if (!filename) {
            console.log('🔍 buildImageUrl: No filename provided');
            return null;
        }
        
        let url: string;
        if (filename.startsWith('http')) {
            url = filename;
            console.log('🔍 buildImageUrl: Using full HTTP URL:', url);
        } else if (filename.startsWith('/')) {
            url = `http://localhost:8000${filename}`;
            console.log('🔍 buildImageUrl: Using absolute path:', url);
        } else {
            url = `http://localhost:8000/uploads/${study.patient_id}/${filename}`;
            console.log('🔍 buildImageUrl: Using relative path:', url);
        }
        
        return url;
    }, [study.patient_id]);
    
    // Helper function to load a single image with detailed error reporting
    const tryLoadMedicalImage = useCallback((url: string): Promise<boolean> => {
        return new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';

            img.onload = () => {
                console.log('✅ Image loaded successfully:', url);
                console.log('📐 Image dimensions:', img.width, 'x', img.height);
                currentImageRef.current = img;
                resolve(true);
            };

            img.onerror = (error) => {
                console.log('❌ Failed to load image:', url);
                console.log('❌ Error details:', error);
                
                // Try to fetch the URL to see what the actual error is
                fetch(url, { method: 'HEAD' })
                    .then(response => {
                        console.log(`📊 HTTP status for ${url}:`, response.status, response.statusText);
                        if (!response.ok) {
                            console.log('❌ HTTP error:', response.status, response.statusText);
                        }
                    })
                    .catch(fetchError => {
                        console.log('❌ Fetch error for', url, ':', fetchError.message);
                    });
                
                resolve(false);
            };

            console.log('🔄 Attempting to load image:', url);
            img.src = url;
        });
    }, []);
    
    // Draw image to canvas with transformations
    const drawImageToCanvas = useCallback((img: HTMLImageElement) => {
        const canvas = canvasRef.current;
        if (!canvas || !img) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Set canvas size to container
        const container = containerRef.current;
        if (container) {
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
        }

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Save context for transformations
        ctx.save();

        // Apply transformations
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;

        ctx.translate(centerX + pan.x, centerY + pan.y);
        ctx.rotate((rotation * Math.PI) / 180);
        ctx.scale(zoom, zoom);

        // Calculate image dimensions to fit canvas
        const imgAspect = img.width / img.height;
        const canvasAspect = canvas.width / canvas.height;
        
        let drawWidth = img.width;
        let drawHeight = img.height;
        
        if (imgAspect > canvasAspect) {
            drawWidth = canvas.width * 0.8;
            drawHeight = drawWidth / imgAspect;
        } else {
            drawHeight = canvas.height * 0.8;
            drawWidth = drawHeight * imgAspect;
        }

        // Draw image centered
        ctx.drawImage(img, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);

        // Restore context
        ctx.restore();

        // Draw slice information
        ctx.fillStyle = '#00ff00';
        ctx.font = '14px monospace';
        ctx.fillText(`Slice: ${currentSlice + 1}/${totalSlices}`, 10, 30);
        ctx.fillText(`Zoom: ${Math.round(zoom * 100)}%`, 10, 50);
        
    }, [zoom, rotation, pan, currentSlice, totalSlices]);
    
    // Load multi-slice DICOM images (updated approach)
    const loadMultiSliceDicom = useCallback(async (): Promise<boolean> => {
        try {
            console.log('🔍 Loading multi-slice DICOM for study:', study.study_uid || study.original_filename);
            setLoading(true);
            setError(null);
            
            const loadedImagesList: HTMLImageElement[] = [];
            
            // Build potential image sources from study data
            const imageSources: string[] = [];
            
            // Add image URLs from study
            if (study.image_urls && Array.isArray(study.image_urls)) {
                imageSources.push(...study.image_urls);
                console.log(`📋 Found ${study.image_urls.length} image URLs in study:`, study.image_urls);
            }
            
            // Add individual images from study (if available)
            if ((study as any).images && Array.isArray((study as any).images)) {
                (study as any).images.forEach((img: any) => {
                    if (img.image_url) {
                        imageSources.push(img.image_url);
                    }
                });
                console.log(`📋 Found ${(study as any).images.length} individual images in study:`, (study as any).images);
            }
            
            // Add fallback URLs
            if (study.dicom_url) {
                imageSources.push(study.dicom_url);
                console.log('📋 Added fallback DICOM URL:', study.dicom_url);
            }
            
            // Add original filename as fallback
            if (study.original_filename) {
                imageSources.push(study.original_filename);
                console.log('📋 Added original filename as fallback:', study.original_filename);
            }
            
            console.log('🎯 All image sources collected:', imageSources);
            
            console.log(`🎯 Total image sources to try: ${imageSources.length}`);
            
            if (imageSources.length === 0) {
                console.warn('⚠️ No image sources found in study data');
                setError('No image sources found in study data');
                setLoading(false);
                return false;
            }
            
            // Try to load each image source
            for (let i = 0; i < imageSources.length; i++) {
                const source = imageSources[i];
                const imageUrl = buildImageUrl(source);
                if (imageUrl) {
                    console.log(`🔍 [${i + 1}/${imageSources.length}] Attempting to load:`, imageUrl);
                    
                    const success = await tryLoadMedicalImage(imageUrl);
                    if (success && currentImageRef.current) {
                        console.log(`✅ [${i + 1}/${imageSources.length}] Successfully loaded slice from:`, imageUrl);
                        loadedImagesList.push(currentImageRef.current);
                        
                        // Update progress
                        setLoadedImages([...loadedImagesList]);
                        setTotalSlices(loadedImagesList.length);
                        
                        // Set the first successful image as the current display
                        if (loadedImagesList.length === 1) {
                            drawImageToCanvas(currentImageRef.current);
                            setImageLoaded(true);
                        }
                    } else {
                        console.log(`❌ [${i + 1}/${imageSources.length}] Failed to load:`, imageUrl);
                    }
                }
            }
            
            // Final update
            if (loadedImagesList.length > 0) {
                setLoadedImages(loadedImagesList);
                setTotalSlices(loadedImagesList.length);
                setLoading(false);
                console.log(`✅ Successfully loaded ${loadedImagesList.length} slices for multi-slice viewing`);
                return true;
            } else {
                const errorMsg = `No images could be loaded from ${imageSources.length} sources`;
                console.error('❌', errorMsg);
                setError(errorMsg);
                setLoading(false);
                return false;
            }
            
        } catch (error) {
            const errorMsg = `Error loading multi-slice DICOM: ${error}`;
            console.error('❌', errorMsg);
            setError(errorMsg);
            setLoading(false);
            return false;
        }
    }, [study, buildImageUrl, tryLoadMedicalImage, drawImageToCanvas]);
    
    // Auto-scroll functionality for cine mode
    useEffect(() => {
        if (autoScroll && isPlaying && totalSlices > 1) {
            const interval = setInterval(() => {
                setCurrentSlice(prev => (prev + 1) % totalSlices);
            }, 1000 / playSpeed);
            return () => clearInterval(interval);
        }
    }, [autoScroll, isPlaying, playSpeed, totalSlices]);
    
    // Handle slice changes - switch to different loaded image
    useEffect(() => {
        if (loadedImages.length > 0 && currentSlice < loadedImages.length) {
            const imageForSlice = loadedImages[currentSlice];
            currentImageRef.current = imageForSlice;
            drawImageToCanvas(imageForSlice);
        }
    }, [currentSlice, loadedImages, drawImageToCanvas]);
    
    // Keyboard navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    setCurrentSlice(prev => Math.max(0, prev - 1));
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    setCurrentSlice(prev => Math.min(totalSlices - 1, prev + 1));
                    break;
                case ' ':
                    e.preventDefault();
                    setIsPlaying(!isPlaying);
                    setAutoScroll(!isPlaying);
                    break;
                case 'Home':
                    e.preventDefault();
                    setCurrentSlice(0);
                    break;
                case 'End':
                    e.preventDefault();
                    setCurrentSlice(totalSlices - 1);
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isPlaying, totalSlices]);
    
    // Initialize multi-slice loading on mount
    useEffect(() => {
        loadMultiSliceDicom();
    }, [loadMultiSliceDicom]);
    
    // Control handlers
    const handleZoomIn = () => setZoom(prev => Math.min(prev * 1.2, 5));
    const handleZoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.2));
    const handleRotateLeft = () => setRotation(prev => prev - 90);
    const handleRotateRight = () => setRotation(prev => prev + 90);
    const handleReset = () => {
        setZoom(1);
        setRotation(0);
        setPan({ x: 0, y: 0 });
    };
    
    if (loading) {
        return (
            <Box sx={{ p: 4, textAlign: 'center' }}>
                <LinearProgress sx={{ mb: 2 }} />
                <Typography>Loading DICOM data for {study.patient_id}...</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Study: {study.study_uid || study.original_filename}
                </Typography>
                {loadedImages.length > 0 && (
                    <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
                        Loaded {loadedImages.length} slice{loadedImages.length !== 1 ? 's' : ''}
                    </Typography>
                )}
            </Box>
        );
    }
    
    if (error) {
        return (
            <Alert severity="error" sx={{ m: 2 }}>
                <Typography variant="h6">Error Loading DICOM</Typography>
                <Typography>{error}</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                    Study: {study.study_uid || study.original_filename}
                </Typography>
                <Typography variant="body2">
                    Patient: {study.patient_id}
                </Typography>
                {study.image_urls && (
                    <Typography variant="body2">
                        Available URLs: {Array.isArray(study.image_urls) ? study.image_urls.length : 'Invalid format'}
                    </Typography>
                )}
                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    <Button 
                        variant="outlined" 
                        size="small" 
                        onClick={() => loadMultiSliceDicom()}
                    >
                        Retry Loading
                    </Button>
                    <Button 
                        variant="text" 
                        size="small" 
                        onClick={() => {
                            console.log('🔍 Debug: Full study object:', study);
                            console.log('🔍 Debug: Study image_urls:', study.image_urls);
                            console.log('🔍 Debug: Study dicom_url:', study.dicom_url);
                            console.log('🔍 Debug: Study original_filename:', study.original_filename);
                        }}
                    >
                        Debug Info
                    </Button>
                </Box>
            </Alert>
        );
    }
    
    return (
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#000' }}>
            {/* Header */}
            <Paper sx={{ p: 1, bgcolor: '#1a1a1a', color: '#00ff00' }}>
                <Grid container alignItems="center" spacing={2}>
                    <Grid item xs={12} md={8}>
                        <Typography variant="h6">
                            🏥 Multi-Slice DICOM Viewer
                        </Typography>
                        <Stack direction="row" spacing={1}>
                            <Chip label={study.patient_id} size="small" />
                            <Chip label={study.original_filename || study.study_uid} size="small" variant="outlined" />
                            <Chip label={`${totalSlices} slices`} size="small" color="success" />
                            {totalSlices > 1 && (
                                <Chip label="Multi-slice Series" size="small" color="warning" />
                            )}
                            {loadedImages.length > 0 && (
                                <Chip label="Enhanced Navigation" size="small" color="info" />
                            )}
                        </Stack>
                    </Grid>
                </Grid>
            </Paper>
            
            {/* Controls */}
            <Paper sx={{ p: 1, bgcolor: '#1a1a1a' }}>
                <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                    {/* Zoom Controls */}
                    <Tooltip title="Zoom In">
                        <IconButton onClick={handleZoomIn} size="small" sx={{ color: '#00ff00' }}>
                            <ZoomIn />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Zoom Out">
                        <IconButton onClick={handleZoomOut} size="small" sx={{ color: '#00ff00' }}>
                            <ZoomOut />
                        </IconButton>
                    </Tooltip>
                    
                    {/* Rotation Controls */}
                    <Tooltip title="Rotate Left">
                        <IconButton onClick={handleRotateLeft} size="small" sx={{ color: '#00ff00' }}>
                            <RotateLeft />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Rotate Right">
                        <IconButton onClick={handleRotateRight} size="small" sx={{ color: '#00ff00' }}>
                            <RotateRight />
                        </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Reset">
                        <IconButton onClick={handleReset} size="small" sx={{ color: '#00ff00' }}>
                            <RestartAlt />
                        </IconButton>
                    </Tooltip>
                    
                    {/* Slice Navigation (Updated) */}
                    {totalSlices > 1 && (
                        <>
                            <Tooltip title="Previous Slice">
                                <IconButton 
                                    onClick={() => setCurrentSlice(prev => Math.max(0, prev - 1))} 
                                    disabled={currentSlice === 0}
                                    size="small" 
                                    sx={{ color: '#00ff00' }}
                                >
                                    <SkipPrevious />
                                </IconButton>
                            </Tooltip>
                            
                            <Tooltip title={isPlaying ? "Pause" : "Play"}>
                                <IconButton 
                                    onClick={() => {
                                        setIsPlaying(!isPlaying);
                                        setAutoScroll(!isPlaying);
                                    }} 
                                    size="small" 
                                    sx={{ color: '#00ff00' }}
                                >
                                    {isPlaying ? <Pause /> : <PlayArrow />}
                                </IconButton>
                            </Tooltip>
                            
                            <Tooltip title="Next Slice">
                                <IconButton 
                                    onClick={() => setCurrentSlice(prev => Math.min(totalSlices - 1, prev + 1))} 
                                    disabled={currentSlice === totalSlices - 1}
                                    size="small" 
                                    sx={{ color: '#00ff00' }}
                                >
                                    <SkipNext />
                                </IconButton>
                            </Tooltip>
                            
                            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '120px' }}>
                                <Typography variant="caption" sx={{ color: '#00ff00', fontSize: '0.75rem', mb: 0.5 }}>
                                    Slice {currentSlice + 1}/{totalSlices}
                                </Typography>
                                <Slider
                                    value={currentSlice}
                                    min={0}
                                    max={totalSlices - 1}
                                    step={1}
                                    onChange={(_, value) => setCurrentSlice(value as number)}
                                    sx={{
                                        width: '100px',
                                        height: 4,
                                        color: '#00ff00',
                                        '& .MuiSlider-thumb': {
                                            width: 12,
                                            height: 12,
                                            backgroundColor: '#00ff00',
                                        },
                                        '& .MuiSlider-track': {
                                            backgroundColor: '#00ff00',
                                        },
                                        '& .MuiSlider-rail': {
                                            backgroundColor: 'rgba(0, 255, 0, 0.3)',
                                        }
                                    }}
                                />
                            </Box>
                            
                            {/* Play Speed */}
                            <Tooltip title="Play Speed">
                                <IconButton size="small" sx={{ color: '#00ff00' }}>
                                    <Speed />
                                </IconButton>
                            </Tooltip>
                            <Slider
                                value={playSpeed}
                                min={1}
                                max={10}
                                onChange={(_, value) => setPlaySpeed(value as number)}
                                sx={{ width: 80, color: '#00ff00' }}
                                size="small"
                            />
                            <Typography variant="caption" sx={{ color: '#00ff00', ml: 1 }}>
                                {playSpeed} fps
                            </Typography>
                        </>
                    )}
                </Stack>
            </Paper>
            
            {/* Canvas */}
            <Box 
                ref={containerRef}
                sx={{ 
                    flex: 1, 
                    position: 'relative',
                    overflow: 'hidden',
                    bgcolor: '#000'
                }}
            >
                <canvas
                    ref={canvasRef}
                    style={{
                        width: '100%',
                        height: '100%',
                        cursor: 'crosshair'
                    }}
                />
                
                {!imageLoaded && !loading && (
                    <Box
                        sx={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            color: '#00ff00',
                            textAlign: 'center',
                            p: 3,
                            border: '1px dashed #00ff00',
                            borderRadius: 2
                        }}
                    >
                        <Typography variant="h6" sx={{ mb: 2 }}>No DICOM image loaded</Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            Study: {study.study_uid || 'Unknown'}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            Patient: {study.patient_id || 'Unknown'}
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 2 }}>
                            File: {study.original_filename || 'Unknown'}
                        </Typography>
                        <Button 
                            variant="outlined" 
                            size="small" 
                            onClick={() => loadMultiSliceDicom()}
                            sx={{ color: '#00ff00', borderColor: '#00ff00' }}
                        >
                            Try Loading Again
                        </Button>
                    </Box>
                )}
            </Box>
        </Box>
    );
};

export default MultiFrameDicomViewer;