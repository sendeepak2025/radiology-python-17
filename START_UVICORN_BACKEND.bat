@echo off
echo.
echo ==========================================
echo  Kiro Backend with Uvicorn (Port 8000)
echo ==========================================
echo.

REM Kill any existing processes on ports 3000 and 8000
echo Cleaning up existing processes...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if database exists
if not exist "kiro_mini.db" (
    echo ERROR: kiro_mini.db not found in current directory
    echo Please make sure you're in the correct directory
    pause
    exit /b 1
)

echo Starting Kiro Backend with Uvicorn...
echo Backend will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

REM Start the backend
python start_uvicorn_backend.py

echo.
echo Backend stopped.
pause