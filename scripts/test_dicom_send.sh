#!/bin/bash

# Test script for sending DICOM files to Kiro-mini Orthanc server
# Requires DCMTK tools (storescu) to be installed

set -e

ORTHANC_HOST="localhost"
ORTHANC_PORT="4242"
ORTHANC_AET="KIRO-MINI"
LOCAL_AET="TEST_SCU"

echo "=== Kiro-mini DICOM Test Script ==="
echo "Target: $ORTHANC_AET@$ORTHANC_HOST:$ORTHANC_PORT"
echo "Source: $LOCAL_AET"
echo

# Check if storescu is available
if ! command -v storescu &> /dev/null; then
    echo "Error: storescu not found. Please install DCMTK tools."
    echo "Ubuntu/Debian: sudo apt-get install dcmtk"
    echo "macOS: brew install dcmtk"
    echo "Windows: Download from https://dicom.offis.de/dcmtk"
    exit 1
fi

# Check if test DICOM files exist
if [ ! -d "test_dicoms" ]; then
    echo "Generating sample DICOM files..."
    python3 scripts/generate_sample_dicom.py
fi

# Test Orthanc connectivity
echo "Testing Orthanc connectivity..."
if ! nc -z $ORTHANC_HOST $ORTHANC_PORT 2>/dev/null; then
    echo "Error: Cannot connect to Orthanc at $ORTHANC_HOST:$ORTHANC_PORT"
    echo "Make sure Orthanc is running: docker-compose up orthanc"
    exit 1
fi

echo "✓ Orthanc is accessible"
echo

# Send each DICOM file
for dcm_file in test_dicoms/*.dcm; do
    if [ -f "$dcm_file" ]; then
        echo "Sending: $(basename $dcm_file)"
        
        # Send DICOM file
        if storescu -aec $ORTHANC_AET -aet $LOCAL_AET $ORTHANC_HOST $ORTHANC_PORT "$dcm_file"; then
            echo "✓ Successfully sent: $(basename $dcm_file)"
        else
            echo "✗ Failed to send: $(basename $dcm_file)"
        fi
        echo
        
        # Wait a moment between sends
        sleep 1
    fi
done

echo "=== DICOM Send Test Complete ==="
echo
echo "Check results:"
echo "- Orthanc Web UI: http://localhost:8042"
echo "- Backend logs: docker-compose logs backend"
echo "- Study ingestion: curl http://localhost:8000/studies"