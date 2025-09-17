@echo off
echo Resetting Backend and Starting Fresh...
echo.

REM Clean up old metadata
if exist study_metadata.json del study_metadata.json
echo Cleared old study metadata

REM Kill any existing backend processes
taskkill /f /im python.exe 2>nul
echo Stopped existing backend processes

echo.
echo Starting Fixed Backend...
echo - Proper study UID generation
echo - Metadata persistence
echo - Debug logging enabled
echo - Upload directory: uploads/
echo.
echo Backend will be available at: http://localhost:8000
echo Press Ctrl+C to stop
echo.

python final_working_backend.py