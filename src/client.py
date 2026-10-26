"""Desktop transport. No MongoDB URI or persistent password on office PCs."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
import requests
from bson import json_util


def config_path():
    return Path(os.getenv("LOCALAPPDATA", Path.home())) / "RandaframesAttendance" / "client.json"


DEFAULT_API_URL = "https://randaframes-attendance.onrender.com"


class ApiClient:
    def __init__(self):
        self.token = None
        self.user = None
        self.saved_token = None
        self.saved_user = None
        self._session = requests.Session()
        from requests.adapters import HTTPAdapter
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=1)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        self.url = os.getenv("ATTENDANCE_API_URL", "")
        if not self.url and config_path().exists():
            try:
                data = json.loads(config_path().read_text(encoding="utf-8"))
                self.url = data.get("api_url", "")
                self.saved_token = data.get("saved_token")
                self.saved_user = data.get("saved_user")
            except (OSError, ValueError):
                self.url = ""
                self.saved_token = None
                self.saved_user = None

        if not self.url:
            self.url = DEFAULT_API_URL

    def save_config(self):
        try:
            config_path().parent.mkdir(parents=True, exist_ok=True)
            payload = {"api_url": self.url}
            if self.saved_token and self.saved_user:
                payload["saved_token"] = self.saved_token
                payload["saved_user"] = self.saved_user
            config_path().write_text(json.dumps(payload), encoding="utf-8")
        except Exception:
            pass

    def restore_saved_session(self):
        if self.saved_token and self.saved_user:
            self.token = self.saved_token
            self.user = self.saved_user
            return True
        return False

    def configure(self, url):
        url = url.strip().rstrip("/")
        parsed = urlparse(url)
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Enter a valid server URL without credentials.")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1")):
            raise ValueError("Use HTTPS for the central server (HTTP is allowed only on this PC for testing).")
        self.url = url
        self.save_config()

    def call(self, path, body=None):
        if not self.url:
            raise ValueError("Enter the central server address first.")
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        headers["Content-Type"] = "application/json"
        payload_bytes = json_util.dumps(body or {}).encode("utf-8")
        try:
            response = self._session.post(self.url + path, data=payload_bytes,
                                          headers=headers, timeout=(15, 60), allow_redirects=False)
        except requests.exceptions.ConnectTimeout:
            raise ValueError("Cannot reach the central server (connection timed out). Check your internet connection and retry.") from None
        except requests.exceptions.ReadTimeout:
            raise ValueError("The central server took too long to respond (read timeout). Please retry.") from None
        except requests.RequestException as exc:
            raise ValueError(f"Cannot reach the central server ({type(exc).__name__}). Check your connection and retry.") from None
        if not 200 <= response.status_code < 300:
            try:
                message = response.json().get("detail", "Request failed.")
            except ValueError:
                message = "The server returned an unexpected response."
            if response.status_code == 401:
                self.token = None
            raise ValueError(message if isinstance(message, str) else "Invalid request. Check the entered values.")
        return json_util.loads(response.text)

    def login(self, username, password):
        result = self.call("/login", {"username": username, "password": password})
        self.token, self.user = result["token"], result["user"]
        if self.user.get("role") == "office_admin":
            self.saved_token = self.token
            self.saved_user = self.user
            self.save_config()
        return self.user

    def logout(self):
        try:
            if self.token:
                self.call("/logout")
        finally:
            self.token = self.user = None
            self.saved_token = self.saved_user = None
            self.save_config()

    def delete_attendance(self, record_id=None, employee_id=None, work_date=None, before_date=None, from_date=None, to_date=None, office_id=None, delete_all=False):
        payload = {
            "record_id": record_id,
            "employee_id": employee_id,
            "work_date": work_date,
            "before_date": before_date,
            "from_date": from_date,
            "to_date": to_date,
            "office_id": office_id,
            "delete_all": delete_all
        }
        return self.call("/attendance/delete", payload)

    def manual_attendance_record(self, employee_id, action, work_date=None, time_str=None, reason=None):
        payload = {
            "employee_id": employee_id,
            "action": action,
            "work_date": work_date,
            "time_str": time_str,
            "reason": reason
        }
        return self.call("/attendance/manual-record", payload)

    def get_digest_settings(self):
        return self.call("/digest/settings")

    def save_digest_settings(self, executive_emails=None, office_emails=None, office_email=None, send_hour=None, is_enabled=None):
        payload = {
            "executive_emails": executive_emails,
            "office_emails": office_emails,
            "office_email": office_email,
            "send_hour": send_hour,
            "is_enabled": is_enabled
        }
        return self.call("/digest/settings", payload)

    def send_digest_now(self, test_email=None, target_date=None):
        payload = {
            "test_email": test_email,
            "target_date": target_date
        }
        return self.call("/digest/send-now", payload)



api = ApiClient()


class Cursor(list):
    def sort(self, key, direction=1):
        return Cursor(sorted(self, key=lambda row: row.get(key) or "", reverse=direction < 0))


class Collection:
    def __init__(self, name):
        self.name = name

    def find(self, query=None):
        if not api.token:
            return Cursor()
        return Cursor(api.call("/read", {"collection": self.name, "query": query or {}}))

    def find_one(self, query):
        rows = self.find(query)
        return rows[0] if rows else None

    def count_documents(self, query):
        return len(self.find(query))

    def distinct(self, key, query):
        return list({row[key] for row in self.find(query) if key in row})

    def insert_one(self, document):
        return SimpleNamespace(**api.call("/save", {"collection": self.name, "document": document}))

    def update_one(self, query, update):
        if set(query) != {"_id"} or set(update) != {"$set"}:
            raise ValueError("Unsupported update.")
        return SimpleNamespace(**api.call("/save", {"collection": self.name,
            "id": str(query["_id"]), "document": update["$set"]}))


class ClientDatabase:
    @classmethod
    def get_db(cls):
        return SimpleNamespace(**{name: Collection(name) for name in
            ("employees", "attendance_records", "departments", "offices")})
