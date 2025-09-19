#!/usr/bin/env python3
"""
Check the study data for PAT002 in the database
"""

import sqlite3
import json
from pathlib import Path

def check_study_data():
    print("🏥 Study Data Checker for PAT002")
    print("=" * 50)
    
    # Connect to database
    db_path = "kiro_mini.db"
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if studies table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='studies'")
    if not cursor.fetchone():
        print("❌ Studies table not found in database")
        conn.close()
        return
    
    # Get all studies for PAT002
    cursor.execute("SELECT * FROM studies WHERE patient_id = 'PAT002'")
    studies = cursor.fetchall()
    
    if not studies:
        print("❌ No studies found for PAT002")
        conn.close()
        return
    
    # Get column names
    cursor.execute("PRAGMA table_info(studies)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"📋 Found {len(studies)} studies for PAT002:")
    
    for i, study_row in enumerate(studies):
        study = dict(zip(columns, study_row))
        print(f"\n🔍 Study {i+1}:")
        print(f"   Study UID: {study.get('study_uid', 'N/A')}")
        print(f"   Patient ID: {study.get('patient_id', 'N/A')}")
        print(f"   Filename: {study.get('filename', 'N/A')}")
        print(f"   Original Filename: {study.get('original_filename', 'N/A')}")
        print(f"   Status: {study.get('status', 'N/A')}")
        print(f"   Modality: {study.get('modality', 'N/A')}")
        print(f"   Study Description: {study.get('study_description', 'N/A')}")
        
        # Check image URLs
        image_urls = study.get('image_urls')
        if image_urls:
            try:
                if isinstance(image_urls, str):
                    urls = json.loads(image_urls) if image_urls.startswith('[') else [image_urls]
                else:
                    urls = image_urls
                print(f"   Image URLs ({len(urls)}):")
                for j, url in enumerate(urls[:5]):  # Show first 5
                    print(f"     {j+1}. {url}")
                if len(urls) > 5:
                    print(f"     ... and {len(urls) - 5} more")
            except:
                print(f"   Image URLs (raw): {image_urls}")
        else:
            print(f"   Image URLs: None")
        
        # Check DICOM content URLs
        dicom_urls = study.get('dicom_content_urls')
        if dicom_urls:
            print(f"   DICOM Content URLs: {dicom_urls}")
        else:
            print(f"   DICOM Content URLs: None")
        
        # Check DICOM URL
        dicom_url = study.get('dicom_url')
        if dicom_url:
            print(f"   DICOM URL: {dicom_url}")
        else:
            print(f"   DICOM URL: None")
    
    conn.close()

if __name__ == "__main__":
    check_study_data()