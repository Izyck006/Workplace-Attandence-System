import os
import sys
import sqlite3
import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class BackupService:
    def __init__(self, backup_dir=None):
        if backup_dir is None:
            docs = os.path.join(os.path.expanduser("~"), "Documents", "Randaframes Attendance", "Backups")
            self.backup_dir = docs
        else:
            self.backup_dir = os.path.abspath(backup_dir)
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
        except OSError:
            self.backup_dir = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "RandaframesAttendance", "Backups")
            os.makedirs(self.backup_dir, exist_ok=True)

    def open_backup_folder(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.backup_dir)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", self.backup_dir])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", self.backup_dir])
            return True
        except Exception:
            return False

    def backup_daily_attendance(self, target_date=None, db=None, records=None, employees=None):
        if target_date is None:
            target_date = datetime.date.today()

        date_str = target_date.strftime("%d%B%Y")
        db_filename = os.path.join(self.backup_dir, f"{date_str}.db")
        today_str = target_date.strftime("%Y-%m-%d")

        if records is None:
            if db is None:
                try:
                    from src.client import ClientDatabase
                    db = ClientDatabase.get_db()
                except Exception:
                    try:
                        from src.data.database import DatabaseManager
                        db = DatabaseManager.get_db()
                    except Exception:
                        return db_filename, 0
            try:
                records = list(db.attendance_records.find({"work_date": today_str}))
            except Exception:
                records = []

        if employees is None and db is not None:
            try:
                emp_list = list(db.employees.find({}))
                employees = {str(e.get("_id")): e for e in emp_list}
            except Exception:
                employees = {}
        elif employees is None:
            employees = {}

        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_backup (
                id TEXT PRIMARY KEY,
                employee_id TEXT,
                employee_name TEXT,
                employee_no TEXT,
                job_title TEXT,
                work_date TEXT,
                clock_in_at TEXT,
                clock_out_at TEXT,
                status TEXT,
                day_type TEXT,
                source TEXT
            )
        """)
        cursor.execute("PRAGMA table_info(attendance_backup)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        expected_cols = {
            "employee_name": "TEXT",
            "employee_no": "TEXT",
            "job_title": "TEXT",
            "day_type": "TEXT",
            "source": "TEXT"
        }
        for col_name, col_type in expected_cols.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE attendance_backup ADD COLUMN {col_name} {col_type}")

        inserted_count = 0
        for event in records:
            eid = str(event.get("employee_id", ""))
            emp = employees.get(eid)
            emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip() if emp else ""
            emp_no = str(emp.get("employee_no", "")) if emp else ""
            job_title = emp.get("job_title", "") if emp else ""

            cursor.execute("""
                INSERT OR REPLACE INTO attendance_backup (
                    id, employee_id, employee_name, employee_no, job_title,
                    work_date, clock_in_at, clock_out_at, status, day_type, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(event.get("_id", "")),
                eid or "UNKNOWN",
                emp_name,
                emp_no,
                job_title,
                event.get("work_date", ""),
                str(event.get("clock_in_at", "")),
                str(event.get("clock_out_at", "")),
                event.get("status", "present"),
                event.get("day_type", "working"),
                event.get("source", "scanner")
            ))
            if cursor.rowcount > 0:
                inserted_count += 1

        conn.commit()
        conn.close()

        return db_filename, inserted_count


if __name__ == "__main__":
    backup = BackupService()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] Running backup...")
    file_path, count = backup.backup_daily_attendance()
    print(f"[{now_str}] Backed up {count} records to {file_path}")
