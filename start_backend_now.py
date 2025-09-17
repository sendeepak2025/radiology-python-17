#!/usr/bin/env python3
"""
Direct backend startup with uvicorn - no cleanup, just start
"""

import subprocess
import sys
import os

def start_backend_direct():
    """Start backend directly with uvicorn"""
    print("🚀 Starting Backend with Uvicorn...")
    print("📊 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🔍 Test: http://localhost:8000/patients/?limit=100")
    print("\nPress Ctrl+C to stop")
    print("-" * 40)
    
    try:
        # Start uvicorn directly
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "fixed_backend:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🏥 Kiro Backend - Direct Start")
    print("=" * 30)
    
    # Check database
    if os.path.exists("kiro_mini.db"):
        print("✅ Database found")
    else:
        print("❌ Database not found")
        exit(1)
    
    start_backend_direct()