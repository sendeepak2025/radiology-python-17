import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Button,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  RotateLeft as RotateLeftIcon,
  RotateRight as RotateRightIcon,
  ThreeDRotation as RotateIcon,
  Refresh as ResetIcon,
  Fullscreen as FullscreenIcon,
  CameraAlt as ScreenshotIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon
} from '@mui/icons-material';
import { Study } from '../../types';

// Fix cornerstone imports with proper typing
declare global {
  interface Window {
    cornerstone: {
      loadImage: (imageId: string) => Promise<any>;
      // Add other cornerstone methods as needed
    };
    cornerstoneWADOImageLoader: any;
  }
}

const cornerstone = window.cornerstone;

interface ThreeDViewerProps {
  study: Study;
  imageIds: string[];
  settings: {
    renderMode: 'volume' | 'mip' | 'surface' | 'raycast';
    opacity: number;
    threshold: number;
    windowWidth: number;
    windowCenter: number;
    colorMap: 'grayscale' | 'hot' | 'cool' | 'bone';
  };
  onSettingsChange: (settings: any) => void;
}

interface ViewportState {
  rotation: { x: number; y: number; z: number };
  zoom: number;
  pan: { x: number; y: number };
}

interface VolumeData {
  dimensions: { width: number; height: number; depth: number };
  spacing: { x: number; y: number; z: number };
  data: Uint16Array;
  minValue: number;
  maxValue: number;
}

