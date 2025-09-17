@echo off
echo ========================================
echo    COMPLETE SYSTEM RESET AND START
echo ========================================
echo.

REM Kill any existing processes
echo 🔄 Stopping existing processes...
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul

REM Clean up old data
echo 🧹 Cleaning up old data...
if exist study_metadata.json del study_metadata.json
if exist uploads rmdir /s /q uploads
mkdir uploads

echo ✅ System cleaned

echo.
echo 🚀 Starting Fixed Backend...
echo.
echo Features:
echo - ✅ Patient Management
echo - ✅ Study Management with proper UID handling
echo - ✅ DICOM Upload with metadata persistence
echo - ✅ Debug endpoints for troubleshooting
echo - ✅ Mock data support for testing
echo.
echo Backend will be available at: http://localhost:8000
echo Debug endpoints:
echo   - http://localhost:8000/debug/studies
echo   - http://localhost:8000/debug/files
echo.
echo Press Ctrl+C to stop
echo.

python final_working_backend.py