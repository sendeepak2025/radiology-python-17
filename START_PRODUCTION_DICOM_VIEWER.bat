@echo off
echo 🏥 Starting Production-Ready DICOM Viewer System
echo ================================================

echo.
echo 🚀 Checking system status...

REM Check if backend is running
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo ✅ Backend already running on port 8000
) else (
    echo 🔄 Starting backend on port 8000...
    start "DICOM Backend" cmd /k "python working_backend.py"
    timeout /t 3 >nul
)

REM Check if frontend is running
netstat -ano | findstr :3000 >nul
if %errorlevel% == 0 (
    echo ✅ Frontend already running on port 3000
) else (
    echo 🔄 Starting frontend on port 3000...
    cd frontend
    start "DICOM Frontend" cmd /k "npm start"
    cd ..
    timeout /t 5 >nul
)

echo.
echo 🧪 Running production tests...
python test_production_viewer.py

echo.
echo 🎉 Production-Ready DICOM Viewer System Started!
echo ================================================
echo.
echo 🌐 Access URLs:
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    Health:   http://localhost:8000/health
echo.
echo 🎯 Production Features:
echo    ✅ Professional medical workstation interface
echo    ✅ 96-frame multi-frame DICOM navigation
echo    ✅ Keyboard shortcuts (arrows, space, R, etc.)
echo    ✅ Mouse wheel navigation + Ctrl+wheel zoom
echo    ✅ Real-time progress and status indicators
echo    ✅ Professional color-coded controls
echo    ✅ Patient information overlay
echo    ✅ Auto-play with loop functionality
echo.
echo 📋 Quick Start:
echo    1. Open http://localhost:3000
echo    2. Navigate to the study
echo    3. Use arrow keys or mouse wheel to navigate frames
echo    4. Press Space to auto-play through all 96 frames
echo    5. Use professional controls for zoom, rotate, reset
echo.
echo 🏆 Ready for professional medical imaging!

pause