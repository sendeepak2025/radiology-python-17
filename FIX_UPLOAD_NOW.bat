@echo off
echo Fixing upload issue NOW...
echo.

REM Kill any existing Python processes
taskkill /F /IM python.exe >nul 2>&1

echo Starting backend with upload support on port 8000...
python -m uvicorn backend_with_uploads:app --host 0.0.0.0 --port 8000 --reload

pause