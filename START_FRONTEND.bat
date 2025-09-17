@echo off
cls
echo.
echo ==========================================
echo  🎨 ADVANCED MEDICAL FRONTEND
echo ==========================================
echo.
echo ✅ Professional Medical Interface
echo ✅ Advanced DICOM Viewer
echo ✅ AI-Powered Analysis Dashboard
echo ✅ Real-time Medical Imaging
echo.

cd frontend

echo 🔍 Checking frontend dependencies...
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
)

echo.
echo 🚀 Starting Advanced Medical Frontend...
echo.
echo 🌐 Frontend URL: http://localhost:3000
echo 🏥 Dashboard: http://localhost:3000/dashboard
echo 👥 Patients: http://localhost:3000/patients
echo 🔬 Studies: http://localhost:3000/studies
echo.
echo 🎯 Advanced Medical Features:
echo    • Professional Medical Dashboard
echo    • AI-Powered DICOM Viewer
echo    • Real-time Anomaly Detection
echo    • Advanced 2D/3D Rendering
echo    • Medical Measurement Tools
echo    • Hospital-Grade Interface
echo.

npm start

pause