const ThreeDViewer: React.FC<ThreeDViewerProps> = ({
  study,
  imageIds,
  settings,
  onSettingsChange
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const glRef = useRef<WebGLRenderingContext | null>(null);
  const programRef = useRef<WebGLProgram | null>(null);
  const animationRef = useRef<number>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [volumeData, setVolumeData] = useState<VolumeData | null>(null);
  const [isInteracting, setIsInteracting] = useState(false);
  const [viewport, setViewport] = useState<ViewportState>({
    rotation: { x: 0, y: 0, z: 0 },
    zoom: 1,
    pan: { x: 0, y: 0 }
  });

  // Enhanced vertex shader for volume rendering
  const vertexShaderSource = `
    attribute vec3 a_position;
    uniform mat4 u_modelViewMatrix;
    uniform mat4 u_projectionMatrix;
    varying vec3 v_rayDirection;
    varying vec3 v_rayOrigin;
    
    void main() {
      vec4 worldPosition = u_modelViewMatrix * vec4(a_position, 1.0);
      gl_Position = u_projectionMatrix * worldPosition;
      
      // Calculate ray direction for volume rendering
      v_rayDirection = normalize(a_position);
      v_rayOrigin = a_position;
    }
  `;

  // Enhanced fragment shader with proper volume rendering
  const fragmentShaderSource = `
    precision highp float;
    
    varying vec3 v_rayDirection;
    varying vec3 v_rayOrigin;
    
    uniform sampler2D u_volumeTexture;
    uniform vec3 u_volumeDimensions;
    uniform vec3 u_volumeSpacing;
    uniform float u_opacity;
    uniform float u_threshold;
    uniform float u_windowWidth;
    uniform float u_windowCenter;
    uniform int u_renderMode;
    uniform int u_colorMap;
    uniform float u_stepSize;
    
    vec4 getColorFromValue(float value) {
      // Apply windowing
      float windowMin = u_windowCenter - u_windowWidth / 2.0;
      float windowMax = u_windowCenter + u_windowWidth / 2.0;
      float normalizedValue = (value - windowMin) / (windowMax - windowMin);
      normalizedValue = clamp(normalizedValue, 0.0, 1.0);
      
      vec3 color;
      if (u_colorMap == 0) { // Grayscale
        color = vec3(normalizedValue);
      } else if (u_colorMap == 1) { // Hot
        color = vec3(normalizedValue, normalizedValue * 0.5, 0.0);
      } else if (u_colorMap == 2) { // Cool
        color = vec3(0.0, normalizedValue * 0.5, normalizedValue);
      } else { // Bone
        color = vec3(normalizedValue * 0.8, normalizedValue * 0.9, normalizedValue);
      }
      
      return vec4(color, normalizedValue > u_threshold ? u_opacity : 0.0);
    }
    
    float sampleVolume(vec3 position) {
      // Convert 3D position to texture coordinates
      vec3 texCoord = (position + 1.0) * 0.5;
      
      if (texCoord.x < 0.0 || texCoord.x > 1.0 ||
          texCoord.y < 0.0 || texCoord.y > 1.0 ||
          texCoord.z < 0.0 || texCoord.z > 1.0) {
        return 0.0;
      }
      
      // Sample from 3D texture (simulated with 2D texture)
      float slice = texCoord.z * u_volumeDimensions.z;
      float sliceIndex = floor(slice);
      float sliceFraction = slice - sliceIndex;
      
      // Calculate texture coordinates for current slice
      vec2 sliceCoord = vec2(
        (texCoord.x + sliceIndex) / u_volumeDimensions.z,
        texCoord.y
      );
      
      return texture2D(u_volumeTexture, sliceCoord).r;
    }
    
    vec4 volumeRaycast() {
      vec3 rayDir = normalize(v_rayDirection);
      vec3 rayPos = v_rayOrigin;
      
      vec4 color = vec4(0.0);
      float stepSize = u_stepSize;
      
      for (int i = 0; i < 512; i++) {
        if (color.a >= 0.95) break;
        
        float sample = sampleVolume(rayPos);
        vec4 sampleColor = getColorFromValue(sample);
        
        // Front-to-back compositing
        color.rgb += sampleColor.rgb * sampleColor.a * (1.0 - color.a);
        color.a += sampleColor.a * (1.0 - color.a);
        
        rayPos += rayDir * stepSize;
        
        // Check bounds
        if (abs(rayPos.x) > 1.0 || abs(rayPos.y) > 1.0 || abs(rayPos.z) > 1.0) {
          break;
        }
      }
      
      return color;
    }
    
    vec4 maximumIntensityProjection() {
      vec3 rayDir = normalize(v_rayDirection);
      vec3 rayPos = v_rayOrigin;
      
      float maxIntensity = 0.0;
      float stepSize = u_stepSize;
      
      for (int i = 0; i < 256; i++) {
        float sample = sampleVolume(rayPos);
        maxIntensity = max(maxIntensity, sample);
        
        rayPos += rayDir * stepSize;
        
        if (abs(rayPos.x) > 1.0 || abs(rayPos.y) > 1.0 || abs(rayPos.z) > 1.0) {
          break;
        }
      }
      
      return getColorFromValue(maxIntensity);
    }
    
    void main() {
      vec4 color;
      
      if (u_renderMode == 0) { // Volume rendering
        color = volumeRaycast();
      } else if (u_renderMode == 1) { // MIP
        color = maximumIntensityProjection();
      } else if (u_renderMode == 2) { // Surface rendering
        color = volumeRaycast(); // Simplified surface rendering
      } else { // Raycast
        color = volumeRaycast();
      }
      
      gl_FragColor = color;
    }
  `;

  // Load and process DICOM images into volume data
  const loadVolumeData = useCallback(async () => {
    if (!imageIds || imageIds.length === 0) {
      setError('No image IDs provided');
      return;
    }

    try {
      setIsLoading(true);
      setError('');

      // Load all DICOM images
      const images = await Promise.all(
        imageIds.map((imageId: string) => cornerstone.loadImage(imageId))
      );

      if (images.length === 0) {
        throw new Error('No images loaded');
      }

      // Extract volume dimensions and spacing
      const firstImage = images[0];
      const dimensions = {
        width: firstImage.width,
        height: firstImage.height,
        depth: images.length
      };

      const spacing = {
        x: firstImage.columnPixelSpacing || 1.0,
        y: firstImage.rowPixelSpacing || 1.0,
        z: images.length > 1 ? Math.abs(
          (images[1].imagePositionPatient?.[2] || 0) - 
          (firstImage.imagePositionPatient?.[2] || 0)
        ) || 1.0 : 1.0
      };

      // Create volume data array
      const totalVoxels = dimensions.width * dimensions.height * dimensions.depth;
      const volumeArray = new Uint16Array(totalVoxels);
      
      let minValue = Infinity;
      let maxValue = -Infinity;

      // Copy pixel data from all images
      images.forEach((image: any, sliceIndex: number) => {
        const pixelData = image.getPixelData();
        const sliceOffset = sliceIndex * dimensions.width * dimensions.height;
        
        for (let i = 0; i < pixelData.length; i++) {
          const value = pixelData[i];
          volumeArray[sliceOffset + i] = value;
          minValue = Math.min(minValue, value);
          maxValue = Math.max(maxValue, value);
        }
      });

      const volume: VolumeData = {
        dimensions,
        spacing,
        data: volumeArray,
        minValue,
        maxValue
      };

      setVolumeData(volume);
      
      // Update settings with appropriate window/level
      onSettingsChange({
        ...settings,
        windowWidth: maxValue - minValue,
        windowCenter: (maxValue + minValue) / 2
      });

    } catch (err) {
      console.error('Error loading volume data:', err);
      setError(`Failed to load volume data: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  }, [imageIds, settings, onSettingsChange]);

  // Create WebGL texture from volume data
  const createVolumeTexture = useCallback((gl: WebGLRenderingContext, volume: VolumeData) => {
    const texture = gl.createTexture();
    if (!texture) return null;

    gl.bindTexture(gl.TEXTURE_2D, texture);
    
    // Create 2D texture atlas from 3D volume
    const { width, height, depth } = volume.dimensions;
    const atlasWidth = width * depth;
    const atlasHeight = height;
    
    // Convert Uint16 to Uint8 for WebGL compatibility
    const normalizedData = new Uint8Array(atlasWidth * atlasHeight);
    const range = volume.maxValue - volume.minValue;
    
    for (let z = 0; z < depth; z++) {
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const volumeIndex = z * width * height + y * width + x;
          const atlasIndex = y * atlasWidth + z * width + x;
          
          const normalizedValue = range > 0 ? 
            ((volume.data[volumeIndex] - volume.minValue) / range) * 255 : 0;
          normalizedData[atlasIndex] = Math.floor(normalizedValue);
        }
      }
    }

    gl.texImage2D(
      gl.TEXTURE_2D, 0, gl.LUMINANCE,
      atlasWidth, atlasHeight, 0,
      gl.LUMINANCE, gl.UNSIGNED_BYTE,
      normalizedData
    );

    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    return texture;
  }, []);

  const createShader = useCallback((gl: WebGLRenderingContext, type: number, source: string) => {
    const shader = gl.createShader(type);
    if (!shader) return null;
    
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error('Shader compilation error:', gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }
    
    return shader;
  }, []);

  const createProgram = useCallback((gl: WebGLRenderingContext) => {
    const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
    const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);
    
    if (!vertexShader || !fragmentShader) return null;
    
    const program = gl.createProgram();
    if (!program) return null;
    
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Program linking error:', gl.getProgramInfoLog(program));
      gl.deleteProgram(program);
      return null;
    }
    
    return program;
  }, [createShader, vertexShaderSource, fragmentShaderSource]);

  // Create cube geometry for volume rendering
  const createCubeGeometry = useCallback(() => {
    const vertices = new Float32Array([
      // Front face
      -1, -1,  1,   1, -1,  1,   1,  1,  1,  -1,  1,  1,
      // Back face
      -1, -1, -1,  -1,  1, -1,   1,  1, -1,   1, -1, -1,
      // Top face
      -1,  1, -1,  -1,  1,  1,   1,  1,  1,   1,  1, -1,
      // Bottom face
      -1, -1, -1,   1, -1, -1,   1, -1,  1,  -1, -1,  1,
      // Right face
       1, -1, -1,   1,  1, -1,   1,  1,  1,   1, -1,  1,
      // Left face
      -1, -1, -1,  -1, -1,  1,  -1,  1,  1,  -1,  1, -1
    ]);

    const indices = new Uint16Array([
      0,  1,  2,    0,  2,  3,    // front
      4,  5,  6,    4,  6,  7,    // back
      8,  9,  10,   8,  10, 11,   // top
      12, 13, 14,   12, 14, 15,   // bottom
      16, 17, 18,   16, 18, 19,   // right
      20, 21, 22,   20, 22, 23    // left
    ]);

    return { vertices, indices };
  }, []);

  const initWebGL = useCallback(async () => {
    const canvas = canvasRef.current;
    if (!canvas || !volumeData) return;

    const gl = canvas.getContext('webgl');
    if (!gl) {
      setError('WebGL not supported');
      return;
    }

    glRef.current = gl;
    
    // Enable extensions
    const ext = gl.getExtension('OES_texture_float');
    if (!ext) {
      console.warn('OES_texture_float not supported');
    }
    
    // Enable depth testing and blending
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    
    const program = createProgram(gl);
    if (!program) {
      setError('Failed to create WebGL program');
      return;
    }
    
    programRef.current = program;
    gl.useProgram(program);
    
    // Create and bind geometry
    const geometry = createCubeGeometry();
    
    const vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, geometry.vertices, gl.STATIC_DRAW);
    
    const indexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, geometry.indices, gl.STATIC_DRAW);
    
    const positionLocation = gl.getAttribLocation(program, 'a_position');
    gl.enableVertexAttribArray(positionLocation);
    gl.vertexAttribPointer(positionLocation, 3, gl.FLOAT, false, 0, 0);
    
    // Create volume texture
    const volumeTexture = createVolumeTexture(gl, volumeData);
    if (!volumeTexture) {
      setError('Failed to create volume texture');
      return;
    }
    
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, volumeTexture);
    
    const textureLocation = gl.getUniformLocation(program, 'u_volumeTexture');
    gl.uniform1i(textureLocation, 0);
    
    setIsLoading(false);
    render();
  }, [volumeData, createProgram, createCubeGeometry, createVolumeTexture]);

  const render = useCallback(() => {
    const gl = glRef.current;
    const canvas = canvasRef.current;
    const program = programRef.current;
    if (!gl || !canvas || !program || !volumeData) return;

    // Set viewport
    gl.viewport(0, 0, canvas.width, canvas.height);
    
    // Clear canvas
    gl.clearColor(0.0, 0.0, 0.0, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    
    // Create matrices
    const modelViewMatrix = createModelViewMatrix();
    const projectionMatrix = createProjectionMatrix(canvas.width / canvas.height);
    
    // Set uniforms
    const modelViewLocation = gl.getUniformLocation(program, 'u_modelViewMatrix');
    const projectionLocation = gl.getUniformLocation(program, 'u_projectionMatrix');
    const volumeDimensionsLocation = gl.getUniformLocation(program, 'u_volumeDimensions');
    const volumeSpacingLocation = gl.getUniformLocation(program, 'u_volumeSpacing');
    const opacityLocation = gl.getUniformLocation(program, 'u_opacity');
    const thresholdLocation = gl.getUniformLocation(program, 'u_threshold');
    const windowWidthLocation = gl.getUniformLocation(program, 'u_windowWidth');
    const windowCenterLocation = gl.getUniformLocation(program, 'u_windowCenter');
    const renderModeLocation = gl.getUniformLocation(program, 'u_renderMode');
    const colorMapLocation = gl.getUniformLocation(program, 'u_colorMap');
    const stepSizeLocation = gl.getUniformLocation(program, 'u_stepSize');
    
    gl.uniformMatrix4fv(modelViewLocation, false, modelViewMatrix);
    gl.uniformMatrix4fv(projectionLocation, false, projectionMatrix);
    gl.uniform3f(volumeDimensionsLocation, volumeData.dimensions.width, volumeData.dimensions.height, volumeData.dimensions.depth);
    gl.uniform3f(volumeSpacingLocation, volumeData.spacing.x, volumeData.spacing.y, volumeData.spacing.z);
    gl.uniform1f(opacityLocation, settings.opacity);
    gl.uniform1f(thresholdLocation, settings.threshold);
    gl.uniform1f(windowWidthLocation, settings.windowWidth);
    gl.uniform1f(windowCenterLocation, settings.windowCenter);
    
    const renderModeMap = { volume: 0, mip: 1, surface: 2, raycast: 3 };
    gl.uniform1i(renderModeLocation, renderModeMap[settings.renderMode]);
    
    const colorMapMap = { grayscale: 0, hot: 1, cool: 2, bone: 3 };
    gl.uniform1i(colorMapLocation, colorMapMap[settings.colorMap]);
    
    // Adaptive step size based on quality vs performance
    const stepSize = isInteracting ? 0.01 : 0.005;
    gl.uniform1f(stepSizeLocation, stepSize);
    
    // Draw
    gl.drawElements(gl.TRIANGLES, 36, gl.UNSIGNED_SHORT, 0);
    
    if (!isInteracting) {
      animationRef.current = requestAnimationFrame(render);
    }
  }, [settings, viewport, volumeData, isInteracting]);

  // Enhanced matrix creation with proper rotations
  const createModelViewMatrix = () => {
    const matrix = new Float32Array(16);
    
    // Identity matrix
    matrix[0] = 1; matrix[5] = 1; matrix[10] = 1; matrix[15] = 1;
    
    // Apply transformations
    const { rotation, zoom, pan } = viewport;
    
    // Translation
    matrix[12] = pan.x;
    matrix[13] = pan.y;
    matrix[14] = -5 / zoom;
    
    // Apply rotations (simplified)
    const cosX = Math.cos(rotation.x * Math.PI / 180);
    const sinX = Math.sin(rotation.x * Math.PI / 180);
    const cosY = Math.cos(rotation.y * Math.PI / 180);
    const sinY = Math.sin(rotation.y * Math.PI / 180);
    
    // Rotation around Y axis
    matrix[0] = cosY;
    matrix[2] = sinY;
    matrix[8] = -sinY;
    matrix[10] = cosY;
    
    // Rotation around X axis
    matrix[5] = cosX;
    matrix[6] = -sinX;
    matrix[9] = sinX;
    matrix[10] *= cosX;
    
    return matrix;
  };

  const createProjectionMatrix = (aspectRatio: number) => {
    const matrix = new Float32Array(16);
    const fov = Math.PI / 4;
    const near = 0.1;
    const far = 100;
    
    const f = Math.tan(Math.PI * 0.5 - 0.5 * fov);
    const rangeInv = 1.0 / (near - far);
    
    matrix[0] = f / aspectRatio;
    matrix[5] = f;
    matrix[10] = (near + far) * rangeInv;
    matrix[11] = -1;
    matrix[14] = near * far * rangeInv * 2;
    
    return matrix;
  };

  // Mouse interaction handlers
  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    setIsInteracting(true);
    const startX = event.clientX;
    const startY = event.clientY;
    const startRotation = { ...viewport.rotation };
    const startPan = { ...viewport.pan };

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - startX;
      const deltaY = e.clientY - startY;

      if (event.shiftKey) {
        // Pan
        setViewport(prev => ({
          ...prev,
          pan: {
            x: startPan.x + deltaX * 0.01,
            y: startPan.y - deltaY * 0.01
          }
        }));
      } else {
        // Rotate
        setViewport(prev => ({
          ...prev,
          rotation: {
            x: startRotation.x + deltaY * 0.5,
            y: startRotation.y + deltaX * 0.5,
            z: prev.rotation.z
          }
        }));
      }
    };

    const handleMouseUp = () => {
      setIsInteracting(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      render(); // Resume animation
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [viewport, render]);

  const handleWheel = useCallback((event: React.WheelEvent) => {
    event.preventDefault();
    const delta = event.deltaY > 0 ? 0.9 : 1.1;
    setViewport(prev => ({
      ...prev,
      zoom: Math.max(0.1, Math.min(10, prev.zoom * delta))
    }));
  }, []);

  // Load volume data when imageIds change
  useEffect(() => {
    if (imageIds && imageIds.length > 0) {
      loadVolumeData();
    }
  }, [imageIds, loadVolumeData]);

  // Initialize WebGL when volume data is ready
  useEffect(() => {
    if (volumeData) {
      initWebGL();
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [volumeData, initWebGL]);

  // Re-render when settings change
  useEffect(() => {
    if (!isInteracting) {
      render();
    }
  }, [settings, viewport, render, isInteracting]);

  const handleRotate = (axis: 'x' | 'y' | 'z', delta: number) => {
    setViewport(prev => ({
      ...prev,
      rotation: {
        ...prev.rotation,
        [axis]: prev.rotation[axis] + delta
      }
    }));
  };

  const handleReset = () => {
    setViewport({
      rotation: { x: 0, y: 0, z: 0 },
      zoom: 1,
      pan: { x: 0, y: 0 }
    });
  };

  const handleScreenshot = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const link = document.createElement('a');
    link.download = `3d-view-${study.study_uid}-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        3D Rendering Error: {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Enhanced 3D Controls */}
      <Card sx={{ mb: 1 }}>
        <CardContent sx={{ py: 1 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Render Mode</InputLabel>
                <Select
                  value={settings.renderMode}
                  onChange={(e) => onSettingsChange({ 
                    ...settings, 
                    renderMode: e.target.value as 'volume' | 'mip' | 'surface' | 'raycast'
                  })}
                >
                  <MenuItem value="volume">Volume Rendering</MenuItem>
                  <MenuItem value="mip">Maximum Intensity</MenuItem>
                  <MenuItem value="surface">Surface Rendering</MenuItem>
                  <MenuItem value="raycast">Raycast</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Color Map</InputLabel>
                <Select
                  value={settings.colorMap}
                  onChange={(e) => onSettingsChange({ 
                    ...settings, 
                    colorMap: e.target.value as 'grayscale' | 'hot' | 'cool' | 'bone'
                  })}
                >
                  <MenuItem value="grayscale">Grayscale</MenuItem>
                  <MenuItem value="hot">Hot</MenuItem>
                  <MenuItem value="cool">Cool</MenuItem>
                  <MenuItem value="bone">Bone</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={6} sm={3} md={2}>
              <Typography variant="caption">Opacity</Typography>
              <Slider
                size="small"
                value={settings.opacity}
                onChange={(_, value) => onSettingsChange({ 
                  ...settings, 
                  opacity: value as number 
                })}
                min={0}
                max={1}
                step={0.05}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={6} sm={3} md={2}>
              <Typography variant="caption">Threshold</Typography>
              <Slider
                size="small"
                value={settings.threshold}
                onChange={(_, value) => onSettingsChange({ 
                  ...settings, 
                  threshold: value as number 
                })}
                min={0}
                max={1}
                step={0.05}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={6} sm={3} md={2}>
              <Typography variant="caption">Window Width</Typography>
              <Slider
                size="small"
                value={settings.windowWidth}
                onChange={(_, value) => onSettingsChange({ 
                  ...settings, 
                  windowWidth: value as number 
                })}
                min={1}
                max={4000}
                step={10}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={6} sm={3} md={2}>
              <Typography variant="caption">Window Center</Typography>
              <Slider
                size="small"
                value={settings.windowCenter}
                onChange={(_, value) => onSettingsChange({ 
                  ...settings, 
                  windowCenter: value as number 
                })}
                min={-1000}
                max={3000}
                step={10}
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={12} md={12}>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Tooltip title="Rotate Left">
                  <IconButton size="small" onClick={() => handleRotate('y', -15)}>
                    <RotateLeftIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Rotate Right">
                  <IconButton size="small" onClick={() => handleRotate('y', 15)}>
                    <RotateRightIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Rotate Up">
                  <IconButton size="small" onClick={() => handleRotate('x', -15)}>
                    <RotateIcon style={{ transform: 'rotate(90deg)' }} />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Rotate Down">
                  <IconButton size="small" onClick={() => handleRotate('x', 15)}>
                    <RotateIcon style={{ transform: 'rotate(-90deg)' }} />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Zoom In">
                  <IconButton size="small" onClick={() => setViewport(prev => ({ ...prev, zoom: prev.zoom * 1.2 }))}>
                    <ZoomInIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Zoom Out">
                  <IconButton size="small" onClick={() => setViewport(prev => ({ ...prev, zoom: prev.zoom * 0.8 }))}>
                    <ZoomOutIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Reset View">
                  <IconButton size="small" onClick={handleReset}>
                    <ResetIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Screenshot">
                  <IconButton size="small" onClick={handleScreenshot}>
                    <ScreenshotIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Enhanced 3D Canvas */}
      <Box sx={{ flex: 1, position: 'relative', bgcolor: 'black' }}>
        {isLoading && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 1,
              textAlign: 'center'
            }}
          >
            <CircularProgress />
            <Typography variant="body2" sx={{ mt: 1, color: 'white' }}>
              Loading DICOM Volume Data...
            </Typography>
          </Box>
        )}
        
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          style={{
            width: '100%',
            height: '100%',
            display: 'block',
            cursor: isInteracting ? 'grabbing' : 'grab'
          }}
          onMouseDown={handleMouseDown}
          onWheel={handleWheel}
        />
        
        {/* Enhanced Overlay Info */}
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            left: 8,
            color: 'white',
            bgcolor: 'rgba(0,0,0,0.8)',
            p: 1,
            borderRadius: 1,
            fontSize: '0.75rem'
          }}
        >
          <Typography variant="caption" display="block">
            3D {settings.renderMode.toUpperCase()} | {settings.colorMap.toUpperCase()}
          </Typography>
          <Typography variant="caption" display="block">
            Study: {study.study_uid}
          </Typography>
          {volumeData && (
            <Typography variant="caption" display="block">
              Volume: {volumeData.dimensions.width}×{volumeData.dimensions.height}×{volumeData.dimensions.depth}
            </Typography>
          )}
        </Box>
        
        {/* Interaction Help */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            color: 'white',
            bgcolor: 'rgba(0,0,0,0.7)',
            p: 1,
            borderRadius: 1,
            fontSize: '0.7rem'
          }}
        >
          <Typography variant="caption" display="block">
            Mouse: Rotate | Shift+Mouse: Pan | Wheel: Zoom
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default ThreeDViewer;