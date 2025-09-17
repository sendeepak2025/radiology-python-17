#!/usr/bin/env python3
"""
Quick start script for the working backend
"""

import subprocess
import sys
import os
import time
import threading

def check_port_8000():
    """Check if port 8000 is available"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        return result != 0  # True if port is available
    except:
        return True

def kill_port_8000():
    """Kill any process using port 8000"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
        else:  # Unix/Linux
            subprocess.run(['pkill', '-f', 'uvicorn'], capture_output=True)
        time.sleep(2)
    except:
        pass

def start_backend():
    """Start the backend server"""
    print("🚀 Starting Kiro Backend...")
    
    # Kill any existing server
    if not check_port_8000():
        print("🔄 Stopping existing server...")
        kill_port_8000()
    
    print("📊 Backend will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Test endpoint: http://localhost:8000/patients/?limit=100")
    print("\nPress Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Start the fixed backend
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "fixed_backend:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🏥 Kiro Patient Management System")
    print("=" * 40)
    
    # Check if database exists
    if not os.path.exists("kiro_mini.db"):
        print("❌ kiro_mini.db not found!")
        exit(1)
    
    print("✅ Database found")
    start_backend()