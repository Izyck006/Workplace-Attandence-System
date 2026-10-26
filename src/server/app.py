"""Office authorization is enforced here, independent of desktop filters."""
from datetime import datetime, timedelta, timezone
import html
import json
import logging
import os
import re
import secrets

from bson import ObjectId, json_util
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError, PyMongoError

from src.data.database import DatabaseManager
from src.offices import OFFICE_MAP
from src.server.security import login, token_hash, validate_password, ph, generate_password
from src.server.rate_limiter import rate_limiter
from src.server.webhooks import verify_paystack_signature, verify_stripe_signature

app = FastAPI(title="Randaframes Central Attendance", docs_url=None, redoc_url=None)
bearer = HTTPBearer()
log = logging.getLogger(__name__)
LAGOS = timezone(timedelta(hours=1))

CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SCRIPT_RE = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def sanitize_string(value: str, max_length: int = 200) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = CONTROL_CHAR_RE.sub("", value).strip()
    cleaned = SCRIPT_RE.sub("", cleaned)
    cleaned = TAG_RE.sub("", cleaned)
    cleaned = html.escape(cleaned)
    return cleaned[:max_length]


def validate_photo_bytes(data_bytes: bytes):
    if not isinstance(data_bytes, bytes):
        raise HTTPException(400, "Photo must be binary bytes.")
    if len(data_bytes) > 2_000_000:
        raise HTTPException(400, "Photo must be at most 2 MB.")
    is_jpeg = data_bytes.startswith(b"\xff\xd8\xff")
    is_png = data_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = data_bytes.startswith(b"RIFF") and len(data_bytes) >= 12 and data_bytes[8:12] == b"WEBP"
    if not (is_jpeg or is_png or is_webp):
        raise HTTPException(400, "Invalid image format. Only JPEG, PNG, or WEBP photos are allowed.")


def get_db():
    return DatabaseManager.get_db()


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    path = request.url.path

    if not os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("TESTING") and path not in ("/health", "/healthz"):
        client_ip = rate_limiter.get_client_ip(request)
        if path == "/login":
            allowed, retry = rate_limiter.check(f"login:{client_ip}", max_requests=15, window_seconds=60)
        elif path == "/password" or path.startswith("/offices/") or path == "/attendance/delete":
            allowed, retry = rate_limiter.check(f"pw:{client_ip}", max_requests=20, window_seconds=60)
        elif path == "/scan":
            allowed, retry = rate_limiter.check(f"scan:{client_ip}", max_requests=60, window_seconds=60)
        else:
            allowed, retry = rate_limiter.check(f"gen:{client_ip}", max_requests=120, window_seconds=60)

        if not allowed:
            return JSONResponse(
                {"detail": "Rate limit exceeded. Please wait before retrying."},
                status_code=429,
                headers={"Retry-After": str(retry)}
            )

    size = 0
    chunks = []
    async for chunk in request.stream():
        size += len(chunk)
        if size > 6_000_000:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
        chunks.append(chunk)
    request._body = b"".join(chunks)

    response = await call_next(request)

    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.get("/healthz")
@app.get("/health")
def health_check():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.exception_handler(PyMongoError)
async def database_error(request, exc):
    log.error("Database operation failed: %s", type(exc).__name__)
    return JSONResponse({"detail": "Database unavailable. No success was confirmed; reconnect and retry."}, status_code=503)


def is_valid_office(office_id: str, db=None) -> bool:
    if not office_id or not isinstance(office_id, str):
        return False
    if office_id in OFFICE_MAP:
        return True
    if db is not None:
        doc = db.offices.find_one({"_id": office_id})
        if doc:
            OFFICE_MAP[office_id] = doc
            return True
    return False


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db=Depends(get_db)):
    session = db.sessions.find_one({"_id": token_hash(credentials.credentials),
                                    "expires_at": {"$gt": datetime.utcnow()}})
    if not session:
        raise HTTPException(401, "Session expired. Please log in again.")
    user = db.users.find_one({"_id": session["user_id"], "is_active": True})
    if not user or user.get("role") not in ("main_admin", "office_admin"):
        raise HTTPException(401, "Account unavailable.")
    if user["role"] == "office_admin" and not is_valid_office(user.get("office_id"), db):
        raise HTTPException(403, "Invalid office assignment.")
    user["session_id"] = session["_id"]
    user["kiosk"] = session.get("kiosk", False)
    if not user["kiosk"]:
        db.sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"expires_at": datetime.utcnow() + timedelta(minutes=10)}}
        )
    return user


def ready_user(user=Depends(current_user)):
    if user.get("must_change_password"):
        raise HTTPException(403, "Change the temporary password before continuing.")
    return user


