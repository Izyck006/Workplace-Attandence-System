import secrets
import string
from datetime import datetime, timedelta
from hashlib import sha256

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException
from pymongo import ReturnDocument

ph = PasswordHasher()
SYMBOLS = "!@#$%&*?"


def generate_password():
    chars = [secrets.choice(pool) for pool in
             (string.ascii_uppercase, string.ascii_lowercase, string.digits, SYMBOLS)]
    chars += [secrets.choice(string.ascii_letters + string.digits + SYMBOLS) for _ in range(6)]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def validate_password(password):
    if not (10 <= len(password) <= 128 and any(c.isalpha() for c in password)
            and any(c.isdigit() for c in password) and any(c in SYMBOLS for c in password)):
        raise HTTPException(400, "Use at least 10 characters with letters, numbers and a symbol (!@#$%&*?).")


def token_hash(token):
    return sha256(token.encode()).hexdigest()


def login(db, username, password):
    now = datetime.utcnow()
    user = db.users.find_one({"username": username})
    if not user or not user.get("is_active"):
        raise HTTPException(401, "Invalid username or password.")
    if user.get("locked_until") and user["locked_until"] > now:
        raise HTTPException(429, "Account locked for 15 minutes after repeated failed logins.")
    try:
        valid = ph.verify(user["password_hash"], password)
    except (VerificationError, InvalidHashError):
        valid = False
    if not valid:
        if user.get("locked_until") and user["locked_until"] <= now:
            db.users.update_one({"_id": user["_id"], "locked_until": user["locked_until"]},
                                {"$set": {"failed_attempts": 0, "locked_until": None}})
        failed = db.users.find_one_and_update({"_id": user["_id"]}, {"$inc": {"failed_attempts": 1}},
                                              return_document=ReturnDocument.AFTER)
        if failed["failed_attempts"] >= 5:
            db.users.update_one({"_id": user["_id"]}, {"$set": {"locked_until": now + timedelta(minutes=15)}})
        raise HTTPException(401, "Invalid username or password.")
    if user["role"] not in ("main_admin", "office_admin"):
        raise HTTPException(403, "Ask the master admin to assign an office account.")
    if user["role"] == "office_admin" and not db.offices.find_one({"_id": user.get("office_id")}):
        raise HTTPException(403, "Account has no valid office.")
    update = {"failed_attempts": 0, "locked_until": None, "last_login_at": now}
    if ph.check_needs_rehash(user["password_hash"]):
        update["password_hash"] = ph.hash(password)
    db.users.update_one({"_id": user["_id"]}, {"$set": update})
    token = secrets.token_urlsafe(32)
    # Admin console session expires in 2 minutes of idle time
    db.sessions.insert_one({"_id": token_hash(token), "user_id": user["_id"], "kiosk": False,
                            "expires_at": now + timedelta(minutes=2)})
    return token, {k: user[k] for k in ("_id", "username", "role", "office_id", "must_change_password") if k in user}
