import os
import sqlite3
import datetime
from src.data.database import DatabaseManager

class BackupService:
    def __init__(self, backup_dir="backup"):
        self.backup_dir = backup_dir
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def backup_daily_attendance(self, target_date: datetime.date = None):
        """
        Backs up the attendance records for a specific day from MongoDB to a SQLite file.
        If target_date is None, defaults to today.
        """
        if target_date is None:
            target_date = datetime.date.today()
            
        
        date_str = target_date.strftime("%d%B%Y")
        db_filename = os.path.join(self.backup_dir, f"{date_str}.db")
        
        
        db = DatabaseManager.get_db()
        events_col = db.attendance_records
        
        
        today_str = target_date.strftime("%Y-%m-%d")
        daily_events = list(events_col.find({
            "work_date": today_str
        }))
        
        
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_backup (
                id TEXT PRIMARY KEY,
                employee_id TEXT,
                work_date TEXT,
                clock_in_at TEXT,
                clock_out_at TEXT,
                status TEXT
            )
        """)
        
        
        inserted_count = 0
        for event in daily_events:
            
            cursor.execute("""
                INSERT OR IGNORE INTO attendance_backup (id, employee_id, work_date, clock_in_at, clock_out_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(event.get("_id", "")),
                str(event.get("employee_id", "UNKNOWN")),
                event.get("work_date", ""),
                str(event.get("clock_in_at", "")),
                str(event.get("clock_out_at", "")),
                event.get("status", "present")
            ))
            if cursor.rowcount > 0:
                inserted_count += 1
                
        conn.commit()
        conn.close()
        
        return db_filename, inserted_count

if __name__ == "__main__":
    
    backup = BackupService()
    print("Running backup for today...")
    file_path, count = backup.backup_daily_attendance()
    print(f"Backed up {count} records to {file_path}")
