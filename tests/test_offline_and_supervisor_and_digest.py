from datetime import datetime, timezone, timedelta
import json
import pytest
import mongomock
import numpy as np
from bson import ObjectId, json_util
from fastapi.testclient import TestClient

from src.server.app import app, get_db
from src.server.security import ph
from src.offices import OFFICES
from src.services.offline_sync import OfflineSyncManager


@pytest.fixture
def system():
    db = mongomock.MongoClient().attendance
    db.offices.insert_many([dict(o) for o in OFFICES])
    db.employees.create_index('employee_no', unique=True)
    db.attendance_records.create_index([('employee_id', 1), ('work_date', 1)], unique=True)

    pw_hash = ph.hash('Password123!')
    for username, role, office in [
        ('kano_admin', 'office_admin', 'engineering-kano'),
        ('abuja_admin', 'office_admin', 'logistics-abuja'),
        ('master_admin', 'main_admin', None)
    ]:
        db.users.insert_one({
            'username': username,
            'role': role,
            'office_id': office,
            'password_hash': pw_hash,
            'is_active': True,
            'failed_attempts': 0,
            'must_change_password': False
        })

    # Sample descriptor array of shape (50, 32)
    sample_desc = np.ones((50, 32), dtype=np.uint8).tolist()

    kano_emp = {
        '_id': ObjectId(),
        'employee_no': 'K001',
        'first_name': 'Aliyu',
        'last_name': 'Kano',
        'full_name': 'Aliyu Kano',
        'job_title': 'Engineer',
        'office_id': 'engineering-kano',
        'status': 'active',
        'has_fingerprint': True,
        'fingerprint_samples': [sample_desc]
    }
    abuja_emp = {
        '_id': ObjectId(),
        'employee_no': 'A001',
        'first_name': 'Bello',
        'last_name': 'Abuja',
        'full_name': 'Bello Abuja',
        'job_title': 'Logistics Lead',
        'office_id': 'logistics-abuja',
        'status': 'active',
        'has_fingerprint': True,
        'fingerprint_samples': [sample_desc]
    }
    db.employees.insert_many([kano_emp, abuja_emp])

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client, db, kano_emp, abuja_emp
    app.dependency_overrides.clear()


def login_auth(client, username='kano_admin'):
    res = client.post('/login', json={'username': username, 'password': 'Password123!'})
    assert res.status_code == 200, res.text
    return {'Authorization': f"Bearer {res.json()['token']}"}


def test_sync_kiosk_cache(system):
    client, db, kano_emp, abuja_emp = system
    kano_headers = login_auth(client, 'kano_admin')

    # 1. Office admin only gets their office's active employees with templates
    res = client.get('/sync/kiosk-cache', headers=kano_headers)
    assert res.status_code == 200
    data = res.json()
    assert data['count'] == 1
    assert data['employees'][0]['employee_no'] == 'K001'
    assert 'fingerprint_samples' in data['employees'][0]

    # 2. Master admin gets all offices
    master_headers = login_auth(client, 'master_admin')
    res_master = client.get('/sync/kiosk-cache', headers=master_headers)
    assert res_master.status_code == 200
    assert res_master.json()['count'] == 2


