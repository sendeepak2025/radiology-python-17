@echo off
echo.
echo ========================================
echo  Starting FIXED Upload Backend
echo ========================================
echo.

REM Kill existing processes
taskkill /F /IM python.exe >nul 2>&1

echo Starting fixed backend with working uploads...
echo API: http://localhost:8000
echo Upload: http://localhost:8000/patients/PAT001/upload/dicom
echo.

python -m uvicorn fixed_upload_backend:app --host 0.0.0.0 --port 8000 --reload

pause