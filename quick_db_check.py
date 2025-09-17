import sqlite3

try:
    conn = sqlite3.connect('kiro_mini.db')
    cursor = conn.cursor()
    
    # Check patients table
    cursor.execute("SELECT COUNT(*) FROM patients WHERE active = 1")
    active_count = cursor.fetchone()[0]
    print(f"Active patients: {active_count}")
    
    # Get sample patient data
    cursor.execute("SELECT patient_id, first_name, last_name FROM patients WHERE active = 1 LIMIT 3")
    patients = cursor.fetchall()
    print("Sample patients:")
    for patient in patients:
        print(f"  - {patient[0]}: {patient[1]} {patient[2]}")
    
    conn.close()
    print("✅ Database is working!")
    
except Exception as e:
    print(f"❌ Database error: {e}")