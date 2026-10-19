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


class ApiClient:
    def __init__(self):
        self.token = None
        self.user = None
        self.url = os.getenv("ATTENDANCE_API_URL", "")
        if not self.url and config_path().exists():
            try:
                self.url = json.loads(config_path().read_text(encoding="utf-8")).get("api_url", "")
            except (OSError, ValueError):
                self.url = ""

    def configure(self, url):
        url = url.strip().rstrip("/")
        parsed = urlparse(url)
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Enter a valid server URL without credentials.")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1")):
            raise ValueError("Use HTTPS for the central server (HTTP is allowed only on this PC for testing).")
        self.url = url
        config_path().parent.mkdir(parents=True, exist_ok=True)
        config_path().write_text(json.dumps({"api_url": url}), encoding="utf-8")

    def call(self, path, body=None):
        if not self.url:
            raise ValueError("Enter the central server address first.")
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            response = requests.post(self.url + path, json=json.loads(json_util.dumps(body or {})),
                                     headers=headers, timeout=(5, 30), allow_redirects=False)
        except requests.RequestException:
            raise ValueError("Cannot reach the central server. Check your connection and retry; no success was confirmed.") from None
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
        return self.user

    def logout(self):
        try:
            if self.token:
                self.call("/logout")
        finally:
            self.token = self.user = None


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