def admin(user=Depends(ready_user)):
    if user["kiosk"]:
        raise HTTPException(403, "Log in to manage employees or view reports.")
    return user


def master(user=Depends(admin)):
    if user["role"] != "main_admin":
        raise HTTPException(403, "Master admin access required.")
    return user


def scope(user, query=None):
    query = query or {}
    if user["role"] == "main_admin":
        return query
    return {"$and": [{"office_id": user["office_id"]}, query]}


def encode(value):
    return json.loads(json_util.dumps(value))


def decode(value):
    return json_util.loads(json.dumps(value))


def audit(db, user, action, target):
    db.audit_events.insert_one({"actor_id": user["_id"], "office_id": user.get("office_id"),
        "action": action, "target": str(target), "created_at": datetime.utcnow()})


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


@app.get("/health")
@app.get("/healthz")
def health(db=Depends(get_db)):
    db.command("ping")
    if db.offices.count_documents({"_id": {"$in": list(OFFICE_MAP)}}) != len(OFFICE_MAP):
        raise HTTPException(503, "Database provisioning is required.")
    return {"status": "ok"}


@app.post("/login")
def sign_in(body: LoginBody, db=Depends(get_db)):
    token, user = login(db, body.username.strip(), body.password)
    return encode({"token": token, "user": user})


class PasswordBody(BaseModel):
    password: str = Field(max_length=128)


@app.post("/password")
def change_password(body: PasswordBody, user=Depends(current_user), db=Depends(get_db)):
    if user["kiosk"]:
        raise HTTPException(403, "Log in first.")
    validate_password(body.password)
    if _same_password(user, body.password):
        raise HTTPException(400, "Choose a different password.")
    db.users.update_one({"_id": user["_id"]}, {"$set": {
        "password_hash": ph.hash(body.password), "must_change_password": False}})
    db.sessions.delete_many({"user_id": user["_id"], "_id": {"$ne": user["session_id"]}})
    audit(db, user, "password_changed", user["_id"])
    return {"ok": True}


def _same_password(user, password):
    from argon2.exceptions import VerificationError
    try:
        return ph.verify(user["password_hash"], password)
    except VerificationError:
        return False


@app.post("/logout")
def logout(user=Depends(current_user), db=Depends(get_db)):
    db.sessions.delete_one({"_id": user["session_id"]})
    return {"ok": True}


@app.post("/kiosk")
def kiosk(user=Depends(admin), db=Depends(get_db)):
    if user["role"] != "office_admin":
        raise HTTPException(403, "Use an office login to open that office's scanner terminal.")
    token = secrets.token_urlsafe(32)
    db.sessions.insert_one({"_id": token_hash(token), "user_id": user["_id"], "kiosk": True,
                            "expires_at": datetime.utcnow() + timedelta(hours=24)})
    db.sessions.delete_one({"_id": user["session_id"]})
    return {"token": token}


class ReadBody(BaseModel):
    collection: str
    query: dict = Field(default_factory=dict)


def safe_query(query):
    allowed = {"$and", "$or", "$in", "$nin", "$ne", "$gte", "$lte", "$gt", "$lt", "$exists", "$eq"}
    if isinstance(query, dict):
        for key, value in query.items():
            if not isinstance(key, str) or "\x00" in key:
                raise HTTPException(400, "Invalid query key.")
            if key.startswith("$") and key not in allowed:
                raise HTTPException(400, "Unsupported query.")
            if "." in key:
                raise HTTPException(400, "Nested key traversal not permitted.")
            safe_query(value)
    elif isinstance(query, list):
        for value in query:
            safe_query(value)


@app.post("/read")
def read(body: ReadBody, user=Depends(admin), db=Depends(get_db)):
    if body.collection not in ("employees", "attendance_records", "departments", "offices"):
        raise HTTPException(403, "Collection unavailable.")
    query = decode(body.query)
    safe_query(query)
    if user["role"] == "office_admin" and isinstance(query, dict) and "office_id" in query:
        del query["office_id"]
    if body.collection in ("employees", "attendance_records"):
        query = scope(user, query)
    elif body.collection == "offices" and user["role"] != "main_admin":
        query = {"$and": [query, {"_id": user["office_id"]}]}
    projection = {"fingerprint_descriptors": 0, "fingerprint_samples": 0}
    records = list(db[body.collection].find(query, projection).limit(50001))
    if len(records) > 50000:
        raise HTTPException(400, "Select a shorter report date range (maximum 50,000 rows).")
    return encode(records)


class WriteBody(BaseModel):
    collection: str
    document: dict
    id: str | None = None


def object_id(value):
    if not ObjectId.is_valid(value):
        raise HTTPException(400, "Invalid record ID.")
    return ObjectId(value)


