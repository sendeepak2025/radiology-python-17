@echo off
echo ========================================
echo    FINAL COMPLETE SYSTEM STARTUP
echo ========================================
echo.
echo 🎉 Starting Complete DICOM Medical Imaging System
echo.

REM Check if database exists
if not exist kiro_mini.db (
    echo ⚠️  Database not found. Creating sample database...
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
    ('PAT002', 'Jane', 'Smith', 'A', '1985-05-15', 'F', '555-0002', 'jane@example.com', '456 Oak Ave', 'City', 'State', '12346', 'MRN002', 1, '2024-01-01')
''')
conn.commit()
conn.close()
print('✅ Sample database created')
"
)

REM Create required directories
if not exist uploads mkdir uploads
if not exist processed mkdir processed

echo ✅ System Setup Complete!
echo.
echo 🏥 DICOM Medical Imaging Features:
echo    ✅ Patient Management
echo    ✅ DICOM File Upload & Processing
echo    ✅ Advanced Image Processing (if libraries installed)
echo    ✅ Study Viewer with Image Display
echo    ✅ Metadata Extraction & Storage
echo    ✅ Multiple Image Format Support
echo    ✅ Professional Medical Imaging Tools
echo.
echo 🌐 System URLs:
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000 (start separately)
echo    Health:   http://localhost:8000/health
echo    Debug:    http://localhost:8000/debug/studies
echo.
echo 📚 Optional: Install DICOM libraries for advanced processing:
echo    COMPLETE_DICOM_SETUP.bat
echo.
echo 🧪 Test system: python test_complete_backend.py
echo.
echo Press Ctrl+C to stop backend
echo.

python final_working_backend.py