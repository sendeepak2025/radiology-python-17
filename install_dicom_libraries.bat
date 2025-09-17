@echo off
echo ========================================
echo    PROFESSIONAL DICOM SETUP
echo ========================================
echo.
echo 🔧 Installing professional DICOM processing libraries...
echo.

echo 1. Installing core DICOM libraries...
pip install pydicom

echo.
echo 2. Installing DICOM-NumPy integration...
pip install dicom-numpy

echo.
echo 3. Installing SimpleITK (Advanced medical imaging)...
pip install SimpleITK

echo.
echo 4. Installing supporting libraries...
pip install numpy matplotlib opencv-python

echo.
echo 5. Installing additional medical imaging tools...
pip install scikit-image nibabel

echo.
echo ✅ Installation complete!
echo.
echo 🧪 Testing installation...
python check_dicom_libraries.py

echo.
echo 🎉 Professional DICOM processing environment ready!
pause