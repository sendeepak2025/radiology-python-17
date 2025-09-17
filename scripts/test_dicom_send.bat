@echo off
REM Test script for sending DICOM files to Kiro-mini Orthanc server
REM Requires DCMTK tools (storescu) to be installed

setlocal enabledelayedexpansion

set ORTHANC_HOST=localhost
set ORTHANC_PORT=4242
set ORTHANC_AET=KIRO-MINI
set LOCAL_AET=TEST_SCU

echo === Kiro-mini DICOM Test Script ===
echo Target: %ORTHANC_AET%@%ORTHANC_HOST%:%ORTHANC_PORT%
echo Source: %LOCAL_AET%
echo.

REM Check if storescu is available
where storescu >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: storescu not found. Please install DCMTK tools.
    echo Download from: https://dicom.offis.de/dcmtk
    echo Or use chocolatey: choco install dcmtk
    exit /b 1
)

REM Check if test DICOM files exist
if not exist "test_dicoms" (
    echo Generating sample DICOM files...
    python scripts/generate_sample_dicom.py
)

REM Test Orthanc connectivity
echo Testing Orthanc connectivity...
powershell -Command "Test-NetConnection -ComputerName %ORTHANC_HOST% -Port %ORTHANC_PORT% -InformationLevel Quiet" >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Cannot connect to Orthanc at %ORTHANC_HOST%:%ORTHANC_PORT%
    echo Make sure Orthanc is running: docker-compose up orthanc
    exit /b 1
)

echo ✓ Orthanc is accessible
echo.

REM Send each DICOM file
for %%f in (test_dicoms\*.dcm) do (
    echo Sending: %%~nxf
    
    REM Send DICOM file
    storescu -aec %ORTHANC_AET% -aet %LOCAL_AET% %ORTHANC_HOST% %ORTHANC_PORT% "%%f"
    if !errorlevel! equ 0 (
        echo ✓ Successfully sent: %%~nxf
    ) else (
        echo ✗ Failed to send: %%~nxf
    )
    echo.
    
    REM Wait a moment between sends
    timeout /t 1 /nobreak >nul
)

echo === DICOM Send Test Complete ===
echo.
echo Check results:
echo - Orthanc Web UI: http://localhost:8042
echo - Backend logs: docker-compose logs backend
echo - Study ingestion: curl http://localhost:8000/studies

pause