@echo off
echo 🚀 Starting Complete DICOM System...
echo ==================================

echo 📋 System Components:
echo    - Backend: Python FastAPI server (Port 8000)
echo    - Frontend: React application (Port 3000)
echo    - DICOM Viewer: Professional single-frame display
echo    - Navigation: Mouse wheel + keyboard shortcuts

echo.
echo 🔄 Starting backend first...
start "DICOM Backend" cmd /k "python working_backend.py"

echo ⏳ Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo 🔄 Starting frontend...
start "DICOM Frontend" cmd /k "cd frontend && npm start"

echo.
echo ✅ Both services starting...
echo 📖 Access the application at: http://localhost:3000
echo 📖 Backend API at: http://localhost:8000
echo.
echo 🎯 Professional DICOM Viewer Features:
echo    - Single frame display (like medical workstations)
echo    - Mouse wheel scrolling for frame navigation
echo    - Arrow keys for precise navigation
echo    - Home/End for first/last frame
echo    - PageUp/PageDown for 10-frame jumps
echo    - Play button for auto-cycling
echo    - Professional medical imaging interface

pause