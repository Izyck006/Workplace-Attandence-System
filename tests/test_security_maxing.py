import os
import time
import hmac
import hashlib
from datetime import datetime, timedelta
import pytest
import mongomock
from bson import ObjectId
from fastapi.testclient import TestClient

from src.server.app import app, get_db, validate_photo_bytes, sanitize_string
from src.server.rate_limiter import rate_limiter
from src.server.security import ph
from src.offices import OFFICES
from src.server.webhooks import verify_paystack_signature, verify_stripe_signature


@pytest.fixture
def sec_system():
    db = mongomock.MongoClient().attendance
    db.offices.insert_many([dict(o) for o in OFFICES])
    db.employees.create_index('employee_no', unique=True)
    db.attendance_records.create_index([('employee_id', 1), ('work_date', 1)], unique=True)
    password_hash = ph.hash('Example12!')
    db.users.insert_one({
        'username': 'kano',
        'role': 'office_admin',
        'office_id': 'engineering-kano',
        'password_hash': password_hash,
        'is_active': True,
        'failed_attempts': 0,
        'must_change_password': False
    })
    kano_emp = {
        '_id': ObjectId(),
        'employee_no': 'K100',
        'full_name': 'Kano Staff',
        'office_id': 'engineering-kano',
        'status': 'active'
    }
    db.employees.insert_one(kano_emp)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client, db, kano_emp
    app.dependency_overrides.clear()


def get_token(client):
    res = client.post('/login', json={'username': 'kano', 'password': 'Example12!'})
    assert res.status_code == 200
    return {'Authorization': f"Bearer {res.json()['token']}"}


def test_security_headers_present(sec_system):
    client, db, emp = sec_system
    res = client.get('/health')
    assert res.status_code == 200
    headers = res.headers
    assert headers.get('Strict-Transport-Security') == 'max-age=31536000; includeSubDomains; preload'
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('X-Frame-Options') == 'DENY'
    assert headers.get('X-XSS-Protection') == '1; mode=block'
    assert headers.get('Content-Security-Policy') == "default-src 'none'; frame-ancestors 'none'"
    assert 'no-store' in headers.get('Cache-Control', '')


def test_rate_limiter_logic():
    limiter = rate_limiter
    test_key = f"test_unit_{time.time()}"
    for _ in range(5):
        allowed, retry = limiter.check(test_key, max_requests=5, window_seconds=60)
        assert allowed is True
        assert retry == 0

    allowed, retry = limiter.check(test_key, max_requests=5, window_seconds=60)
    assert allowed is False
    assert retry > 0


def test_photo_magic_bytes_validation():
    # Valid JPEG
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 50
    validate_photo_bytes(jpeg_bytes)

    # Valid PNG
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    validate_photo_bytes(png_bytes)

    # Valid WEBP
    webp_bytes = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 50
    validate_photo_bytes(webp_bytes)

    # Invalid executable/script pretending to be photo
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    with pytest.raises(Exception):
        validate_photo_bytes(exe_bytes)

    # Invalid empty or text bytes
    with pytest.raises(Exception):
        validate_photo_bytes(b"<script>alert(1)</script>")

    # Over 2MB
    huge_bytes = b"\xff\xd8\xff" + b"\x00" * 2_000_005
    with pytest.raises(Exception):
        validate_photo_bytes(huge_bytes)


def test_input_sanitization():
    xss_payload = "<script>alert('xss')</script> John Doe"
    cleaned = sanitize_string(xss_payload, 100)
    assert "<script>" not in cleaned
    assert "alert" not in cleaned
    assert "John Doe" in cleaned

    control_chars = "Hello\x00\x01\x02World"
    cleaned_ctrl = sanitize_string(control_chars, 50)
    assert "\x00" not in cleaned_ctrl
    assert cleaned_ctrl == "HelloWorld"


def test_nosql_injection_rejection(sec_system):
    client, db, emp = sec_system
    headers = get_token(client)

    # Null byte in key
    res = client.post('/read', headers=headers, json={'collection': 'employees', 'query': {'office_id\x00': 'val'}})
    assert res.status_code == 400

    # Nested key traversal
    res = client.post('/read', headers=headers, json={'collection': 'employees', 'query': {'department.secret': 'val'}})
    assert res.status_code == 400

    # Disallowed mongo operator
    res = client.post('/read', headers=headers, json={'collection': 'employees', 'query': {'$where': 'true'}})
    assert res.status_code == 400


def test_paystack_webhook_verification():
    secret = "sk_test_paystack_secret_123"
    body = b'{"event": "charge.success", "data": {"amount": 5000}}'
    correct_sig = hmac.new(secret.encode('utf-8'), body, hashlib.sha512).hexdigest()

    assert verify_paystack_signature(body, correct_sig, secret) is True
    assert verify_paystack_signature(body, "invalidsig", secret) is False
    assert verify_paystack_signature(body, None, secret) is False


def test_stripe_webhook_verification():
    secret = "whsec_stripe_test_456"
    body = b'{"type": "payment_intent.succeeded", "data": {}}'
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.".encode('utf-8') + body
    correct_v1 = hmac.new(secret.encode('utf-8'), signed_payload, hashlib.sha256).hexdigest()
    sig_header = f"t={timestamp},v1={correct_v1}"

    assert verify_stripe_signature(body, sig_header, secret) is True
    assert verify_stripe_signature(body, f"t={timestamp},v1=wrongsig", secret) is False
    assert verify_stripe_signature(body, f"t={timestamp - 500},v1={correct_v1}", secret, tolerance=300) is False
