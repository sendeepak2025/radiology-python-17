@echo off
echo.
echo ==========================================
echo  Kiro Backend - WORKING UPLOADS
echo ==========================================
echo.

REM Kill any existing processes
taskkill /F /IM python.exe >nul 2>&1

echo Starting backend with WORKING upload functionality...
echo.
echo Backend: http://localhost:8000
echo Upload:  http://localhost:8000/patients/PAT001/upload/dicom
echo Docs:    http://localhost:8000/docs
echo.
echo Your frontend uploads will now work!
echo.

python -m uvicorn fixed_upload_backend:app --host 0.0.0.0 --port 8000 --reload

pause