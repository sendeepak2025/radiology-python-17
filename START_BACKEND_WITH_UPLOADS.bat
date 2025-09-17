@echo off
echo.
echo ==========================================
echo  Kiro Backend with File Upload Support
echo ==========================================
echo.

REM Kill existing processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo Starting backend with upload support...
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo Upload: http://localhost:8000/patients/{patient_id}/upload
echo.

python -m uvicorn backend_with_uploads:app --host 0.0.0.0 --port 8000 --reload

pause