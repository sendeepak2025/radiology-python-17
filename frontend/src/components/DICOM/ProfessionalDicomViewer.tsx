"use client"

import type React from "react"
import { useState, useEffect, useLayoutEffect, useRef, useCallback } from "react"
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent,
  Slider,
  Button,
  ButtonGroup,
  Chip,
  LinearProgress,
  Alert,
} from "@mui/material"
import {
  ZoomIn,
  ZoomOut,
  RotateLeft,
  RotateRight,
  Refresh,
  PlayArrow,
  Pause,
  Straighten,
  RadioButtonUnchecked,
  CropFree,
  Edit as AnnotateIcon,
  Psychology as AIIcon,
  Save as SaveIcon,
} from "@mui/icons-material"

// Import real DICOM service
import cornerstone from 'cornerstone-core'
import { dicomServiceBlackImageFix as dicomService } from '../../services/dicomService_BlackImageFix'

// Initialize DICOM service on component load
let dicomServiceInitialized = false
const initializeDicomService = async () => {
  if (!dicomServiceInitialized) {
    try {
      await dicomService.initialize()
      dicomServiceInitialized = true
      console.log('✅ [ProfessionalDicomViewer] DICOM service initialized')
    } catch (error) {
      console.error('❌ [ProfessionalDicomViewer] DICOM service initialization failed:', error)
      throw error
    }
  }
}

interface Study {
  patient_id: string
  study_uid: string
  study_date?: string
  modality: string
  description?: string
  study_description?: string
  filename?: string
  image_urls?: string[]
  patient_info?: {
    name?: string
    gender?: string
    date_of_birth?: string
  }
  status: string
  exam_type?: string
  reports?: Array<{
    report_id: string
    status: string
    created_at: string
    finalized_at?: string
    ai_generated: boolean
  }>
}

interface ProfessionalDicomViewerProps {
  study: Study
  onError?: (error: string) => void
}

