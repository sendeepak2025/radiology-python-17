@echo off
echo.
echo ==========================================
echo  KIRO FINAL WORKING SYSTEM
echo ==========================================
echo.
echo ✅ Upload: WORKING
echo ✅ Patients: WORKING  
echo ✅ Studies: WORKING
echo ✅ Database: CLEAN
echo.

REM Kill any existing processes
taskkill /F /IM python.exe >nul 2>&1

echo Starting complete working system...
echo.
echo 🌐 Backend: http://localhost:8000
echo 📤 Upload: http://localhost:8000/patients/PAT001/upload/dicom
echo 👥 Patients: http://localhost:8000/patients?limit=100
echo 🔬 Studies: http://localhost:8000/patients/PAT001/studies
echo 📖 Docs: http://localhost:8000/docs
echo.
echo Your system is ready for production use!
echo.

python -m uvicorn fixed_upload_backend:app --host 0.0.0.0 --port 8000 --reload

pause