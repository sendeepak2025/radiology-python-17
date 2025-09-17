#!/usr/bin/env python3
"""
Start the backend with upload support immediately
"""

import subprocess
import sys
import os
import time

def start_backend():
    """Start the backend with upload support"""
    print("🚀 Starting Backend with Upload Support on Port 8000...")
    print("📤 Upload endpoints will be available at:")
    print("   POST /patients/{patient_id}/upload/dicom")
    print("   POST /patients/{patient_id}/upload")
    print("   GET  /patients/{patient_id}/files")
    print("\n🌐 API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Start the backend with uploads
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend_with_uploads:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🏥 Kiro Backend with Upload Support")
    print("=" * 40)
    
    # Check if backend file exists
    if not os.path.exists("backend_with_uploads.py"):
        print("❌ backend_with_uploads.py not found!")
        print("Please make sure the file exists in the current directory")
        exit(1)
    
    # Check database
    if os.path.exists("kiro_mini.db"):
        print("✅ Database found")
    else:
        print("❌ Database not found")
        exit(1)
    
    start_backend()