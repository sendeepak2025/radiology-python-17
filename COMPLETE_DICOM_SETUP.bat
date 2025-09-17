@echo off
echo ========================================
echo    COMPLETE PROFESSIONAL DICOM SETUP
echo ========================================
echo.
echo 🏥 Setting up professional medical imaging environment...
echo.

echo 📦 Step 1: Installing DICOM libraries...
echo.
pip install pydicom dicom-numpy SimpleITK numpy matplotlib opencv-python scikit-image nibabel

echo.
echo 🧪 Step 2: Testing installation...
python check_dicom_libraries.py

echo.
echo 🔄 Step 3: Processing existing DICOM files...
python advanced_dicom_processor.py

echo.
echo 🚀 Step 4: Starting enhanced backend...
echo.
echo ✅ Professional DICOM Features:
echo    - Advanced DICOM metadata extraction
echo    - Multi-format image processing (normalized, windowed, thumbnail)
echo    - SimpleITK integration for medical imaging
echo    - Automatic preview generation
echo    - Comprehensive error handling
echo.
echo 🌐 Backend: http://localhost:8000
echo 🖥️  Frontend: http://localhost:3000
echo.
echo Press Ctrl+C to stop backend
echo.

python final_working_backend.py