@app.post("/save")
def save(body: WriteBody, user=Depends(admin), db=Depends(get_db)):
    data = decode(body.document)
    now = datetime.utcnow()
    if body.collection == "departments" and body.id is None:
        name = sanitize_string(data.get("name", ""), 100)
        if not name:
            raise HTTPException(400, "Department name required (maximum 100 characters).")
        db.departments.update_one({"name": name}, {"$setOnInsert": {
            "name": name, "is_active": True, "created_at": now}}, upsert=True)
        return encode({"inserted_id": db.departments.find_one({"name": name})["_id"]})
    if body.collection != "employees":
        raise HTTPException(403, "Operation unavailable.")
    allowed = {"first_name", "last_name", "full_name", "employee_id", "employee_no", "job_title",
               "department_id", "status", "photo_bytes", "office_id", "updated_at", "created_at", "has_fingerprint"}
    if set(data) - allowed:
        raise HTTPException(400, "Unsupported employee field.")
    existing = None
    if body.id:
        existing = db.employees.find_one(scope(user, {"_id": object_id(body.id)}))
        if not existing:
            raise HTTPException(404, "Employee not found.")
    office = user.get("office_id") if user["role"] == "office_admin" else data.get("office_id", (existing or {}).get("office_id"))
    if not is_valid_office(office, db) or (data.get("office_id") and data["office_id"] != office):
        raise HTTPException(403, "Invalid office for this account.")
    if existing and office != existing.get("office_id"):
        raise HTTPException(400, "Office transfers require a reviewed migration; historical records must be preserved.")
    for field in ("first_name", "last_name", "employee_no", "job_title"):
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_string(data[field], 200)
        value = data.get(field, (existing or {}).get(field, ""))
        if not isinstance(value, str) or len(value) > 200:
            raise HTTPException(400, f"Invalid {field}.")
    if not data.get("employee_no", (existing or {}).get("employee_no")):
        raise HTTPException(400, "Employee number required.")
    if data.get("status", "active") not in ("active", "inactive"):
        raise HTTPException(400, "Invalid employee status.")
    if "photo_bytes" in data and data["photo_bytes"] is not None:
        validate_photo_bytes(data["photo_bytes"])
    data.update(office_id=office, updated_at=now)
    data.pop("created_at", None)
    data.pop("has_fingerprint", None)
    try:
        if existing:
            db.employees.update_one(scope(user, {"_id": existing["_id"]}), {"$set": data})
            target = existing["_id"]
        else:
            data.update(created_at=now, has_fingerprint=False)
            target = db.employees.insert_one(data).inserted_id
    except DuplicateKeyError:
        raise HTTPException(409, "That employee number is already in use.")
    audit(db, user, "employee_saved", target)
    return encode({"inserted_id": target, "matched_count": 1})


class SamplesBody(BaseModel):
    samples: list = Field(min_length=1, max_length=3)


def descriptor_arrays(samples):
    import numpy as np
    arrays = []
    for sample in samples:
        arr = np.asarray(sample)
        if arr.ndim != 2 or not (10 <= arr.shape[0] <= 2000) or arr.shape[1] != 32:
            raise HTTPException(400, "Poor or invalid fingerprint sample. Scan again.")
        if arr.dtype.kind not in "iu" or (arr < 0).any() or (arr > 255).any():
            raise HTTPException(400, "Invalid fingerprint data.")
        arrays.append(arr.astype(np.uint8))
    return arrays


@app.post("/employees/{employee_id}/fingerprint")
def enroll(employee_id: str, body: SamplesBody, user=Depends(admin), db=Depends(get_db)):
    descriptor_arrays(body.samples)
    query = scope(user, {"_id": object_id(employee_id), "status": "active"})
    result = db.employees.update_one(query, {"$set": {"fingerprint_samples": body.samples,
        "has_fingerprint": True, "updated_at": datetime.utcnow()}, "$unset": {"fingerprint_descriptors": ""}})
    if not result.matched_count:
        raise HTTPException(404, "Active employee not found.")
    audit(db, user, "fingerprint_enrolled", employee_id)
    return {"ok": True}


class ScanBody(SamplesBody):
    action: str


