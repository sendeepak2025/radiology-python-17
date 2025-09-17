@echo off
echo ========================================
echo    CLEAN MEDICAL IMAGING UI SYSTEM
echo ========================================
echo.
echo 🎨 Starting Professional Medical Interface
echo.

REM Ensure database and processed images exist
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

REM Process DICOM files and update metadata
echo 🔄 Processing DICOM files...
python simple_dicom_processor.py
python update_existing_studies.py

echo.
echo ✅ Clean Medical UI System Ready!
echo.
echo 🎨 PROFESSIONAL UI FEATURES:
echo    ✅ Clean, modern medical interface design
echo    ✅ Professional DICOM viewer with controls
echo    ✅ Streamlined patient management
echo    ✅ Clean dashboard with key metrics
echo    ✅ Intuitive upload and study management
echo    ✅ Medical-grade dark theme for image viewing
echo    ✅ Responsive design for all devices
echo.
echo 🏥 MEDICAL IMAGING COMPONENTS:
echo    📊 CleanDashboard - Professional overview
echo    👤 CleanPatientList - Streamlined patient management
echo    🖼️  ProfessionalDicomViewer - Medical-grade image viewer
echo    📤 SmartDicomUpload - Intelligent file processing
echo.
echo 🌐 System URLs:
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000 (start with: npm start)
echo    Dashboard: http://localhost:3000/dashboard
echo    Patients: http://localhost:3000/patients
echo    Studies: http://localhost:3000/studies/{study_uid}
echo.
echo 🎯 UI/UX IMPROVEMENTS:
echo    - Clean, professional medical interface
echo    - Proper spacing and typography
echo    - Medical-grade dark theme for DICOM viewing
echo    - Intuitive navigation and controls
echo    - Responsive design for all screen sizes
echo    - Professional color scheme and icons
echo.
echo Press Ctrl+C to stop backend
echo.

python final_working_backend.py