const ProfessionalDicomViewer: React.FC<ProfessionalDicomViewerProps> = ({ study, onError }) => {
  // State variables
  const [isLoading, setIsLoading] = useState(true)
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [currentImage, setCurrentImage] = useState(0)
  const [totalImages, setTotalImages] = useState(0)
  const [imageUrls, setImageUrls] = useState<string[]>([])
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [cornerstoneReady, setCornerstoneReady] = useState(false)

  // Viewer controls
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [windowWidth, setWindowWidth] = useState(400)
  const [windowCenter, setWindowCenter] = useState(40)

  // Advanced features
  const [measurementMode, setMeasurementMode] = useState<string | null>(null)
  const [annotationMode, setAnnotationMode] = useState<string | null>(null)
  const [showAIFindings, setShowAIFindings] = useState(false)
  const [measurements] = useState<any[]>([])
  const [annotations] = useState<any[]>([])

  const viewerRef = useRef<HTMLDivElement>(null)

  // Window presets for different imaging modalities
  const windowPresets = {
    "Soft Tissue": { width: 400, center: 40 },
    Lung: { width: 1500, center: -600 },
    Bone: { width: 1800, center: 400 },
    Brain: { width: 100, center: 50 },
    Liver: { width: 150, center: 30 },
  }

  // Define loadImage function FIRST before any useEffect that uses it
  const loadImage = useCallback(async (url: string): Promise<void> => {
    try {
      console.log("🔄 [ProfessionalDicomViewer] Loading image from:", url)

      if (!viewerRef.current) {
        throw new Error("Viewer element not found")
      }

      if (!cornerstoneReady) {
        throw new Error("Cornerstone not ready")
      }

      // Use real DICOM service to load image
      const imageId = `wadouri:${url}`
      console.log("🆔 [ProfessionalDicomViewer] Generated imageId:", imageId)

      // Ensure the element is enabled for Cornerstone
      try {
        cornerstone.enable(viewerRef.current)
      } catch (enableError: any) {
        // Element might already be enabled
      }

      // Load and cache the image using real DICOM service
      console.log("📥 [ProfessionalDicomViewer] Loading image with DICOM service...")

      const image = await dicomService.loadImage(imageId)
      console.log("✅ [ProfessionalDicomViewer] Image loaded successfully:", {
        width: image.width,
        height: image.height,
        minPixelValue: image.minPixelValue,
        maxPixelValue: image.maxPixelValue,
      })

      // Display the image
      console.log("🖼️ [ProfessionalDicomViewer] Displaying image...")
      cornerstone.displayImage(viewerRef.current, image)
      console.log("✅ [ProfessionalDicomViewer] Image displayed successfully")

      // Get the current viewport and properly fit the image
      const element = viewerRef.current
      const enabledElement = cornerstone.getEnabledElement(element)
      const displayedImage = enabledElement.image

      if (displayedImage) {
        // Calculate scale to fit image in viewport with proper aspect ratio
        const windowWidth = element.clientWidth
        const windowHeight = element.clientHeight
        const imageWidth = displayedImage.width
        const imageHeight = displayedImage.height

        // Calculate scale to fit image while maintaining aspect ratio
        const scaleX = windowWidth / imageWidth
        const scaleY = windowHeight / imageHeight
        const scale = Math.min(scaleX, scaleY) * 0.9 // 90% to leave some margin

        // Set proper viewport with correct window/level values
        const viewport = {
          scale: scale,
          translation: { x: 0, y: 0 },
          rotation: 0,
          hflip: false,
          vflip: false,
          voi: {
            windowWidth: windowWidth,
            windowCenter: windowCenter,
          },
        }

        cornerstone.setViewport(element, viewport)
        console.log("🔧 [ProfessionalDicomViewer] Viewport set with scale:", scale)

        // Update zoom state to match actual scale
        setZoom(scale)
      }

      // Apply window/level settings with a small delay to ensure image is rendered
      setTimeout(() => {
        try {
          const currentViewport = cornerstone.getViewport(viewerRef.current!)
          currentViewport.voi.windowWidth = windowWidth
          currentViewport.voi.windowCenter = windowCenter
          cornerstone.setViewport(viewerRef.current!, currentViewport)
          console.log("🎛️ [ProfessionalDicomViewer] Window/Level applied:", { windowWidth, windowCenter })
        } catch (viewportError) {
          console.warn("⚠️ [ProfessionalDicomViewer] Failed to apply window/level:", viewportError)
        }
      }, 100)

      setCurrentImageUrl(imageId)
    } catch (err) {
      console.error("❌ [ProfessionalDicomViewer] Failed to load DICOM image:", err)
      const errorMessage = err instanceof Error ? err.message : "Unknown error loading image"
      setError(`Failed to load DICOM image: ${errorMessage}`)
      throw err
    }
  }, [cornerstoneReady, windowWidth, windowCenter])

  useLayoutEffect(() => {
    let retryCount = 0
    const maxRetries = 10
    let isMounted = true

    const initializeCornerstone = async () => {
      if (!isMounted) return

      try {
        console.log(`🔧 [ProfessionalDicomViewer] Initializing cornerstone... (attempt ${retryCount + 1}/${maxRetries})`)

        // Initialize DICOM service first
        await initializeDicomService()

        // Wait for DOM to be ready and check if element exists
        await new Promise((resolve) => setTimeout(resolve, 200))

        if (!isMounted) return

        // Check if the element is actually in the DOM and has dimensions
        if (!viewerRef.current || !viewerRef.current.offsetParent) {
          retryCount++
          if (retryCount < maxRetries) {
            console.warn(`⏳ [ProfessionalDicomViewer] Viewer element not ready or not visible, retrying... (${retryCount}/${maxRetries})`)
            setTimeout(initializeCornerstone, 300)
            return
          } else {
            throw new Error(`Failed to initialize after ${maxRetries} attempts: Viewer element not available or not visible`)
          }
        }

        // Additional check for element dimensions
        const rect = viewerRef.current.getBoundingClientRect()
        if (rect.width === 0 || rect.height === 0) {
          retryCount++
          if (retryCount < maxRetries) {
            console.warn(`⏳ [ProfessionalDicomViewer] Viewer element has no dimensions, retrying... (${retryCount}/${maxRetries})`)
            setTimeout(initializeCornerstone, 300)
            return
          } else {
            throw new Error(`Failed to initialize after ${maxRetries} attempts: Viewer element has no dimensions`)
          }
        }

        // Enable cornerstone on the element
        try {
          cornerstone.enable(viewerRef.current)
          console.log("✅ [ProfessionalDicomViewer] Cornerstone enabled successfully")
          setCornerstoneReady(true)
        } catch (enableError: any) {
          console.log("ℹ️ [ProfessionalDicomViewer] Cornerstone already enabled")
          setCornerstoneReady(true)
        }
      } catch (error) {
        if (!isMounted) return
        console.error("❌ [ProfessionalDicomViewer] Cornerstone initialization failed:", error)
        setError(`Cornerstone initialization failed: ${error}`)
        onError?.(`Cornerstone initialization failed: ${error}`)
      }
    }

    // Use a small delay to ensure the component is fully mounted
    const timeoutId = setTimeout(initializeCornerstone, 100)

    // Cleanup function to prevent memory leaks and disable cornerstone
    return () => {
      isMounted = false
      clearTimeout(timeoutId)
      // Copy ref to variable to avoid stale closure warning
      const currentViewer = viewerRef.current
      if (currentViewer) {
        try {
          cornerstone.disable(currentViewer)
        } catch (error) {
          console.warn("Warning during cornerstone cleanup:", error)
        }
      }
    }
  }, [onError])

  // Main viewer initialization useEffect
  useEffect(() => {
    const initializeViewer = async () => {
      if (!cornerstoneReady) {
        console.log("⏳ [ProfessionalDicomViewer] Waiting for cornerstone to be ready...")
        return
      }

      try {
        console.log("🚀 [ProfessionalDicomViewer] Starting viewer initialization...")
        setIsLoading(true)
        setError(null)
        setLoadingProgress(10)

        if (!study || !study.patient_id) {
          throw new Error("No study or patient ID found")
        }

        console.log("📊 [ProfessionalDicomViewer] Study data:", {
          patient_id: study.patient_id,
          study_uid: study.study_uid,
          modality: study.modality,
          filename: study.filename,
          image_urls: study.image_urls?.length || 0,
        })

        setLoadingProgress(20)

        // Build actual image URLs from backend using DICOM service
        const urls: string[] = []

        if (study.image_urls && study.image_urls.length > 0) {
          console.log("📁 [ProfessionalDicomViewer] Using existing image URLs:", study.image_urls)
          urls.push(...study.image_urls)
          setLoadingProgress(40)
        } else {
          // Use DICOM service to get proper image IDs
          console.log("🔧 [ProfessionalDicomViewer] Getting image IDs from DICOM service...")
          const imageIds = dicomService.getImageIds(study.study_uid || 'default')
          urls.push(...imageIds)
          setLoadingProgress(45)
        }

        if (urls.length === 0) {
          throw new Error("No valid DICOM file URLs could be constructed")
        }

        console.log("🖼️ [ProfessionalDicomViewer] Constructed image URLs:", urls)
        setImageUrls(urls)
        setTotalImages(urls.length)
        setCurrentImage(0)
        setLoadingProgress(60)

        // Set default window/level values for CT images
        if (study.modality === "CT") {
          setWindowCenter(40)
          setWindowWidth(400)
        } else {
          setWindowCenter(128)
          setWindowWidth(256)
        }

        setLoadingProgress(70)

        // Load first image
        console.log("🖼️ [ProfessionalDicomViewer] Loading first image...")
        await loadImage(urls[0])

        setLoadingProgress(100)
        setIsLoading(false)
        console.log("✅ [ProfessionalDicomViewer] Viewer initialization complete")
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to initialize DICOM viewer"
        console.error("❌ [ProfessionalDicomViewer] Initialization error:", err)
        setError(errorMessage)
        setIsLoading(false)
        onError?.(errorMessage)
      }
    }

    initializeViewer()
  }, [study, onError, cornerstoneReady, loadImage])

  // Auto-play functionality
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isPlaying && totalImages > 1) {
      interval = setInterval(() => {
        setCurrentImage((prev) => {
          const nextIndex = (prev + 1) % totalImages
          loadImage(imageUrls[nextIndex]).catch(console.error)
          return nextIndex
        })
      }, 1000) // Change image every second
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isPlaying, totalImages, imageUrls])

  // Navigation handlers
  const handleImageNavigation = (direction: "prev" | "next") => {
    if (totalImages <= 1) return

    const newIndex =
      direction === "next" ? (currentImage + 1) % totalImages : (currentImage - 1 + totalImages) % totalImages

    setCurrentImage(newIndex)
    loadImage(imageUrls[newIndex]).catch(console.error)
  }

  const handleWindowPreset = (preset: keyof typeof windowPresets) => {
    const { width, center } = windowPresets[preset]
    setWindowWidth(width)
    setWindowCenter(center)

    if (viewerRef.current && currentImageUrl) {
      try {
        const viewport = cornerstone.getViewport(viewerRef.current)
        viewport.voi.windowWidth = width
        viewport.voi.windowCenter = center
        cornerstone.setViewport(viewerRef.current, viewport)
      } catch (error) {
        console.warn("Failed to apply window preset:", error)
      }
    }
  }

  const handleZoom = (factor: number) => {
    const newZoom = Math.max(0.1, Math.min(5.0, zoom * factor))
    setZoom(newZoom)

    if (viewerRef.current && currentImageUrl) {
      try {
        const viewport = cornerstone.getViewport(viewerRef.current)
        viewport.scale = newZoom
        cornerstone.setViewport(viewerRef.current, viewport)
      } catch (error) {
        console.warn("Failed to apply zoom:", error)
      }
    }
  }

  const handleRotate = (degrees: number) => {
    const newRotation = rotation + degrees
    setRotation(newRotation)

    if (viewerRef.current && currentImageUrl) {
      try {
        const viewport = cornerstone.getViewport(viewerRef.current)
        viewport.rotation = (newRotation * Math.PI) / 180 // Convert to radians
        cornerstone.setViewport(viewerRef.current, viewport)
      } catch (error) {
        console.warn("Failed to apply rotation:", error)
      }
    }
  }

  const handleReset = () => {
    setZoom(1.0)
    setRotation(0)
    setWindowWidth(400)
    setWindowCenter(40)

    if (viewerRef.current && currentImageUrl) {
      try {
        const element = viewerRef.current
        const enabledElement = cornerstone.getEnabledElement(element)
        const displayedImage = enabledElement.image

        if (displayedImage) {
          const windowWidth = element.clientWidth
          const windowHeight = element.clientHeight
          const imageWidth = displayedImage.width
          const imageHeight = displayedImage.height

          const scaleX = windowWidth / imageWidth
          const scaleY = windowHeight / imageHeight
          const scale = Math.min(scaleX, scaleY) * 0.9

          const viewport = {
            scale: scale,
            translation: { x: 0, y: 0 },
            rotation: 0,
            hflip: false,
            vflip: false,
            voi: {
              windowWidth: 400,
              windowCenter: 40,
            },
          }

          cornerstone.setViewport(element, viewport)
          setZoom(scale)
        }
      } catch (error) {
        console.warn("Failed to reset viewport:", error)
      }
    }
  }

  const handleMeasurement = (tool: string) => {
    setMeasurementMode(measurementMode === tool ? null : tool)
  }

  const handleAnnotation = (tool: string) => {
    setAnnotationMode(annotationMode === tool ? null : tool)
  }

  const handleSaveMeasurements = () => {
    console.log("Saving measurements and annotations:", { measurements, annotations })
  }

  useEffect(() => {
    if (viewerRef.current && currentImageUrl) {
      try {
        const viewport = cornerstone.getViewport(viewerRef.current)
        viewport.voi.windowWidth = windowWidth
        viewport.voi.windowCenter = windowCenter
        viewport.scale = zoom
        cornerstone.setViewport(viewerRef.current, viewport)
      } catch (error) {
        console.warn("Failed to update viewport:", error)
      }
    }
  }, [windowWidth, windowCenter, zoom, currentImageUrl])

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          DICOM Viewer Error
        </Typography>
        <Typography variant="body2">{error}</Typography>
        <Button onClick={() => window.location.reload()} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Alert>
    )
  }

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column", bgcolor: "#000" }}>
      {/* Loading Progress */}
      {isLoading && (
        <Box sx={{ position: "absolute", top: 0, left: 0, right: 0, zIndex: 1000 }}>
          <LinearProgress variant="determinate" value={loadingProgress} />
          <Typography variant="body2" sx={{ textAlign: "center", color: "white", mt: 1 }}>
            Loading DICOM Study... {loadingProgress}%{loadingProgress < 20 && " - Initializing..."}
            {loadingProgress >= 20 && loadingProgress < 40 && " - Fetching files..."}
            {loadingProgress >= 40 && loadingProgress < 70 && " - Processing URLs..."}
            {loadingProgress >= 70 && loadingProgress < 100 && " - Loading image..."}
          </Typography>
        </Box>
      )}

      <Grid container sx={{ height: "100%" }}>
        {/* Main Viewer */}
        <Grid item xs={12} md={9} sx={{ height: "100%" }}>
          <Paper sx={{ height: "100%", position: "relative", bgcolor: "#000" }}>
            {/* Toolbar */}
            <Box
              sx={{
                position: "absolute",
                top: 8,
                left: 8,
                zIndex: 10,
                display: "flex",
                gap: 1,
                backgroundColor: "rgba(0, 0, 0, 0.8)",
                borderRadius: 1,
                p: 1,
              }}
            >
              <ButtonGroup size="small">
                <Tooltip title="Zoom In">
                  <IconButton onClick={() => handleZoom(1.2)} sx={{ color: "white" }}>
                    <ZoomIn />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Zoom Out">
                  <IconButton onClick={() => handleZoom(0.8)} sx={{ color: "white" }}>
                    <ZoomOut />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Rotate Left">
                  <IconButton onClick={() => handleRotate(-90)} sx={{ color: "white" }}>
                    <RotateLeft />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Rotate Right">
                  <IconButton onClick={() => handleRotate(90)} sx={{ color: "white" }}>
                    <RotateRight />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Reset">
                  <IconButton onClick={handleReset} sx={{ color: "white" }}>
                    <Refresh />
                  </IconButton>
                </Tooltip>
              </ButtonGroup>

              <ButtonGroup size="small" sx={{ ml: 1 }}>
                <Tooltip title="Length Measurement">
                  <IconButton
                    onClick={() => handleMeasurement("length")}
                    sx={{ color: measurementMode === "length" ? "yellow" : "white" }}
                  >
                    <Straighten />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Circle ROI">
                  <IconButton
                    onClick={() => handleMeasurement("circle")}
                    sx={{ color: measurementMode === "circle" ? "yellow" : "white" }}
                  >
                    <RadioButtonUnchecked />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Rectangle ROI">
                  <IconButton
                    onClick={() => handleMeasurement("rectangle")}
                    sx={{ color: measurementMode === "rectangle" ? "yellow" : "white" }}
                  >
                    <CropFree />
                  </IconButton>
                </Tooltip>
              </ButtonGroup>

              <ButtonGroup size="small" sx={{ ml: 1 }}>
                <Tooltip title="Annotate">
                  <IconButton
                    onClick={() => handleAnnotation("text")}
                    sx={{ color: annotationMode === "text" ? "yellow" : "white" }}
                  >
                    <AnnotateIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="AI Findings">
                  <IconButton
                    onClick={() => setShowAIFindings(!showAIFindings)}
                    sx={{ color: showAIFindings ? "cyan" : "white" }}
                  >
                    <AIIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Save Annotations">
                  <IconButton onClick={handleSaveMeasurements} sx={{ color: "white" }}>
                    <SaveIcon />
                  </IconButton>
                </Tooltip>
              </ButtonGroup>

              <Tooltip title={totalImages <= 1 ? "Single image - no playback available" : isPlaying ? "Pause" : "Play"}>
                <span>
                  <IconButton
                    onClick={() => setIsPlaying(!isPlaying)}
                    sx={{ color: "white", ml: 1 }}
                    disabled={totalImages <= 1}
                  >
                    {isPlaying ? <Pause /> : <PlayArrow />}
                  </IconButton>
                </span>
              </Tooltip>
            </Box>

            {/* Navigation Controls */}
            {totalImages > 1 && (
              <Box
                sx={{
                  position: "absolute",
                  bottom: 8,
                  left: "50%",
                  transform: "translateX(-50%)",
                  zIndex: 10,
                  display: "flex",
                  gap: 1,
                  backgroundColor: "rgba(0, 0, 0, 0.8)",
                  borderRadius: 1,
                  p: 1,
                  alignItems: "center",
                }}
              >
                <IconButton onClick={() => handleImageNavigation("prev")} sx={{ color: "white" }}>
                  <RotateLeft />
                </IconButton>
                <Typography variant="body2" sx={{ color: "white", mx: 2 }}>
                  {currentImage + 1} / {totalImages}
                </Typography>
                <IconButton onClick={() => handleImageNavigation("next")} sx={{ color: "white" }}>
                  <RotateRight />
                </IconButton>
              </Box>
            )}

            {/* Main Image Display */}
            <Box
              sx={{
                width: "100%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                position: "relative",
                overflow: "hidden",
                backgroundColor: "#000",
              }}
            >
              {currentImageUrl ? (
                <div
                  ref={viewerRef}
                  style={{
                    width: "100%",
                    height: "100%",
                    minHeight: "400px",
                    backgroundColor: "#000",
                    position: "relative",
                    overflow: "hidden",
                    display: "block",
                  }}
                  onContextMenu={(e) => e.preventDefault()} // Prevent right-click menu
                ></div>
              ) : (
                <Box sx={{ textAlign: "center", color: "white" }}>
                  <Typography variant="h6">{isLoading ? "Loading DICOM Image..." : "No Image Available"}</Typography>
                  <Typography variant="body2">Study: {study.study_uid}</Typography>
                  <Typography variant="body2">Patient: {study.patient_id}</Typography>
                  {error && (
                    <Typography variant="body2" sx={{ color: "red", mt: 1 }}>
                      Error: {error}
                    </Typography>
                  )}
                </Box>
              )}

              {/* DICOM Overlay */}
              <Box
                sx={{
                  position: "absolute",
                  top: 8,
                  right: 8,
                  color: "#00ff00",
                  fontFamily: "monospace",
                  fontSize: "12px",
                  pointerEvents: "none",
                  textShadow: "1px 1px 2px rgba(0,0,0,0.8)",
                  zIndex: 5,
                }}
              >
                <div>Patient: {study.patient_info?.name || study.patient_id}</div>
                <div>Study: {study.study_date}</div>
                <div>Modality: {study.modality}</div>
                <div>
                  W/L: {windowWidth}/{windowCenter}
                </div>
                <div>Zoom: {(zoom * 100).toFixed(0)}%</div>
                <div>
                  Image: {currentImage + 1}/{totalImages}
                </div>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Control Panel */}
        <Grid item xs={12} md={3} sx={{ height: "100%", overflow: "auto" }}>
          <Paper sx={{ height: "100%", p: 2 }}>
            <Typography variant="h6" gutterBottom>
              DICOM Controls
            </Typography>

            {/* Window/Level Controls */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Window/Level
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption">Window Width: {windowWidth}</Typography>
                  <Slider
                    value={windowWidth}
                    onChange={(_, value) => setWindowWidth(value as number)}
                    min={1}
                    max={2000}
                    size="small"
                  />
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption">Window Center: {windowCenter}</Typography>
                  <Slider
                    value={windowCenter}
                    onChange={(_, value) => setWindowCenter(value as number)}
                    min={-1000}
                    max={1000}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                  {Object.keys(windowPresets).map((preset) => (
                    <Chip
                      key={preset}
                      label={preset}
                      size="small"
                      onClick={() => handleWindowPreset(preset as keyof typeof windowPresets)}
                      variant="outlined"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>

            {/* Study Information */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Study Information
                </Typography>
                <Typography variant="body2">Patient: {study.patient_info?.name || study.patient_id}</Typography>
                <Typography variant="body2">Study Date: {study.study_date}</Typography>
                <Typography variant="body2">Modality: {study.modality}</Typography>
                <Typography variant="body2">Description: {study.description}</Typography>
                <Typography variant="body2">Images: {totalImages}</Typography>
              </CardContent>
            </Card>

            {/* AI Findings */}
            {showAIFindings && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    AI Findings
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    AI analysis results will appear here when available.
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default ProfessionalDicomViewer
