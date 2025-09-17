"use client"

import type React from "react"
import { useState, useEffect } from "react"
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Divider,
  Avatar,
  Grid,
  Paper,
  IconButton,
  Tooltip,
  Badge,
  useTheme,
  alpha,
  useMediaQuery,
  Drawer,
  Fab,
} from "@mui/material"
import {
  Assignment as ReportIcon,
  Receipt as BillingIcon,
  ArrowBack as BackIcon,
  Person as PersonIcon,
  AccessTime as TimeIcon,
  LocalHospital as HospitalIcon,
  Warning as WarningIcon,
  Star as StarIcon,
  Share as ShareIcon,
  Print as PrintIcon,
  Download as DownloadIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  PriorityHigh as PriorityIcon,
  AutoAwesome as AIIcon,
  TrendingUp as TrendingIcon,
  Notifications as NotificationIcon,
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
  Psychology as PsychologyIcon,
  Speed as SpeedIcon,
  Assessment as AssessmentIcon,
  Group as GroupIcon,
  Chat as ChatIcon,
  VideoCall as VideoCallIcon,
  PersonAdd as PersonAddIcon,
  Visibility as VisibilityIcon,
  Lock as LockIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import { useParams } from "react-router-dom"

import ProfessionalDicomViewer from "../components/DICOM/ProfessionalDicomViewer"
import SimpleDicomViewer from "../components/DICOM/SimpleDicomViewer"
import WorkingDicomViewer from "../components/DICOM/WorkingDicomViewer"
import SmartDicomViewer from "../components/DICOM/SmartDicomViewer"
import type { Study } from "../types"
import { apiService } from "../services/api"

const StudyViewer: React.FC = () => {
  const { studyUid } = useParams()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down("md"))
  const isTablet = useMediaQuery(theme.breakpoints.down("lg"))
  const [study, setStudy] = useState<Study | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isStarred, setIsStarred] = useState(false)
  const [urgentFindings, setUrgentFindings] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile)
  const [useSimpleViewer, setUseSimpleViewer] = useState(true) // Start with simple viewer

  useEffect(() => {
    console.log("🚀 StudyViewer component mounted with studyUid:", studyUid)

    const loadStudy = async () => {
      if (!studyUid) {
        setError("Study UID is required")
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError(null)

        console.log("🔍 [StudyViewer] Fetching study:", studyUid)
        const response = await apiService.getStudy(studyUid)
        console.log("📊 [StudyViewer] API response received:", response)
        console.log("🖼️ [StudyViewer] Study data:", response)
        console.log("🖼️ [StudyViewer] Image URLs:", response?.image_urls)
        console.log("🔍 [StudyViewer] Study structure:", {
          patient_id: response.patient_id,
          study_uid: response.study_uid,
          study_date: response.study_date,
          modality: response.modality,
          image_urls_count: response.image_urls?.length || 0,
          first_image_url: response.image_urls?.[0],
        })

        if (!response) {
          throw new Error("No study data received from server")
        }

        if (!response.patient_id) {
          throw new Error("Study data is missing patient_id")
        }

        // Ensure image_urls is an array
        if (!response.image_urls) {
          response.image_urls = []
        }

        console.log("✅ [StudyViewer] About to set study state")
        setStudy(response)
        console.log("✅ [StudyViewer] Study state set successfully")
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load study"
        setError(errorMessage)
        console.error("❌ [StudyViewer] Error loading study:", err)
      } finally {
        setLoading(false)
      }
    }

    loadStudy()
  }, [studyUid])

  const handleViewReport = (reportId: string) => {
    console.log("StudyViewer: Navigating to report with ID:", reportId)
    // In a real app, this would navigate to the report page
  }

  const handleCreateReport = () => {
    console.log("Creating new report for study:", studyUid)
    // In a real app, this would navigate to create report page
  }

  const handleViewBilling = () => {
    console.log("Viewing billing for study:", studyUid)
    // In a real app, this would navigate to billing page
  }

  const handleStarToggle = () => {
    setIsStarred(!isStarred)
  }

  const handleShare = () => {
    // Implement study sharing functionality
    console.log("Sharing study:", studyUid)
  }

  const handlePrint = () => {
    window.print()
  }

  const handleDownload = () => {
    // Implement study download functionality
    console.log("Downloading study:", studyUid)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "received":
        return "info"
      case "processing":
        return "warning"
      case "completed":
        return "success"
      case "billed":
        return "secondary"
      case "error":
        return "error"
      default:
        return "default"
    }
  }

  const getPriorityLevel = (study: Study) => {
    // Determine priority based on study characteristics
    if (study.exam_type?.includes("emergency") || study.status === "error") {
      return "high"
    }
    if (study.modality === "CT" || study.modality === "MR") {
      return "medium"
    }
    return "normal"
  }

  const getPatientAge = (study: Study) => {
    // Calculate age from date of birth if available
    if (study.patient_info?.date_of_birth) {
      const birthDate = new Date(study.patient_info.date_of_birth)
      const today = new Date()
      let age = today.getFullYear() - birthDate.getFullYear()
      const monthDiff = today.getMonth() - birthDate.getMonth()
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--
      }
      return age
    }
    return null
  }

  const getPatientGender = (study: Study) => {
    // Get gender from patient info
    return study.patient_info?.gender || "Unknown"
  }

  const getPatientName = (study: Study) => {
    // Get patient name from patient info
    return study.patient_info?.name || study.patient_id
  }

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 400 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Button startIcon={<BackIcon />} onClick={() => console.log("Back to studies")} sx={{ mb: 2 }}>
          Back to Studies
        </Button>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (!study) {
    return (
      <Box>
        <Button startIcon={<BackIcon />} onClick={() => console.log("Back to studies")} sx={{ mb: 2 }}>
          Back to Studies
        </Button>
        <Alert severity="warning">Study not found</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Enhanced Professional Header */}
      <Paper
        sx={{
          p: isMobile ? 2 : 3,
          mb: 1,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          borderLeft: `4px solid ${getPriorityLevel(study) === "high" ? theme.palette.error.main : getPriorityLevel(study) === "medium" ? theme.palette.warning.main : theme.palette.success.main}`,
        }}
      >
        <Grid container spacing={isMobile ? 2 : 3} alignItems="center">
          {/* Patient & Study Info */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
              <Button
                startIcon={<BackIcon />}
                onClick={() => console.log("Back to studies")}
                variant="outlined"
                size="small"
                sx={{ minWidth: "auto" }}
              >
                Back
              </Button>

              <Avatar
                sx={{
                  bgcolor: theme.palette.primary.main,
                  width: 48,
                  height: 48,
                }}
              >
                <PersonIcon />
              </Avatar>

              <Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                  <Typography variant={isMobile ? "h6" : "h5"} sx={{ fontWeight: 700, color: "primary.main" }}>
                    {getPatientName(study)}
                  </Typography>
                  <Chip
                    size="small"
                    label={`${getPatientAge(study) ? `${getPatientAge(study)}Y` : ""} ${getPatientGender(study)}`}
                    sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), color: "info.main" }}
                  />
                  {getPriorityLevel(study) === "high" && (
                    <Tooltip title="High Priority Study">
                      <Badge color="error" variant="dot">
                        <PriorityIcon color="error" fontSize="small" />
                      </Badge>
                    </Tooltip>
                  )}
                  <Tooltip title={isStarred ? "Remove from favorites" : "Add to favorites"}>
                    <IconButton size="small" onClick={handleStarToggle}>
                      <StarIcon color={isStarred ? "warning" : "disabled"} fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Typography variant={isMobile ? "body1" : "subtitle1"} sx={{ fontWeight: 600, mb: 0.5 }}>
                  {study.study_description || study.exam_type}
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Chip
                    icon={<HospitalIcon />}
                    label={study.modality}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    icon={<TimeIcon />}
                    label={study.study_date ? new Date(study.study_date).toLocaleDateString() : "No date"}
                    size="small"
                    variant="outlined"
                  />
                  <Chip label={study.status} size="small" color={getStatusColor(study.status) as any} />
                  {urgentFindings && (
                    <Chip
                      icon={<WarningIcon />}
                      label="Urgent Findings"
                      size="small"
                      color="error"
                      sx={{ animation: "pulse 2s infinite" }}
                    />
                  )}
                </Box>
              </Box>
            </Box>
          </Grid>

          {/* Quick Actions */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, flexWrap: "wrap" }}>
              {/* Primary Actions */}
              <Box sx={{ display: "flex", gap: 1, mb: 1 }}>
                {study.reports && study.reports.length > 0 ? (
                  <Button
                    startIcon={<ReportIcon />}
                    onClick={() => handleViewReport(study.reports![0].report_id)}
                    variant="contained"
                    size="medium"
                    sx={{ minWidth: 120 }}
                  >
                    View Report
                  </Button>
                ) : (
                  <Button
                    startIcon={<ReportIcon />}
                    onClick={handleCreateReport}
                    variant="contained"
                    size="medium"
                    sx={{ minWidth: 120 }}
                  >
                    Create Report
                  </Button>
                )}

                <Button startIcon={<BillingIcon />} onClick={handleViewBilling} variant="outlined" size="medium">
                  Billing
                </Button>

                <Button
                  onClick={() => setUseSimpleViewer(!useSimpleViewer)}
                  variant="outlined"
                  size="medium"
                  color={useSimpleViewer ? "primary" : "secondary"}
                >
                  {useSimpleViewer ? "Professional View" : "Simple View"}
                </Button>
              </Box>

              {/* Secondary Actions */}
              <Box sx={{ display: "flex", gap: 0.5 }}>
                <Tooltip title="Share Study">
                  <IconButton onClick={handleShare} size="small">
                    <ShareIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Print Study">
                  <IconButton onClick={handlePrint} size="small">
                    <PrintIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download Study">
                  <IconButton onClick={handleDownload} size="small">
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Contact Referring Physician">
                  <IconButton size="small">
                    <PhoneIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Send Results">
                  <IconButton size="small">
                    <EmailIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Comprehensive Study Metadata Panel */}
      <Paper sx={{ p: 2, mb: 2, bgcolor: alpha(theme.palette.background.paper, 0.8) }}>
        <Grid container spacing={3}>
          {/* Patient Demographics & Clinical Info */}
          <Grid item xs={12} md={4}>
            <Typography variant={isMobile ? "subtitle1" : "h6"} sx={{ mb: 2, color: "primary.main", fontWeight: 600 }}>
              Patient Information
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Patient ID:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {study.patient_id}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Age/Gender:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {getPatientAge(study)}Y {getPatientGender(study)}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Referring Physician:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {"Not specified"}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Institution:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {"Main Hospital"}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Accession Number:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {"N/A"}
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Study Details */}
          <Grid item xs={12} md={4}>
            <Typography variant={isMobile ? "subtitle1" : "h6"} sx={{ mb: 2, color: "primary.main", fontWeight: 600 }}>
              Study Details
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Study Date:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {study.study_date
                    ? new Date(study.study_date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })
                    : "Not available"}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Modality:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {study.modality}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Body Part:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {"Not specified"}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Series Count:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {"Unknown"}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Images Count:
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {"Unknown"}
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Clinical Context & History */}
          <Grid item xs={12} md={4}>
            <Typography variant={isMobile ? "subtitle1" : "h6"} sx={{ mb: 2, color: "primary.main", fontWeight: 600 }}>
              Clinical Context
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  Clinical History:
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    bgcolor: alpha(theme.palette.info.main, 0.05),
                    p: 1,
                    borderRadius: 1,
                    fontSize: "0.875rem",
                    lineHeight: 1.4,
                  }}
                >
                  {study.study_description || "No clinical history provided"}
                </Typography>
              </Box>

              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  Indication:
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    bgcolor: alpha(theme.palette.warning.main, 0.05),
                    p: 1,
                    borderRadius: 1,
                    fontSize: "0.875rem",
                  }}
                >
                  {"Routine examination"}
                </Typography>
              </Box>

              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Priority Level:
                </Typography>
                <Chip
                  label={getPriorityLevel(study).toUpperCase()}
                  size="small"
                  color={
                    getPriorityLevel(study) === "high"
                      ? "error"
                      : getPriorityLevel(study) === "medium"
                        ? "warning"
                        : "success"
                  }
                  sx={{ fontWeight: 600 }}
                />
              </Box>

              <Box sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography variant="body2" color="text.secondary">
                  Prior Studies:
                </Typography>
                <Button
                  size="small"
                  variant="text"
                  sx={{ minWidth: "auto", p: 0.5 }}
                  onClick={() => console.log("View prior studies")}
                >
                  View (3)
                </Button>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: "flex", position: "relative" }}>
        {/* Mobile Menu Button */}
        {isMobile && (
          <Fab
            color="primary"
            size="small"
            sx={{
              position: "fixed",
              top: 16,
              right: 16,
              zIndex: 1300,
            }}
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <CloseIcon /> : <MenuIcon />}
          </Fab>
        )}

        {/* Image Viewer */}
        <Box
          sx={{
            flexGrow: 1,
            minHeight: 0,
            width: isMobile ? "100%" : isTablet ? "calc(100% - 280px)" : "calc(100% - 300px)",
          }}
        >
          {study ? (
            <SmartDicomViewer
              study={study}
              onError={(error) => {
                console.error("Smart DICOM Viewer Error:", error)
                setError(`Smart DICOM Viewer Error: ${error}`)
              }}
            />
          ) : (
            <Box
              sx={{
                p: 2,
                textAlign: "center",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Typography variant="h6" color="text.secondary">
                {loading ? "Loading study data..." : "No study data available"}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Study Information Panel - Responsive Drawer */}
        <Drawer
          variant={isMobile ? "temporary" : "persistent"}
          anchor="right"
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          sx={{
            width: isMobile ? 280 : isTablet ? 280 : 300,
            flexShrink: 0,
            "& .MuiDrawer-paper": {
              width: isMobile ? 280 : isTablet ? 280 : 300,
              boxSizing: "border-box",
              position: isMobile ? "fixed" : "relative",
              height: isMobile ? "100vh" : "auto",
              top: isMobile ? 0 : "auto",
            },
          }}
        >
          <Box sx={{ p: 2, overflow: "auto", height: "100%" }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Study Information
            </Typography>

            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Patient Information
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Patient Name:</strong> {study.patient_info?.name || study.patient_id || "Unknown"}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Patient ID:</strong> {study.patient_id || "N/A"}
                </Typography>
                {study.patient_info?.date_of_birth && (
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Date of Birth:</strong> {new Date(study.patient_info.date_of_birth).toLocaleDateString()}
                  </Typography>
                )}
                {study.patient_info?.date_of_birth && (
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Age:</strong> {getPatientAge(study)} years
                  </Typography>
                )}
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Gender:</strong> {study.patient_info?.gender || "Unknown"}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Study Date:</strong>{" "}
                  {study.study_date ? new Date(study.study_date).toLocaleDateString() : "N/A"}
                </Typography>
                <Typography variant="body2">
                  <strong>Modality:</strong> {study.modality || "N/A"}
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Study Details
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Study UID:</strong>
                </Typography>
                <Typography variant="caption" sx={{ wordBreak: "break-all", mb: 2, display: "block" }}>
                  {study.study_uid}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Exam Type:</strong> {study.exam_type || "N/A"}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Description:</strong> {study.description || study.study_description || "N/A"}
                </Typography>
                {study.study_time && (
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Study Time:</strong> {study.study_time}
                  </Typography>
                )}
                {study.workflow_status && (
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Workflow Status:</strong> {study.workflow_status}
                  </Typography>
                )}
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Typography variant="body2">
                    <strong>Status:</strong>
                  </Typography>
                  <Chip label={study.status} size="small" color={getStatusColor(study.status) as any} />
                </Box>
              </CardContent>
            </Card>

            {/* Study Statistics Section */}
            {study.study_statistics && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Study Statistics
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Total Files:</strong> {study.study_statistics.total_files || "N/A"}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Total Size:</strong>{" "}
                    {study.study_statistics.total_size_mb ? `${study.study_statistics.total_size_mb} MB` : "N/A"}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Series Count:</strong> {study.study_statistics.series_count || "N/A"}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Instance Count:</strong> {study.study_statistics.instance_count || "N/A"}
                  </Typography>
                </CardContent>
              </Card>
            )}

            {/* Processing Information Section */}
            {study.processing_info && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Processing Information
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Upload Duration:</strong>{" "}
                    {study.processing_info.upload_duration_ms
                      ? `${study.processing_info.upload_duration_ms} ms`
                      : "N/A"}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Processing Steps:</strong> {study.processing_info.processing_steps || "N/A"}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Processing Status:</strong> {study.processing_info.status || "N/A"}
                  </Typography>
                </CardContent>
              </Card>
            )}

            {/* Image URLs Section */}
            {study.image_urls && study.image_urls.length > 0 && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Available Images ({study.image_urls.length})
                  </Typography>
                  {study.image_urls.map((url, index) => (
                    <Typography key={index} variant="body2" sx={{ mb: 1, wordBreak: "break-all" }}>
                      <strong>Image {index + 1}:</strong> {url}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Reports Section */}
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Reports ({study.reports?.length || 0})
                </Typography>

                {study.reports && study.reports.length > 0 ? (
                  study.reports.map((report, index) => (
                    <Box key={report.report_id} sx={{ mb: index < study.reports!.length - 1 ? 2 : 0 }}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Report {index + 1}
                        </Typography>
                        <Chip
                          label={report.status}
                          size="small"
                          color={report.status === "final" ? "success" : "warning"}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
                        Created: {new Date(report.created_at).toLocaleString()}
                      </Typography>
                      {report.finalized_at && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
                          Finalized: {new Date(report.finalized_at).toLocaleString()}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
                        {report.ai_generated ? "AI Generated" : "Manual"}
                      </Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleViewReport(report.report_id)}
                        fullWidth
                      >
                        View Report
                      </Button>
                      {index < study.reports!.length - 1 && <Divider sx={{ mt: 2 }} />}
                    </Box>
                  ))
                ) : (
                  <Box sx={{ textAlign: "center", py: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      No reports available
                    </Typography>
                    <Button variant="contained" size="small" onClick={handleCreateReport} fullWidth>
                      Create Report
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Intelligent Workflow Panel */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                  <PsychologyIcon color="primary" />
                  <Typography variant="subtitle2" color="text.secondary">
                    AI-Powered Workflow
                  </Typography>
                </Box>

                {/* Critical Findings Alert */}
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <NotificationIcon fontSize="small" />
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      2 Critical Findings Detected
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ display: "block", mt: 0.5 }}>
                    Possible pneumothorax in right lung, enlarged cardiac silhouette
                  </Typography>
                </Alert>

                {/* AI Analysis Status */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      AI Analysis Progress
                    </Typography>
                    <Chip label="85% Complete" size="small" color="info" />
                  </Box>
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                    <Chip
                      icon={<CheckIcon />}
                      label="Anatomy Detection"
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                    <Chip
                      icon={<CheckIcon />}
                      label="Pathology Screening"
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                    <Chip
                      icon={<ScheduleIcon />}
                      label="Report Generation"
                      size="small"
                      color="warning"
                      variant="outlined"
                    />
                  </Box>
                </Box>

                {/* Quick Actions */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Quick Actions
                  </Typography>
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                    <Button variant="contained" size="small" startIcon={<AIIcon />} fullWidth>
                      Generate AI Report
                    </Button>
                    <Button variant="outlined" size="small" startIcon={<AssessmentIcon />} fullWidth>
                      Review Findings
                    </Button>
                    <Button variant="outlined" size="small" startIcon={<ShareIcon />} fullWidth>
                      Request Consultation
                    </Button>
                  </Box>
                </Box>

                {/* Next Steps Recommendations */}
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Recommended Next Steps
                  </Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1, display: "flex", alignItems: "center", gap: 1 }}>
                      <SpeedIcon fontSize="small" color="error" />
                      <strong>Urgent:</strong> Contact referring physician about pneumothorax
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1, display: "flex", alignItems: "center", gap: 1 }}>
                      <TrendingIcon fontSize="small" color="warning" />
                      <strong>Follow-up:</strong> Recommend cardiac echo within 48 hours
                    </Typography>
                    <Typography variant="body2" sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <CheckIcon fontSize="small" color="success" />
                      <strong>Documentation:</strong> Complete radiology report
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>

            {/* Collaborative Features Panel */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                  <GroupIcon color="primary" />
                  <Typography variant="subtitle2" color="text.secondary">
                    Collaboration & Sharing
                  </Typography>
                </Box>

                {/* Active Collaborators */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Active Collaborators (3)
                  </Typography>
                  <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
                    <Tooltip title="Dr. Sarah Johnson - Radiologist">
                      <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main" }}>SJ</Avatar>
                    </Tooltip>
                    <Tooltip title="Dr. Michael Chen - Cardiologist">
                      <Avatar sx={{ width: 32, height: 32, bgcolor: "secondary.main" }}>MC</Avatar>
                    </Tooltip>
                    <Tooltip title="Dr. Emily Davis - Resident">
                      <Avatar sx={{ width: 32, height: 32, bgcolor: "success.main" }}>ED</Avatar>
                    </Tooltip>
                    <IconButton size="small" sx={{ width: 32, height: 32 }}>
                      <PersonAddIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>

                {/* Recent Annotations */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Recent Annotations
                  </Typography>
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                    <Box
                      sx={{ display: "flex", alignItems: "center", gap: 1, p: 1, bgcolor: "grey.50", borderRadius: 1 }}
                    >
                      <Avatar sx={{ width: 24, height: 24, bgcolor: "primary.main" }}>SJ</Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="caption" sx={{ fontWeight: 600 }}>
                          Dr. Johnson
                        </Typography>
                        <Typography variant="caption" sx={{ display: "block", color: "text.secondary" }}>
                          "Suspicious opacity in RUL"
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        2m ago
                      </Typography>
                    </Box>
                    <Box
                      sx={{ display: "flex", alignItems: "center", gap: 1, p: 1, bgcolor: "grey.50", borderRadius: 1 }}
                    >
                      <Avatar sx={{ width: 24, height: 24, bgcolor: "secondary.main" }}>MC</Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="caption" sx={{ fontWeight: 600 }}>
                          Dr. Chen
                        </Typography>
                        <Typography variant="caption" sx={{ display: "block", color: "text.secondary" }}>
                          "Cardiac silhouette enlarged"
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        5m ago
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                {/* Collaboration Actions */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Collaboration Tools
                  </Typography>
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                    <Button variant="outlined" size="small" startIcon={<ChatIcon />} fullWidth>
                      Start Discussion
                    </Button>
                    <Button variant="outlined" size="small" startIcon={<VideoCallIcon />} fullWidth>
                      Video Consultation
                    </Button>
                    <Button variant="outlined" size="small" startIcon={<ShareIcon />} fullWidth>
                      Share Study
                    </Button>
                  </Box>
                </Box>

                {/* Study Permissions */}
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Study Access
                  </Typography>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      p: 1,
                      bgcolor: "grey.50",
                      borderRadius: 1,
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <VisibilityIcon fontSize="small" color="success" />
                      <Typography variant="caption">Shared with team</Typography>
                    </Box>
                    <IconButton size="small">
                      <LockIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Drawer>
      </Box>
    </Box>
  )
}

export default StudyViewer
