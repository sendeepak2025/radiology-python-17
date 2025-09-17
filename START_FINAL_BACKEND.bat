@echo off
echo Starting Final Working Backend...
echo.
echo Backend Features:
echo - Patient Management (GET /patients, GET /patients/{id})
echo - Study Management (GET /studies, GET /patients/{id}/studies)
echo - DICOM Upload (POST /patients/{id}/upload/dicom)
echo - File Serving (GET /uploads/{patient_id}/{filename})
echo - Health Checks (GET /health, GET /upload/health)
echo.
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python final_working_backend.py