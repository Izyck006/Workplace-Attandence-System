"""
Script to wipe all biometric fingerprint data across all employees in the database,
while keeping all employee profiles and all attendance records intact.
Also cleans local offline cache if present.
"""
import sys
import sqlite3
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from src.data.database import DatabaseManager
from src.services.offline_sync import get_db_path

def wipe_all_fingerprints():
    print("Connecting to database...")
    db = DatabaseManager.get_db()
    
    total_employees = db.employees.count_documents({})
    enrolled_count = db.employees.count_documents({"has_fingerprint": True})
    total_records = db.attendance_records.count_documents({})
    
    print(f"Total employees: {total_employees}")
    print(f"Employees with enrolled fingerprints: {enrolled_count}")
    print(f"Existing attendance records (will NOT be touched): {total_records}")
    
    result = db.employees.update_many(
        {},
        {
            "$set": {
                "has_fingerprint": False,
                "fingerprint_samples": []
            },
            "$unset": {
                "fingerprint_descriptors": ""
            }
        }
    )
    print(f"Updated {result.modified_count} employee records in MongoDB.")
    
    sqlite_path = get_db_path()
    if os.path.exists(sqlite_path):
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cached_employees'")
            if cursor.fetchone():
                cursor.execute("UPDATE cached_employees SET fingerprint_samples = '[]'")
                conn.commit()
                print(f"Wiped {cursor.rowcount} cached employee fingerprints from local SQLite.")
            conn.close()
        except Exception as e:
            print(f"Note: Could not update SQLite offline cache: {e}")
            
    remaining = db.employees.count_documents({"has_fingerprint": True})
    records_after = db.attendance_records.count_documents({})
    print(f"Verification: Employees with fingerprints now = {remaining}")
    print(f"Verification: Attendance records preserved = {records_after}")
    print("All fingerprints successfully wiped. Employees and attendance records preserved.")

if __name__ == "__main__":
    wipe_all_fingerprints()
