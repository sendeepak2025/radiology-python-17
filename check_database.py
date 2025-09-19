#!/usr/bin/env python3
"""
Check the database structure and content
"""

import sqlite3
from pathlib import Path

def check_database():
    print("🗄️  Database Structure Checker")
    print("=" * 50)
    
    # Connect to database
    db_path = "kiro_mini.db"
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"📋 Found {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        print(f"\n🔍 Table: {table_name}")
        
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"   Columns ({len(columns)}):")
        for col in columns:
            print(f"     - {col[1]} ({col[2]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   Rows: {count}")
        
        # If it's patients table, show some data
        if table_name == 'patients' and count > 0:
            cursor.execute(f"SELECT patient_id, first_name, last_name FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            print(f"   Sample data:")
            for row in rows:
                print(f"     - {row[0]}: {row[1]} {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()