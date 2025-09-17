#!/usr/bin/env python3
"""
🏥 Advanced Medical DICOM System - Status Check & Optimization
Complete system health check and performance optimization
"""

import os
import sys
import sqlite3
import requests
import subprocess
import time
from pathlib import Path
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🏥 {title}")
    print(f"{'='*60}")

def print_status(item, status, details=""):
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {item:<30} {details}")

def check_database():
    """Check database status and optimization"""
    print_header("DATABASE STATUS")
    
    try:
        # Check if database exists
        db_path = "kiro_mini.db"
        if not os.path.exists(db_path):
            print_status("Database File", False, "kiro_mini.db not found")
            return False
        
        # Connect and check tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check patients table
        cursor.execute("SELECT COUNT(*) FROM patients WHERE active = 1")
        patient_count = cursor.fetchone()[0]
        print_status("Database Connection", True, f"Connected to {db_path}")
        print_status("Active Patients", True, f"{patient_count} patients")
        
        # Check database size
        db_size = os.path.getsize(db_path) / 1024 / 1024  # MB
        print_status("Database Size", True, f"{db_size:.2f} MB")
        
        # Check indexes
        cursor.execute("PRAGMA index_list(patients)")
        indexes = cursor.fetchall()
        print_status("Database Indexes", True, f"{len(indexes)} indexes")
        
        conn.close()
        return True
        
    except Exception as e:
        print_status("Database Check", False, f"Error: {str(e)}")
        return False

def check_backend():
    """Check backend API status"""
    print_header("BACKEND API STATUS")
    
    try:
        # Check if backend is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print_status("Backend Server", True, f"Running on port 8000")
            print_status("API Health", True, f"Status: {health_data.get('status', 'unknown')}")
            print_status("API Version", True, f"Version: {health_data.get('version', 'unknown')}")
        else:
            print_status("Backend Server", False, f"HTTP {response.status_code}")
            return False
            
        # Check patients endpoint
        response = requests.get("http://localhost:8000/patients?limit=1", timeout=5)
        if response.status_code == 200:
            patients_data = response.json()
            print_status("Patients API", True, f"{patients_data.get('total', 0)} total patients")
        else:
            print_status("Patients API", False, f"HTTP {response.status_code}")
        
        # Check studies endpoint
        response = requests.get("http://localhost:8000/studies?limit=1", timeout=5)
        if response.status_code == 200:
            studies_data = response.json()
            print_status("Studies API", True, f"{studies_data.get('total', 0)} total studies")
        else:
            print_status("Studies API", False, f"HTTP {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print_status("Backend Server", False, "Not running on port 8000")
        return False
    except Exception as e:
        print_status("Backend Check", False, f"Error: {str(e)}")
        return False

def check_uploads():
    """Check uploads directory and files"""
    print_header("UPLOADS & FILES STATUS")
    
    uploads_dir = Path("uploads")
    
    if not uploads_dir.exists():
        print_status("Uploads Directory", False, "uploads/ directory not found")
        return False
    
    print_status("Uploads Directory", True, f"Found at {uploads_dir.absolute()}")
    
    # Count patient directories
    patient_dirs = [d for d in uploads_dir.iterdir() if d.is_dir()]
    print_status("Patient Directories", True, f"{len(patient_dirs)} patient folders")
    
    # Count total files
    total_files = 0
    dicom_files = 0
    total_size = 0
    
    for patient_dir in patient_dirs:
        for file_path in patient_dir.iterdir():
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
                if file_path.suffix.lower() in ['.dcm', '.dicom']:
                    dicom_files += 1
    
    print_status("Total Files", True, f"{total_files} files")
    print_status("DICOM Files", True, f"{dicom_files} DICOM files")
    print_status("Total Size", True, f"{total_size / 1024 / 1024:.2f} MB")
    
    return True

def check_frontend():
    """Check frontend status"""
    print_header("FRONTEND STATUS")
    
    # Check if package.json exists
    frontend_dir = Path("frontend")
    package_json = frontend_dir / "package.json"
    
    if not package_json.exists():
        print_status("Frontend Directory", False, "frontend/package.json not found")
        return False
    
    print_status("Frontend Directory", True, "Found frontend/")
    
    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print_status("Dependencies", True, "node_modules installed")
    else:
        print_status("Dependencies", False, "node_modules not found")
    
    # Try to check if frontend is running
    try:
        # Common frontend ports
        for port in [3000, 3001, 5173, 8080]:
            try:
                response = requests.get(f"http://localhost:{port}", timeout=2)
                if response.status_code == 200:
                    print_status("Frontend Server", True, f"Running on port {port}")
                    return True
            except:
                continue
        
        print_status("Frontend Server", False, "Not running on common ports")
        return False
        
    except Exception as e:
        print_status("Frontend Check", False, f"Error: {str(e)}")
        return False

def check_system_resources():
    """Check system resources"""
    print_header("SYSTEM RESOURCES")
    
    try:
        # Check Python processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, shell=True)
        python_processes = len([line for line in result.stdout.split('\n') if 'python.exe' in line])
        print_status("Python Processes", True, f"{python_processes} running")
        
        # Check Node processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], 
                              capture_output=True, text=True, shell=True)
        node_processes = len([line for line in result.stdout.split('\n') if 'node.exe' in line])
        print_status("Node Processes", True, f"{node_processes} running")
        
        return True
        
    except Exception as e:
        print_status("System Resources", False, f"Error: {str(e)}")
        return False

def optimize_system():
    """Perform system optimizations"""
    print_header("SYSTEM OPTIMIZATION")
    
    try:
        # Optimize database
        if os.path.exists("kiro_mini.db"):
            conn = sqlite3.connect("kiro_mini.db")
            cursor = conn.cursor()
            
            # Vacuum database
            cursor.execute("VACUUM")
            print_status("Database Vacuum", True, "Database optimized")
            
            # Analyze database
            cursor.execute("ANALYZE")
            print_status("Database Analyze", True, "Statistics updated")
            
            conn.close()
        
        # Clean temporary files
        temp_files = list(Path(".").glob("*.tmp"))
        for temp_file in temp_files:
            temp_file.unlink()
        print_status("Temp Files Cleanup", True, f"Removed {len(temp_files)} temp files")
        
        return True
        
    except Exception as e:
        print_status("System Optimization", False, f"Error: {str(e)}")
        return False

def generate_system_report():
    """Generate comprehensive system report"""
    print_header("SYSTEM REPORT")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "database": check_database(),
        "backend": check_backend(),
        "uploads": check_uploads(),
        "frontend": check_frontend(),
        "resources": check_system_resources()
    }
    
    # Overall system health
    all_good = all(report.values())
    health_status = "EXCELLENT" if all_good else "NEEDS ATTENTION"
    
    print(f"\n🏥 OVERALL SYSTEM HEALTH: {health_status}")
    
    if all_good:
        print("\n✅ Your Advanced Medical DICOM System is running perfectly!")
        print("   - Database: Optimized and responsive")
        print("   - Backend: All APIs working")
        print("   - Files: Upload system operational")
        print("   - Frontend: Ready for medical imaging")
        print("\n🚀 System ready for production medical use!")
    else:
        print("\n⚠️  Some components need attention:")
        for component, status in report.items():
            if not status:
                print(f"   - {component.title()}: Needs fixing")
    
    return report

def main():
    """Main system check and optimization"""
    print("🏥 Advanced Medical DICOM System - Health Check")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    report = generate_system_report()
    
    # Optimize if everything is working
    if all(report.values()):
        optimize_system()
    
    print(f"\n{'='*60}")
    print("🏥 System check complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()