def test_sync_offline_records(system):
    client, db, kano_emp, abuja_emp = system
    kano_headers = login_auth(client, 'kano_admin')

    now_iso = datetime.now(timezone.utc).isoformat()
    work_date = "2026-10-26"

    # Batch offline sync payload
    payload = {
        "records": [
            {
                "offline_id": 101,
                "employee_id": str(kano_emp["_id"]),
                "action": "in",
                "recorded_at": now_iso,
                "work_date": work_date,
                "office_id": "engineering-kano"
            },
            {
                "offline_id": 102,
                "employee_id": str(kano_emp["_id"]),
                "action": "out",
                "recorded_at": now_iso,
                "work_date": work_date,
                "office_id": "engineering-kano"
            }
        ]
    }

    res = client.post('/sync/offline-records', headers=kano_headers, json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data['ok'] is True
    assert 101 in res_data['synced_ids']
    assert 102 in res_data['synced_ids']

    # Verify attendance record in MongoDB
    rec = db.attendance_records.find_one({"employee_id": kano_emp["_id"], "work_date": work_date})
    assert rec is not None
    assert rec["source"] == "scanner"
    assert rec.get("offline_synced") is True
    assert rec["clock_in_at"] is not None
    assert rec["clock_out_at"] is not None


def test_supervisor_manual_clock_in_and_out(system):
    client, db, kano_emp, abuja_emp = system
    kano_headers = login_auth(client, 'kano_admin')

    # 1. Kano admin cannot manually clock in Abuja employee (404 / scoped)
    bad_res = client.post('/attendance/manual-record', headers=kano_headers, json={
        "employee_id": str(abuja_emp["_id"]),
        "action": "in",
        "reason": "Cut finger"
    })
    assert bad_res.status_code == 404

    # 2. Kano admin successfully clocks in Kano employee
    res_in = client.post('/attendance/manual-record', headers=kano_headers, json={
        "employee_id": str(kano_emp["_id"]),
        "action": "in",
        "work_date": "2026-10-26",
        "time_str": "08:15",
        "reason": "Cut finger / bandaged"
    })
    assert res_in.status_code == 200
    assert res_in.json()["ok"] is True

    # Verify record in DB
    rec = db.attendance_records.find_one({"employee_id": kano_emp["_id"], "work_date": "2026-10-26"})
    assert rec is not None
    assert rec["source"] == "manual"
    assert rec.get("supervisor_override") is True
    assert rec["recorded_by"] == "kano_admin"
    assert "Cut finger" in rec["reason"]

    # 3. Kano admin clocks out the employee
    res_out = client.post('/attendance/manual-record', headers=kano_headers, json={
        "employee_id": str(kano_emp["_id"]),
        "action": "out",
        "work_date": "2026-10-26",
        "time_str": "17:05",
        "reason": "Approved departure"
    })
    assert res_out.status_code == 200
    assert res_out.json()["ok"] is True

    rec_out = db.attendance_records.find_one({"employee_id": kano_emp["_id"], "work_date": "2026-10-26"})
    assert rec_out["clock_out_at"] is not None
    assert rec_out["minutes_worked"] > 0

    # 4. Verify audit event
    audit_log = db.audit_events.find_one({"action": "supervisor_manual_clock_in"})
    assert audit_log is not None


def test_digest_settings_and_send_now(system):
    client, db, kano_emp, abuja_emp = system
    master_headers = login_auth(client, 'master_admin')
    kano_headers = login_auth(client, 'kano_admin')

    # 1. Kano admin saves their branch alert email
    res_k = client.post('/digest/settings', headers=kano_headers, json={
        "office_email": "kano.manager@randaframes.com"
    })
    assert res_k.status_code == 200

    # 2. Master admin saves executive emails
    res_m = client.post('/digest/settings', headers=master_headers, json={
        "executive_emails": ["md@randaframes.com", "hr@randaframes.com"],
        "send_hour": 8,
        "is_enabled": True
    })
    assert res_m.status_code == 200

    # 3. Master admin reads settings
    read_m = client.get('/digest/settings', headers=master_headers)
    assert read_m.status_code == 200
    assert "md@randaframes.com" in read_m.json()["executive_emails"]
    assert read_m.json()["send_hour"] == 8

    # 4. Trigger send-now test digest
    send_res = client.post('/digest/send-now', headers=master_headers, json={
        "test_email": "test.recipient@randaframes.com"
    })
    assert send_res.status_code == 200
    data = send_res.json()
    assert data["ok"] is True
    assert "test.recipient@randaframes.com" in data["recipients"]
    assert data["stats"]["total_staff"] == 2


def test_local_offline_sync_manager(tmp_path):
    # Test local SQLite offline manager operations in a clean tmp database
    db_file = str(tmp_path / "test_offline.db")
    mgr = OfflineSyncManager(db_path=db_file)

    sample = np.ones((50, 32), dtype=np.uint8).tolist()
    employees = [
        {
            "_id": "507f1f77bcf86cd799439011",
            "office_id": "engineering-kano",
            "first_name": "Test",
            "last_name": "User",
            "full_name": "Test User",
            "employee_no": "T001",
            "job_title": "Tester",
            "fingerprint_samples": [sample],
            "photo_bytes": b"fake_bytes",
            "status": "active"
        }
    ]

    # Save to SQLite cache
    mgr.save_cached_employees(employees)
    cached = mgr.get_cached_employees()
    assert len(cached) == 1
    assert cached[0]["employee_no"] == "T001"

    # Record offline attendance
    res = mgr.record_offline_attendance(cached[0], "in")
    assert res["offline"] is True
    assert "Recorded" in res["action"]

    # Verify pending queue
    pending = mgr.get_pending_records()
    assert len(pending) == 1
    assert pending[0]["action"] == "in"
    assert mgr.get_pending_count() == 1

    # Mark as synced
    mgr.mark_records_synced([pending[0]["id"]])
    assert mgr.get_pending_count() == 0
