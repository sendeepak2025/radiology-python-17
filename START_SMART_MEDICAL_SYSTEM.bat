@echo off
echo ========================================
echo    SMART MEDICAL IMAGING SYSTEM
echo ========================================
echo.
echo 🧠 Starting Intelligent Medical Imaging Platform
echo.

REM Check and create database
if not exist kiro_mini.db (
    echo 📊 Creating medical database...
    python -c "
import sqlite3
conn = sqlite3.connect('kiro_mini.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        middle_name TEXT,
        date_of_birth TEXT,
        gender TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        medical_record_number TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT
    )
''')
cursor.execute('''
    INSERT OR REPLACE INTO patients VALUES 
    ('PAT001', 'John', 'Doe', 'M', '1980-01-01', 'M', '555-0001', 'john@example.com', '123 Main St', 'City', 'State', '12345', 'MRN001', 1, '2024-01-01'),
    ('PAT002', 'Jane', 'Smith', 'A', '1985-05-15', 'F', '555-0002', 'jane@example.com', '456 Oak Ave', 'City', 'State', '12346', 'MRN002', 1, '2024-01-01'),
    ('PAT003', 'Michael', 'Johnson', 'R', '1975-03-20', 'M', '555-0003', 'michael@example.com', '789 Pine St', 'City', 'State', '12347', 'MRN003', 1, '2024-01-01')
''')
conn.commit()
conn.close()
print('✅ Medical database ready')
"
)

REM Create directories
if not exist uploads mkdir uploads
if not exist processed mkdir processed

REM Process existing DICOM files with smart processing
echo 🔄 Smart DICOM processing...
python simple_dicom_processor.py

echo.
echo ✅ Smart Medical System Ready!
echo.
echo 🧠 INTELLIGENT FEATURES:
echo    ✅ Smart DICOM Viewer with image manipulation
echo    ✅ Intelligent upload with processing status
echo    ✅ Smart patient dashboard with previews
echo    ✅ Medical imaging dashboard with analytics
echo    ✅ Automatic DICOM processing and preview generation
echo    ✅ Advanced metadata extraction and display
echo    ✅ Professional medical imaging tools
echo    ✅ Real-time processing status and health monitoring
echo.
echo 🎯 SMART COMPONENTS:
echo    📊 SmartMedicalDashboard - Intelligent overview
echo    👤 SmartPatientDashboard - Patient-focused interface
echo    🖼️  SmartDicomViewer - Advanced image viewing
echo    📤 SmartDicomUpload - Intelligent file processing
echo.
echo 🌐 System URLs:
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000 (start with: npm start)
echo    Smart Dashboard: http://localhost:3000/dashboard
echo    Patients: http://localhost:3000/patients
echo    Studies: http://localhost:3000/studies
echo.
echo 📊 API Endpoints:
echo    Health: http://localhost:8000/health
echo    Studies: http://localhost:8000/studies
echo    Debug: http://localhost:8000/debug/studies
echo.
echo 🧪 Test: python test_complete_backend.py
echo.
echo 🎉 Your DICOM files now have:
echo    - Smart preview images for web viewing
echo    - Intelligent metadata extraction
echo    - Advanced image manipulation tools
echo    - Real-time processing status
echo    - Professional medical imaging interface
echo.
echo Press Ctrl+C to stop backend
echo.

python final_working_backend.py