@echo off
cls
echo.
echo ==========================================
echo  🏥 ADVANCED MEDICAL DICOM SYSTEM
echo ==========================================
echo.
echo ✅ AI-Powered Medical Imaging Platform
echo ✅ Professional DICOM Viewer
echo ✅ Advanced 2D/3D/MPR/Volume Rendering
echo ✅ Real-time Anomaly Detection
echo ✅ Hospital-Grade Interface
echo.

REM Kill any existing processes to ensure clean start
echo 🔄 Cleaning up existing processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul

echo.
echo 🔍 Running system health check...
python SYSTEM_STATUS_CHECK.py

echo.
echo 🚀 Starting Advanced Medical Backend...
echo.
echo 🌐 Backend API: http://localhost:8000
echo 📤 DICOM Upload: http://localhost:8000/patients/PAT001/upload/dicom
echo 👥 Patient Management: http://localhost:8000/patients
echo 🔬 Medical Studies: http://localhost:8000/studies
echo 📖 API Documentation: http://localhost:8000/docs
echo.
echo 🏥 Advanced Features Available:
echo    • AI Anomaly Detection
echo    • 2D/3D/MPR/Volume Rendering
echo    • Professional Medical Tools
echo    • Window/Level Controls
echo    • Real-time Analysis
echo    • Medical Measurements
echo.
echo ⚡ Starting backend server...

REM Start the advanced backend
python -m uvicorn fixed_upload_backend:app --host 0.0.0.0 --port 8000 --reload

pause