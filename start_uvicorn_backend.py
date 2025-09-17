#!/usr/bin/env python3
"""
Start backend with uvicorn after cleaning up ports
"""

import subprocess
import sys
import os
import time
import socket

def check_port(port):
    """Check if port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result != 0  # True if port is available
    except:
        return True

def kill_port_processes():
    """Kill processes on common ports"""
    ports_to_check = [3000, 8000]
    
    for port in ports_to_check:
        if not check_port(port):
            print(f"🔄 Killing processes on port {port}...")
            try:
                # Get process using the port
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                                print(f"  ✅ Killed PID {pid} on port {port}")
                            except:
                                pass
            except Exception as e:
                print(f"  ⚠️  Error killing port {port}: {e}")
    
    # Wait for ports to clear
    time.sleep(2)

def start_backend():
    """Start the backend with uvicorn"""
    print("🚀 Starting Kiro Backend with Uvicorn...")
    print("=" * 50)
    
    # Kill existing processes
    kill_port_processes()
    
    # Check if database exists
    if not os.path.exists("kiro_mini.db"):
        print("❌ kiro_mini.db not found!")
        return False
    
    print("✅ Database found")
    print("📊 Backend API: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Test patients: http://localhost:8000/patients/?limit=100")
    print("💊 Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start uvicorn with the fixed backend
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "fixed_backend:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 Backend stopped")
        return True
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

def main():
    print("🏥 Kiro Backend Startup (Uvicorn)")
    print("=" * 40)
    
    # Check dependencies
    try:
        import uvicorn
        import fastapi
        print("✅ Dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing required packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic'])
    
    # Start backend
    start_backend()

if __name__ == "__main__":
    main()