@echo off
echo.
echo ========================================
echo  Kiro Fixed Backend (uses kiro_mini.db)
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if kiro_mini.db exists
if not exist "kiro_mini.db" (
    echo ERROR: kiro_mini.db not found in current directory
    echo Please make sure you're in the correct directory
    pause
    exit /b 1
)

echo Starting fixed backend with existing database...
echo.

REM Run the startup script
python start_fixed_backend.py

echo.
echo Backend stopped.
pause