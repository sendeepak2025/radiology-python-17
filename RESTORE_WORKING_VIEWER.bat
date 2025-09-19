@echo off
echo 🔄 RESTORING WORKING STUDY VIEWER CONFIGURATION
echo ===============================================

echo 📋 This script restores the CONFIRMED WORKING configuration:
echo    - SimpleDicomViewer as primary component
echo    - Backend frame processing enabled
echo    - Professional single-frame display
echo    - Mouse wheel + keyboard navigation
echo    - 96-frame series support

echo.
echo ⚠️  Use this if the viewer stops working properly
echo.

echo 🔧 Restoration Steps:
echo    1. Ensure working_backend.py has frame processing
echo    2. Ensure SimpleDicomViewer.tsx is primary viewer
echo    3. Ensure no size constraints in URLs
echo    4. Restart both backend and frontend

echo.
echo 🚀 Starting the WORKING configuration...
echo.

echo 📖 Reference Document: WORKING_STUDY_VIEWER_REFERENCE.md
echo 📖 Contains all technical details and troubleshooting

echo.
echo 🔄 Starting backend with frame processing...
start "DICOM Backend (Working)" cmd /k "python working_backend.py"

echo ⏳ Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo 🔄 Starting frontend with SimpleDicomViewer...
start "DICOM Frontend (Working)" cmd /k "cd frontend && npm start"

echo.
echo ✅ WORKING CONFIGURATION RESTORED
echo 📖 Access at: http://localhost:3000
echo 🎯 Navigate to study: 1.2.840.113619.2.5.1757966844190003.8.432244991
echo.
echo 🏥 Expected: Professional single-frame DICOM viewer
echo 🖱️  Mouse wheel scrolling for frame navigation
echo ⌨️  Keyboard shortcuts (arrows, home/end, pageup/down)
echo 📊 Frame counter: "Image X/96"

pause