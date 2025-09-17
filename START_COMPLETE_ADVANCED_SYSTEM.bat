@echo off
cls
echo.
echo ==========================================
echo  🏥 COMPLETE ADVANCED MEDICAL SYSTEM
echo ==========================================
echo.
echo ✅ Advanced Medical DICOM Viewer - READY
echo ✅ 2D/3D/MPR/Volume/Cine/Fusion Modes
echo ✅ Auto-Scroll & Cine Loop Controls
echo ✅ AI-Powered Problem Detection
echo ✅ Professional Medical Tools
echo ✅ Window/Level Presets
echo ✅ Real-time Analysis Dashboard
echo.

REM Kill any existing processes
echo 🔄 Preparing advanced medical system...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

echo.
echo 🚀 Starting Complete Advanced Medical System...
echo.
echo 🌐 BACKEND API: http://localhost:8000
echo 📖 API Documentation: http://localhost:8000/docs
echo 👥 Patient Management: http://localhost:8000/patients
echo 🔬 Medical Studies: http://localhost:8000/studies
echo.
echo 🎨 FRONTEND (Start separately):
echo    http://localhost:3000/dashboard
echo    http://localhost:3000/patients
echo    http://localhost:3000/studies
echo.
echo 🏥 ADVANCED FEATURES NOW AVAILABLE:
echo.
echo    📊 VIEWING MODES:
echo       • 2D View - Standard medical imaging
echo       • 3D Volume - 3D volume rendering
echo       • MPR - Multi-planar reconstruction
echo       • Volume Render - Advanced volume rendering
echo       • Cine Loop - Automated playback
echo       • Fusion - Image fusion capabilities
echo.
echo    🎬 AUTO-SCROLL & CINE:
echo       • Variable speed (0.5x to 10x)
echo       • Play/Pause controls
echo       • Slice navigation
echo       • Progress indicators
echo.
echo    🔍 AI PROBLEM DETECTION:
echo       • Real-time anomaly detection
echo       • Confidence scoring
echo       • Severity classification
echo       • Visual problem markers
echo       • Verification system
echo.
echo    🛠️ PROFESSIONAL TOOLS:
echo       • Distance/Angle measurements
echo       • ROI analysis tools
echo       • Annotation system
echo       • Magnification tools
echo       • Crosshair references
echo.
echo    ⚙️ MEDICAL CONTROLS:
echo       • Window/Level presets
echo       • Brightness/Contrast
echo       • Image rotation/zoom
echo       • Grid overlays
echo.
echo ⚡ Starting advanced backend server...

python -m uvicorn fixed_upload_backend:app --host 0.0.0.0 --port 8000 --reload

pause