def record_attendance(db, employee, action, now=None):
    now = now or datetime.utcnow()
    date = now.replace(tzinfo=timezone.utc).astimezone(LAGOS).strftime("%Y-%m-%d")
    query = {"employee_id": employee["_id"], "office_id": employee["office_id"], "work_date": date}
    if action == "in":
        doc = dict(query, clock_in_at=now, clock_out_at=None, status="present", day_type="working",
                   source="scanner", is_edited=False, created_at=now, updated_at=now)
        try:
            result = db.attendance_records.update_one(query, {"$setOnInsert": doc}, upsert=True)
            return "Time In Recorded" if result.upserted_id else "Already Timed In"
        except DuplicateKeyError:
            return "Already Timed In"
    record = db.attendance_records.find_one(query)
    if not record or not record.get("clock_in_at"):
        raise HTTPException(409, "Must time in first.")
    result = db.attendance_records.update_one(dict(query, clock_out_at=None), {"$set": {
        "clock_out_at": now, "updated_at": now,
        "minutes_worked": max(0, int((now - record["clock_in_at"]).total_seconds() // 60))}})
    return "Time Out Recorded" if result.modified_count else "Already Timed Out"


@app.post("/scan")
def scan(body: ScanBody, user=Depends(ready_user), db=Depends(get_db)):
    if user["role"] != "office_admin" or body.action not in ("in", "out") or len(body.samples) != 1:
        raise HTTPException(403, "An office login and a valid scan action are required.")
    from src.services.fingerprint import FingerprintMatcher
    probe = descriptor_arrays(body.samples)[0]
    matcher = FingerprintMatcher()
    scores = []
    for employee in db.employees.find(scope(user, {"status": "active", "has_fingerprint": True,
                                                  "fingerprint_samples": {"$exists": True}})):
        score = max(matcher.get_match_score(probe, candidate)
                    for candidate in descriptor_arrays(employee["fingerprint_samples"]))
        scores.append((score, employee))
    scores.sort(key=lambda pair: pair[0], reverse=True)
    if not scores or scores[0][0] < 18:
        raise HTTPException(404, "Fingerprint not recognized clearly. Scan again or ask your office admin to enroll you.")
    employee = scores[0][1]
    action = record_attendance(db, employee, body.action)
    audit(db, user, action, employee["_id"])
    return encode({"action": action, "employee": {k: employee.get(k) for k in
                   ("first_name", "last_name", "employee_no", "job_title", "photo_bytes")}})


@app.post("/offices/{office_id}/reset-password")
def reset_password(office_id: str, user=Depends(master), db=Depends(get_db)):
    account = db.users.find_one({"office_id": office_id, "role": "office_admin"})
    if not account:
        raise HTTPException(404, "Office account not found.")
    password = generate_password()
    db.users.update_one({"_id": account["_id"]}, {"$set": {"password_hash": ph.hash(password),
        "must_change_password": True, "failed_attempts": 0, "locked_until": None}})
    db.sessions.delete_many({"user_id": account["_id"]})
    audit(db, user, "office_password_reset", office_id)
    return {"username": account["username"], "password": password}


class CreateOfficeBody(BaseModel):
    name: str
    location: str
    office_id: str | None = None
    username: str | None = None
    password: str | None = None


@app.post("/offices/create")
def create_office(body: CreateOfficeBody, user=Depends(master), db=Depends(get_db)):
    name = sanitize_string(body.name.strip(), 100) if body.name else ""
    location = sanitize_string(body.location.strip(), 100) if body.location else ""
    if not name or not location:
        raise HTTPException(400, "Office name and location are required.")

    if body.office_id and body.office_id.strip():
        raw_id = re.sub(r"[^a-zA-Z0-9_-]", "", body.office_id.strip().lower().replace(" ", "-"))
    else:
        raw_id = re.sub(r"[^a-zA-Z0-9_-]", "", name.lower().replace(" ", "-"))
    office_id = raw_id[:50]
    if not office_id:
        raise HTTPException(400, "Invalid office identifier.")

    if db.offices.find_one({"_id": office_id}) or office_id in OFFICE_MAP:
        raise HTTPException(400, f"Office with ID '{office_id}' already exists.")

    username = (body.username.strip() if body.username else office_id).lower()
    if db.users.find_one({"username": username}):
        raise HTTPException(400, f"Username '{username}' is already taken.")

    password = body.password if (body.password and len(body.password) >= 8) else generate_password()

    office_doc = {"_id": office_id, "name": name, "location": location}
    db.offices.insert_one(office_doc)
    OFFICE_MAP[office_id] = office_doc

    db.users.insert_one({
        "username": username,
        "password_hash": ph.hash(password),
        "role": "office_admin",
        "office_id": office_id,
        "is_active": True,
        "must_change_password": True,
        "failed_attempts": 0,
        "locked_until": None
    })

    audit(db, user, "office_created", office_id)
    return {
        "ok": True,
        "office": office_doc,
        "username": username,
        "password": password
    }


@app.post("/offices/{office_id}/delete")
def delete_office(office_id: str, user=Depends(master), db=Depends(get_db)):
    from src.offices import CORE_OFFICE_IDS, unregister_office
    if office_id in CORE_OFFICE_IDS:
        raise HTTPException(400, "Core default offices are protected and cannot be deleted.")

    check_q = {"_id": office_id}
    if user.get("organization_id"):
        check_q["organization_id"] = user["organization_id"]
    office = db.offices.find_one(check_q)
    if not office:
        raise HTTPException(404, "Office not found.")

    emp_q = {"office_id": office_id, "status": "active"}
    if user.get("organization_id"):
        emp_q["organization_id"] = user["organization_id"]
    active_staff = db.employees.count_documents(emp_q)
    if active_staff > 0:
        raise HTTPException(400, f"Cannot delete office while it has {active_staff} active employee(s). Please reassign or deactivate staff members first.")

    db.offices.delete_one(check_q)
    unregister_office(office_id)

    user_q = {"office_id": office_id, "role": "office_admin"}
    if user.get("organization_id"):
        user_q["organization_id"] = user["organization_id"]
    for admin_user in db.users.find(user_q):
        db.sessions.delete_many({"user_id": admin_user["_id"]})
    db.users.delete_many(user_q)

    audit(db, user, "office_deleted", office_id)
    return {
        "ok": True,
        "office_id": office_id,
        "message": f"Office '{office.get('name', office_id)}' deleted successfully."
    }


class DeleteAttendanceBody(BaseModel):
    record_id: str | None = None
    employee_id: str | None = None
    work_date: str | None = None
    before_date: str | None = None
    from_date: str | None = None
    to_date: str | None = None
    office_id: str | None = None
    delete_all: bool = False


@app.post("/attendance/delete")
def delete_attendance(body: DeleteAttendanceBody, user=Depends(admin), db=Depends(get_db)):
    is_office_admin = user["role"] == "office_admin"

    query = {}
    if is_office_admin:
        query["office_id"] = user["office_id"]
        if body.delete_all:
            raise HTTPException(403, "Office admins cannot perform all-time company-wide deletions.")
        if body.before_date:
            raise HTTPException(403, "Office admins cannot purge historical records across all time.")

        if body.record_id:
            if ObjectId.is_valid(body.record_id):
                query["_id"] = {"$in": [ObjectId(body.record_id), str(body.record_id)]}
            else:
                query["_id"] = body.record_id
        elif body.employee_id and body.work_date:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", body.work_date):
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")
            emp = db.employees.find_one({"_id": object_id(body.employee_id), "office_id": user["office_id"]})
            if not emp:
                raise HTTPException(404, "Employee not found in your assigned office.")
            query["employee_id"] = emp["_id"]
            query["work_date"] = body.work_date
        elif body.work_date:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", body.work_date):
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")
            query["work_date"] = body.work_date
        elif body.from_date and body.to_date:
            if not (re.match(r"^\d{4}-\d{2}-\d{2}$", body.from_date) and re.match(r"^\d{4}-\d{2}-\d{2}$", body.to_date)):
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")
            query["work_date"] = {"$gte": body.from_date, "$lte": body.to_date}
        else:
            raise HTTPException(400, "Specify a record ID, staff log date, or particular date to delete.")

    else:
        if body.record_id:
            if ObjectId.is_valid(body.record_id):
                query["_id"] = {"$in": [ObjectId(body.record_id), str(body.record_id)]}
            else:
                query["_id"] = body.record_id
        elif body.employee_id and body.work_date:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", body.work_date):
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")
            if ObjectId.is_valid(body.employee_id):
                query["employee_id"] = {"$in": [ObjectId(body.employee_id), str(body.employee_id)]}
            else:
                query["employee_id"] = body.employee_id
            query["work_date"] = body.work_date
        elif body.delete_all:
            query = {}
        elif body.before_date:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", body.before_date):
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")
            query["work_date"] = {"$lte": body.before_date}
        elif body.from_date and body.to_date:
            if not (re.match(r"^\d{4}-\d{2}-\d{2}$", body.from_date) and re.match(r"^\d{4}-\d{2}-\d{2}$", body.to_date)):
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")
            query["work_date"] = {"$gte": body.from_date, "$lte": body.to_date}
        elif body.work_date:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", body.work_date):
                raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")
            query["work_date"] = body.work_date
        else:
            raise HTTPException(400, "Specify a record ID, staff log date, date range, or delete_all flag.")

        if body.office_id:
            if not is_valid_office(body.office_id, db):
                raise HTTPException(400, "Invalid office ID.")
            query["office_id"] = body.office_id

    result = db.attendance_records.delete_many(query)
    audit(db, user, "attendance_deleted", f"deleted_{result.deleted_count}_records")
    return {"ok": True, "deleted_count": result.deleted_count}



@app.post("/webhooks/paystack")
async def paystack_webhook(request: Request):
    secret_key = os.getenv("PAYSTACK_SECRET_KEY", "")
    sig = request.headers.get("x-paystack-signature")
    body = await request.body()
    if not verify_paystack_signature(body, sig, secret_key):
        raise HTTPException(400, "Invalid Paystack signature.")
    event = json.loads(body.decode("utf-8"))
    log.info("Verified Paystack webhook event: %s", event.get("event"))
    return {"status": "success"}


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    secret_key = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    sig = request.headers.get("stripe-signature")
    body = await request.body()
    if not verify_stripe_signature(body, sig, secret_key):
        raise HTTPException(400, "Invalid Stripe signature.")
    event = json.loads(body.decode("utf-8"))
    log.info("Verified Stripe webhook event: %s", event.get("type"))
    return {"status": "success"}



@app.get("/sync/kiosk-cache")
@app.post("/sync/kiosk-cache")
def sync_kiosk_cache(user=Depends(ready_user), db=Depends(get_db)):
    """Return active employee templates for local SQLite kiosk caching and offline verification."""
    query = scope(user, {"status": "active", "has_fingerprint": True, "fingerprint_samples": {"$exists": True}})
    projection = {
        "_id": 1,
        "office_id": 1,
        "first_name": 1,
        "last_name": 1,
        "full_name": 1,
        "employee_no": 1,
        "job_title": 1,
        "photo_bytes": 1,
        "fingerprint_samples": 1,
        "status": 1,
        "updated_at": 1,
    }
    employees = list(db.employees.find(query, projection))
    return {"employees": encode(employees), "count": len(employees)}


class OfflineRecordItem(BaseModel):
    offline_id: int | str
    employee_id: str
    action: str
    recorded_at: str
    work_date: str | None = None
    office_id: str | None = None


class OfflineSyncBody(BaseModel):
    records: list[OfflineRecordItem] = Field(max_length=500)


@app.post("/sync/offline-records")
def sync_offline_records(body: OfflineSyncBody, user=Depends(ready_user), db=Depends(get_db)):
    """Ingest attendance scans recorded offline while local internet was disconnected."""
    synced_ids = []
    for item in body.records:
        if item.action not in ("in", "out"):
            continue
        emp_query = scope(user, {"_id": object_id(item.employee_id), "status": "active"})
        emp = db.employees.find_one(emp_query)
        if not emp:
            continue

        try:
            recorded_dt = datetime.fromisoformat(item.recorded_at.replace("Z", "+00:00"))
            if recorded_dt.tzinfo is None:
                recorded_dt = recorded_dt.replace(tzinfo=timezone.utc)
            recorded_dt = recorded_dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            recorded_dt = datetime.utcnow()

        work_date = item.work_date
        if not work_date:
            work_date = recorded_dt.replace(tzinfo=timezone.utc).astimezone(LAGOS).strftime("%Y-%m-%d")

        query = {"employee_id": emp["_id"], "office_id": emp["office_id"], "work_date": work_date}
        if item.action == "in":
            rec = db.attendance_records.find_one(query)
            if not rec:
                doc = dict(query, clock_in_at=recorded_dt, clock_out_at=None, status="present", day_type="working",
                           source="scanner", offline_synced=True, is_edited=False, created_at=recorded_dt, updated_at=datetime.utcnow())
                try:
                    db.attendance_records.insert_one(doc)
                except DuplicateKeyError:
                    pass
            elif not rec.get("clock_in_at"):
                db.attendance_records.update_one(query, {"$set": {
                    "clock_in_at": recorded_dt, "status": "present", "source": "scanner",
                    "offline_synced": True, "updated_at": datetime.utcnow()
                }})
        else:
            rec = db.attendance_records.find_one(query)
            if rec and rec.get("clock_in_at"):
                mins = max(0, int((recorded_dt - rec["clock_in_at"]).total_seconds() // 60))
                db.attendance_records.update_one(query, {"$set": {
                    "clock_out_at": recorded_dt, "minutes_worked": mins, "offline_synced": True, "updated_at": datetime.utcnow()}})
            else:
                doc = dict(query, clock_in_at=recorded_dt, clock_out_at=recorded_dt, minutes_worked=0,
                           status="present", day_type="working", source="scanner", offline_synced=True,
                           is_edited=False, created_at=recorded_dt, updated_at=datetime.utcnow())
                try:
                    db.attendance_records.insert_one(doc)
                except DuplicateKeyError:
                    pass

        synced_ids.append(item.offline_id)

    audit(db, user, "offline_records_synced", f"synced_{len(synced_ids)}_records")
    return {"ok": True, "synced_ids": synced_ids, "synced_count": len(synced_ids)}



class ManualAttendanceBody(BaseModel):
    employee_id: str
    action: str
    work_date: str | None = None
    time_str: str | None = None
    reason: str | None = None


@app.post("/attendance/manual-record")
def manual_attendance_record(body: ManualAttendanceBody, user=Depends(admin), db=Depends(get_db)):
    """Allow office or master admin to manually record clock-in/out for injured/unreadable finger or emergency."""
    if body.action not in ("in", "out"):
        raise HTTPException(400, "Action must be either 'in' or 'out'.")

    emp = db.employees.find_one(scope(user, {"_id": object_id(body.employee_id), "status": "active"}))
    if not emp:
        raise HTTPException(404, "Active employee not found in your assigned office.")

    now_lagos = datetime.now(timezone.utc).astimezone(LAGOS)
    work_date = body.work_date.strip() if body.work_date else now_lagos.strftime("%Y-%m-%d")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", work_date):
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")

    time_str = body.time_str.strip() if body.time_str else now_lagos.strftime("%H:%M")
    if not re.match(r"^\d{2}:\d{2}$", time_str):
        raise HTTPException(400, "Invalid time format. Use HH:MM.")

    try:
        hour, minute = map(int, time_str.split(":"))
        year, month, day = map(int, work_date.split("-"))
        target_lagos = datetime(year, month, day, hour, minute, tzinfo=LAGOS)
        target_utc = target_lagos.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        raise HTTPException(400, "Invalid date or time value.")

    reason = sanitize_string(body.reason or "Supervisor manual check-in", 200)
    admin_name = user.get("username", "admin")
    query = {"employee_id": emp["_id"], "office_id": emp["office_id"], "work_date": work_date}

    if body.action == "in":
        doc = dict(query, clock_in_at=target_utc, clock_out_at=None, status="present", day_type="working",
                   source="manual", supervisor_override=True, recorded_by=admin_name, reason=reason,
                   is_edited=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        res = db.attendance_records.update_one(query, {"$setOnInsert": doc}, upsert=True)
        if not res.upserted_id:
            db.attendance_records.update_one(query, {"$set": {
                "clock_in_at": target_utc, "source": "manual", "supervisor_override": True,
                "recorded_by": admin_name, "reason": reason, "updated_at": datetime.utcnow()
            }})
        msg = f"Time In recorded for {emp.get('full_name', emp.get('employee_no'))} at {time_str}."
    else:
        rec = db.attendance_records.find_one(query)
        clock_in_at = (rec or {}).get("clock_in_at") or target_utc
        mins = max(0, int((target_utc - clock_in_at).total_seconds() // 60))
        if rec:
            db.attendance_records.update_one(query, {"$set": {
                "clock_out_at": target_utc, "minutes_worked": mins,
                "source": "manual", "supervisor_override": True, "recorded_by": admin_name,
                "reason": reason, "updated_at": datetime.utcnow()
            }})
        else:
            doc = dict(query, clock_in_at=target_utc, clock_out_at=target_utc, minutes_worked=0,
                       status="present", day_type="working", source="manual", supervisor_override=True,
                       recorded_by=admin_name, reason=reason, is_edited=False,
                       created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            db.attendance_records.update_one(query, {"$setOnInsert": doc}, upsert=True)
        msg = f"Time Out recorded for {emp.get('full_name', emp.get('employee_no'))} at {time_str}."

    audit(db, user, f"supervisor_manual_clock_{body.action}", emp["_id"])
    return {"ok": True, "message": msg, "work_date": work_date, "time": time_str}



class DigestSettingsBody(BaseModel):
    executive_emails: list[str] | None = None
    office_emails: dict[str, str] | None = None
    office_email: str | None = None
    send_hour: int | None = Field(default=None, ge=5, le=22)
    is_enabled: bool | None = None


@app.get("/digest/settings")
def get_digest_settings(user=Depends(admin), db=Depends(get_db)):
    """Retrieve configured recipient email addresses for the morning attendance digest."""
    from src.services.email_service import is_smtp_configured
    settings = db.settings.find_one({"_id": "digest_settings"}) or {}
    exec_emails = settings.get("executive_emails", [])
    office_emails = settings.get("office_emails", {})

    if user["role"] == "office_admin":
        return {
            "office_id": user["office_id"],
            "office_email": office_emails.get(user["office_id"], ""),
            "smtp_configured": is_smtp_configured(),
        }

    return {
        "executive_emails": exec_emails,
        "office_emails": office_emails,
        "send_hour": settings.get("send_hour", 9),
        "is_enabled": settings.get("is_enabled", True),
        "smtp_configured": is_smtp_configured(),
    }


@app.post("/digest/settings")
def save_digest_settings(body: DigestSettingsBody, user=Depends(admin), db=Depends(get_db)):
    """Save or update recipient email addresses for morning attendance digests."""
    from src.services.email_service import validate_email_address

    settings = db.settings.find_one({"_id": "digest_settings"}) or {
        "_id": "digest_settings",
        "executive_emails": [],
        "office_emails": {},
        "send_hour": 9,
        "is_enabled": True
    }

    if user["role"] == "office_admin":
        off_id = user["office_id"]
        email = (body.office_email or "").strip()
        if email and not validate_email_address(email):
            raise HTTPException(400, "Invalid email address format.")
        office_emails = settings.get("office_emails", {})
        if email:
            office_emails[off_id] = email
        else:
            office_emails.pop(off_id, None)
        db.settings.update_one(
            {"_id": "digest_settings"},
            {"$set": {"office_emails": office_emails, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        audit(db, user, "digest_settings_updated", off_id)
        return {"ok": True, "message": "Branch notification email updated."}

    update_data = {"updated_at": datetime.utcnow()}
    if body.executive_emails is not None:
        cleaned_exec = []
        for em in body.executive_emails:
            em_clean = em.strip()
            if em_clean:
                if not validate_email_address(em_clean):
                    raise HTTPException(400, f"Invalid executive email address: {em_clean}")
                cleaned_exec.append(em_clean)
        update_data["executive_emails"] = cleaned_exec

    if body.office_emails is not None:
        cleaned_offices = {}
        for off_id, em in body.office_emails.items():
            em_clean = (em or "").strip()
            if em_clean:
                if not validate_email_address(em_clean):
                    raise HTTPException(400, f"Invalid email for office {off_id}: {em_clean}")
                cleaned_offices[off_id] = em_clean
        update_data["office_emails"] = cleaned_offices

    if body.send_hour is not None:
        update_data["send_hour"] = body.send_hour
    if body.is_enabled is not None:
        update_data["is_enabled"] = body.is_enabled

    db.settings.update_one(
        {"_id": "digest_settings"},
        {"$set": update_data},
        upsert=True
    )
    audit(db, user, "digest_settings_updated", "master_config")
    return {"ok": True, "message": "Email notification settings saved successfully."}


class SendDigestBody(BaseModel):
    target_date: str | None = None
    test_email: str | None = None


@app.post("/digest/send-now")
def send_digest_now(body: SendDigestBody = None, user=Depends(admin), db=Depends(get_db)):
    """Trigger an immediate delivery of the Morning Executive Digest or a test email."""
    from src.services.email_service import (
        build_morning_digest,
        send_email,
        validate_email_address,
        is_smtp_configured
    )

    body = body or SendDigestBody()
    settings = db.settings.find_one({"_id": "digest_settings"}) or {}

    recipients = []
    if body.test_email:
        test_addr = body.test_email.strip()
        if not validate_email_address(test_addr):
            raise HTTPException(400, "Invalid test email address.")
        recipients = [test_addr]
    else:
        if user["role"] == "office_admin":
            off_email = settings.get("office_emails", {}).get(user["office_id"])
            if off_email:
                recipients.append(off_email)
            else:
                raise HTTPException(400, "No email address configured for your branch. Please configure one first.")
        else:
            recipients = list(settings.get("executive_emails", []))
            for em in settings.get("office_emails", {}).values():
                if em and em not in recipients:
                    recipients.append(em)
            if not recipients:
                raise HTTPException(400, "No recipient emails configured. Please add executive or office email addresses first.")

    target_date = body.target_date
    if target_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", target_date):
        raise HTTPException(400, "Invalid target date format. Use YYYY-MM-DD.")

    digest = build_morning_digest(db, target_date)
    subject = f"Randaframes Attendance - Morning Digest ({digest['date']})"
    send_res = send_email(recipients, subject, digest["html"], digest["text"])

    db.digest_history.insert_one({
        "target_date": digest["date"],
        "sent_at": datetime.utcnow(),
        "triggered_by": user.get("username", "admin"),
        "recipients": recipients,
        "total_staff": digest["total_staff"],
        "total_present": digest["total_present"],
        "total_absent": digest["total_absent"],
        "turnout_rate": digest["turnout_rate"],
        "success": send_res.get("success", False),
        "result_message": send_res.get("message") or send_res.get("error", "")
    })

    audit(db, user, "digest_sent_manually", f"sent_to_{len(recipients)}_recipients")
    return {
        "ok": True,
        "date": digest["date"],
        "recipients": recipients,
        "delivery": send_res,
        "stats": {
            "total_staff": digest["total_staff"],
            "present": digest["total_present"],
            "absent": digest["total_absent"],
            "turnout": f"{digest['turnout_rate']}%"
        }
    }

