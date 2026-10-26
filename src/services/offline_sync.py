import os
import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

log = logging.getLogger(__name__)
LAGOS = timezone(timedelta(hours=1))


def get_db_path() -> str:
    base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    data_dir = Path(base) / "RandaframesAttendance"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "offline_store.db")


class OfflineSyncManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_employees (
                    id TEXT PRIMARY KEY,
                    office_id TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    full_name TEXT,
                    employee_no TEXT,
                    job_title TEXT,
                    fingerprint_samples TEXT,
                    photo_bytes BLOB,
                    status TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT,
                    employee_name TEXT,
                    employee_no TEXT,
                    job_title TEXT,
                    office_id TEXT,
                    action TEXT,
                    recorded_at TEXT,
                    work_date TEXT,
                    synced INTEGER DEFAULT 0,
                    synced_at TEXT
                )
            """)
            conn.commit()

    def save_cached_employees(self, employees: list[dict]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()
            for emp in employees:
                emp_id = str(emp.get("_id"))
                samples = emp.get("fingerprint_samples") or []
                samples_json = json.dumps(samples) if samples else ""
                full_name = emp.get("full_name") or f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
                cursor.execute("""
                    INSERT OR REPLACE INTO cached_employees (
                        id, office_id, first_name, last_name, full_name, employee_no,
                        job_title, fingerprint_samples, photo_bytes, status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emp_id,
                    emp.get("office_id", ""),
                    emp.get("first_name", ""),
                    emp.get("last_name", ""),
                    full_name,
                    emp.get("employee_no", ""),
                    emp.get("job_title", ""),
                    samples_json,
                    emp.get("photo_bytes"),
                    emp.get("status", "active"),
                    now_iso
                ))
            conn.commit()

    def get_cached_employees(self, office_id: str = None) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if office_id:
                cursor.execute("SELECT * FROM cached_employees WHERE office_id = ? AND status = 'active'", (office_id,))
            else:
                cursor.execute("SELECT * FROM cached_employees WHERE status = 'active'")
            rows = cursor.fetchall()
            employees = []
            for r in rows:
                samples = json.loads(r["fingerprint_samples"]) if r["fingerprint_samples"] else []
                employees.append({
                    "_id": r["id"],
                    "office_id": r["office_id"],
                    "first_name": r["first_name"],
                    "last_name": r["last_name"],
                    "full_name": r["full_name"],
                    "employee_no": r["employee_no"],
                    "job_title": r["job_title"],
                    "fingerprint_samples": samples,
                    "photo_bytes": r["photo_bytes"],
                    "status": r["status"]
                })
            return employees

    def match_offline_fingerprint(self, sample, office_id: str = None):
        import numpy as np
        from src.services.fingerprint import FingerprintMatcher

        probe = np.asarray(sample, dtype=np.uint8)
        matcher = FingerprintMatcher()
        cached = self.get_cached_employees(office_id)
        if not cached:
            return None, 0

        scores = []
        for emp in cached:
            samples = emp.get("fingerprint_samples") or []
            if not samples:
                continue
            cand_arrays = [np.asarray(s, dtype=np.uint8) for s in samples]
            score = max((matcher.get_match_score(probe, cand) for cand in cand_arrays), default=0)
            scores.append((score, emp))

        scores.sort(key=lambda pair: pair[0], reverse=True)
        if scores and scores[0][0] >= 18:
            return scores[0][1], scores[0][0]
        return None, (scores[0][0] if scores else 0)

    def record_offline_attendance(self, employee: dict, action: str) -> dict:
        now_utc = datetime.now(timezone.utc)
        work_date = now_utc.astimezone(LAGOS).strftime("%Y-%m-%d")
        now_iso = now_utc.isoformat()
        emp_id = str(employee.get("_id"))
        emp_name = employee.get("full_name") or f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM offline_records
                WHERE employee_id = ? AND work_date = ? AND action = ?
            """, (emp_id, work_date, action))
            existing = cursor.fetchone()
            if existing:
                msg = f"Already Timed {action.capitalize()} (Recorded Offline)"
                return {
                    "action": msg,
                    "offline": True,
                    "employee": employee,
                    "already_recorded": True
                }

            cursor.execute("""
                INSERT INTO offline_records (
                    employee_id, employee_name, employee_no, job_title,
                    office_id, action, recorded_at, work_date, synced
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                emp_id,
                emp_name,
                employee.get("employee_no", ""),
                employee.get("job_title", ""),
                employee.get("office_id", ""),
                action,
                now_iso,
                work_date
            ))
            conn.commit()

        action_msg = f"Time {action.capitalize()} Recorded (Offline)"
        return {
            "action": action_msg,
            "offline": True,
            "employee": employee,
            "already_recorded": False
        }

    def get_pending_records(self) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM offline_records WHERE synced = 0 ORDER BY id ASC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_pending_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM offline_records WHERE synced = 0")
            return cursor.fetchone()[0]

    def mark_records_synced(self, record_ids: list[int]):
        if not record_ids:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()
            placeholders = ",".join("?" for _ in record_ids)
            cursor.execute(f"""
                UPDATE offline_records
                SET synced = 1, synced_at = ?
                WHERE id IN ({placeholders})
            """, [now_iso] + record_ids)
            conn.commit()

    def sync_templates_from_server(self, api_client) -> int:
        try:
            res = api_client.call("/sync/kiosk-cache")
            employees = res.get("employees", [])
            if employees:
                self.save_cached_employees(employees)
            return len(employees)
        except Exception as exc:
            log.warning("Could not sync templates from server: %s", exc)
            return 0

    def push_offline_records_to_server(self, api_client) -> int:
        pending = self.get_pending_records()
        if not pending:
            return 0

        payload = {
            "records": [
                {
                    "offline_id": r["id"],
                    "employee_id": r["employee_id"],
                    "action": r["action"],
                    "recorded_at": r["recorded_at"],
                    "work_date": r["work_date"],
                    "office_id": r["office_id"]
                }
                for r in pending
            ]
        }

        try:
            res = api_client.call("/sync/offline-records", payload)
            synced_ids = res.get("synced_ids", [])
            if synced_ids:
                self.mark_records_synced(synced_ids)
                log.info("Pushed and confirmed %d offline records to central server", len(synced_ids))
            return len(synced_ids)
        except Exception as exc:
            log.warning("Failed to push offline records to server: %s", exc)
            return 0

    def has_local_time_in_today(self, employee_id: str, work_date: str = None) -> bool:
        if not work_date:
            work_date = datetime.now(timezone.utc).astimezone(LAGOS).strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM offline_records
                WHERE employee_id = ? AND work_date = ? AND action = 'in'
            """, (str(employee_id), work_date))
            return cursor.fetchone() is not None

    def check_server_online(self, api_client, timeout: float = 2.0) -> bool:
        if not getattr(api_client, "url", None):
            return False
        try:
            url = api_client.url.rstrip("/") + "/healthz"
            resp = api_client._session.get(url, timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False


offline_manager = OfflineSyncManager()
