@echo off
echo.
echo ==========================================
echo  STARTING WORKING BACKEND (ROOT DIR)
echo ==========================================
echo.

REM Kill any existing processes
taskkill /F /IM python.exe >nul 2>&1

REM Make sure we're in the root directory (not backend subdirectory)
echo Current directory: %CD%
echo.

REM Check if we have the working backend file
if exist "fixed_upload_backend.py" (
    echo ✅ Found working backend file
    echo Starting fixed_upload_backend.py...
    python -m uvicorn fixed_upload_backend:app --host 0.0.0.0 --port 8000 --reload
) else if exist "minimal_working_backend.py" (
    echo ✅ Found minimal backend file
    echo Starting minimal_working_backend.py...
    python -m uvicorn minimal_working_backend:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo ❌ No working backend file found!
    echo Please make sure you're in the root directory with:
    echo   - fixed_upload_backend.py
    echo   - OR minimal_working_backend.py
    echo.
    echo Current files:
    dir *.py
)

pause