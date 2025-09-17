#!/usr/bin/env python3
"""
Startup script for the fixed Kiro backend that works with existing kiro_mini.db
"""

import subprocess
import sys
import os
import time

def check_database():
    """Check if kiro_mini.db exists."""
    if not os.path.exists("kiro_mini.db"):
        print("❌ kiro_mini.db not found in current directory")
        print("Please make sure you're running this from the directory containing kiro_mini.db")
        return False
    
    print("✅ Found kiro_mini.db")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ Packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    else:
        print("✅ All required packages are available")
    
    return True

def start_server():
    """Start the fixed backend server."""
    print("🚀 Starting Fixed Kiro Backend...")
    print("📊 Backend API: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔧 Debug endpoint: http://localhost:8000/debug/patients/count")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "fixed_backend:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

def main():
    """Main startup function."""
    print("🏥 Kiro Fixed Backend Startup")
    print("=" * 40)
    
    # Check if database exists
    if not check_database():
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()