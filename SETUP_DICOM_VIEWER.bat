@echo off
echo ========================================
echo    DICOM VIEWER SETUP & TEST
echo ========================================
echo.
echo 🔧 Setting up DICOM image viewing...
echo.

REM Check if Python libraries are available
echo 1. Checking DICOM processing libraries...
python -c "import pydicom, PIL, numpy; print('✅ All libraries available')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Missing libraries. Installing...
    pip install pydicom pillow numpy
)

echo.
echo 2. Converting existing DICOM files to previews...
python convert_dicom_to_preview.py

echo.
echo 3. Starting backend with DICOM support...
echo.
echo Backend Features:
echo ✅ DICOM file upload
echo ✅ Preview image generation
echo ✅ Proper CORS headers
echo ✅ Multiple image format support
echo.
echo Backend will be available at: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press Ctrl+C to stop
echo.

python final_working_backend.py