@echo off
echo.
echo ================================
echo  Kiro Backend - Quick Start
echo ================================
echo.

REM Kill existing processes quickly
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo Starting backend on port 8000...
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo.

python start_backend_now.py

pause