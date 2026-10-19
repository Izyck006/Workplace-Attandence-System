from datetime import datetime, timedelta
import json
import pytest
import mongomock
from bson import ObjectId, json_util
from fastapi.testclient import TestClient
from src.server.app import app, get_db, record_attendance
from src.server.security import ph, generate_password, token_hash
from src.offices import OFFICES
from src.server.schema import assign_legacy


@pytest.fixture
def system():
    db = mongomock.MongoClient().attendance
    db.offices.insert_many([dict(o) for o in OFFICES])
    db.employees.create_index('employee_no', unique=True)
    db.attendance_records.create_index([('employee_id', 1), ('work_date', 1)], unique=True)
    password_hash = ph.hash('Example12!')
    for username, role, office in [('kano', 'office_admin', 'engineering-kano'),
                                  ('abuja', 'office_admin', 'logistics-abuja'), ('master', 'main_admin', None)]:
        db.users.insert_one({'username': username, 'role': role, 'office_id': office,
                             'password_hash': password_hash, 'is_active': True, 'failed_attempts': 0,
                             'must_change_password': False})
    kano = {'_id': ObjectId(), 'employee_no': 'K1', 'full_name': 'Kano Person',
            'office_id': 'engineering-kano', 'status': 'active'}
    abuja = {'_id': ObjectId(), 'employee_no': 'A1', 'full_name': 'Abuja Person',
             'office_id': 'logistics-abuja', 'status': 'active'}
    db.employees.insert_many([kano, abuja])
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client, db, kano, abuja
    app.dependency_overrides.clear()


def auth(client, username='kano'):
    response = client.post('/login', json={'username': username, 'password': 'Example12!'})
    assert response.status_code == 200, response.text
    return {'Authorization': 'Bearer ' + response.json()['token']}


def wire(value):
    return json.loads(json_util.dumps(value))


def test_office_cannot_read_other_office_even_with_forged_query(system):
    client, db, kano, abuja = system
    headers = auth(client)
    for query in [{}, {'office_id': 'logistics-abuja'}, {'$or': [{}, {'office_id': 'logistics-abuja'}]}, {'_id': abuja['_id']}]:
        result = client.post('/read', headers=headers, json=wire({'collection': 'employees', 'query': query}))
        assert result.status_code == 200
        assert all(row['office_id'] == 'engineering-kano' for row in result.json())
    assert len(client.post('/read', headers=auth(client, 'master'), json={'collection': 'employees'}).json()) == 2


def test_forged_writes_enrollment_and_credentials_denied(system):
    client, db, kano, abuja = system
    headers = auth(client)
    response = client.post('/save', headers=headers, json={'collection': 'employees', 'id': str(abuja['_id']),
                                                           'document': {'full_name': 'Hacked'}})
    assert response.status_code == 404
    response = client.post('/save', headers=headers, json={'collection': 'employees',
        'document': {'office_id': 'logistics-abuja', 'employee_no': 'BAD'}})
    assert response.status_code == 403
    response = client.post(f"/employees/{abuja['_id']}/fingerprint", headers=headers,
                            json={'samples': [[[1] * 32] * 25]})
    assert response.status_code == 404
    for collection in ('users', 'sessions', 'audit_events'):
        assert client.post('/read', headers=headers, json={'collection': collection}).status_code == 403
    assert client.post('/offices/logistics-abuja/reset-password', headers=headers).status_code == 403
    assert db.employees.find_one({'_id': abuja['_id']})['full_name'] == 'Abuja Person'


def test_kiosk_token_cannot_manage_staff_or_change_password(system):
    client, db, kano, abuja = system
    headers = auth(client)
    result = client.post('/kiosk', headers=headers)
    assert result.status_code == 200
    kiosk = {'Authorization': 'Bearer ' + result.json()['token']}
    assert client.post('/read', headers=headers, json={'collection': 'employees'}).status_code == 401
    assert client.post('/read', headers=kiosk, json={'collection': 'employees'}).status_code == 403
    assert client.post('/password', headers=kiosk, json={'password': 'Another12!'}).status_code == 403
    assert client.post('/kiosk', headers=auth(client, 'master')).status_code == 403


def test_attendance_is_idempotent_and_uses_nigerian_date(system):
    client, db, kano, abuja = system
    now = datetime(2026, 10, 19, 23, 30)
    assert record_attendance(db, kano, 'in', now) == 'Time In Recorded'
    assert record_attendance(db, kano, 'in', now) == 'Already Timed In'
    assert db.attendance_records.count_documents({}) == 1
    assert db.attendance_records.find_one()['work_date'] == '2026-10-20'
    assert record_attendance(db, kano, 'out', now + timedelta(minutes=15)) == 'Time Out Recorded'
    assert record_attendance(db, kano, 'out', now + timedelta(minutes=20)) == 'Already Timed Out'
    assert db.attendance_records.find_one()['minutes_worked'] == 15
    result = client.post('/read', headers=auth(client, 'abuja'), json={'collection': 'attendance_records'})
    assert result.json() == []


def test_password_policy_lockout_expiration_and_reset(system):
    client, db, kano, abuja = system
    headers = auth(client)
    for _ in range(5):
        assert client.post('/login', json={'username': 'kano', 'password': 'wrong'}).status_code == 401
    assert client.post('/login', json={'username': 'kano', 'password': 'Example12!'}).status_code == 429
    result = client.post('/offices/engineering-kano/reset-password', headers=auth(client, 'master'))
    assert result.status_code == 200
    password = result.json()['password']
    assert len(password) == 10 and any(c.isdigit() for c in password) and any(not c.isalnum() for c in password)
    assert client.post('/read', headers=headers, json={'collection': 'employees'}).status_code == 401
    result = client.post('/login', json={'username': 'kano', 'password': password})
    headers = {'Authorization': 'Bearer ' + result.json()['token']}
    assert client.post('/read', headers=headers, json={'collection': 'employees'}).status_code == 403
    assert client.post('/password', headers=headers, json={'password': 'abcdefghij'}).status_code == 400
    assert client.post('/password', headers=headers, json={'password': 'NewPassword12!'}).status_code == 200
    assert client.post('/read', headers=headers, json={'collection': 'employees'}).status_code == 200
    db.sessions.update_many({}, {'$set': {'expires_at': datetime.utcnow() - timedelta(seconds=1)}})
    assert client.post('/read', headers=headers, json={'collection': 'employees'}).status_code == 401


def test_legacy_assignment_preserves_existing_offices(system):
    client, db, kano, abuja = system
    legacy = db.employees.insert_one({'employee_no': 'legacy'}).inserted_id
    legacy_null = db.employees.insert_one({'employee_no': 'legacy_null', 'office_id': None}).inserted_id
    t_in = datetime(2026, 1, 1, 10, 0, 0)
    db.attendance_records.insert_one({'employee_id': legacy, 'work_date': '2026-01-01', 'clock_in_at': t_in})
    assign_legacy(db, 'engineering-kano', normalize_timestamps=True)
    assign_legacy(db, 'engineering-kano', normalize_timestamps=True)
    assert db.employees.find_one({'_id': legacy})['office_id'] == 'engineering-kano'
    assert db.employees.find_one({'_id': legacy_null})['office_id'] == 'engineering-kano'
    assert db.employees.find_one({'_id': abuja['_id']})['office_id'] == 'logistics-abuja'
    assert db.attendance_records.find_one({'employee_id': legacy})['office_id'] == 'engineering-kano'
    assert db.attendance_records.find_one({'employee_id': legacy})['clock_in_at'] == t_in - timedelta(hours=1)


def test_scan_matches_only_own_office_and_rejects_inactive_staff(system, monkeypatch):
    client, db, kano, abuja = system
    from src.services.fingerprint import FingerprintMatcher
    monkeypatch.setattr(FingerprintMatcher, 'get_match_score', lambda self, a, b: 100 if (a == b).all() else 0)
    for employee, number in [(kano, 1), (abuja, 2)]:
        db.employees.update_one({'_id': employee['_id']}, {'$set': {
            'has_fingerprint': True, 'fingerprint_samples': [[[number] * 32] * 25]}})
    headers = auth(client)
    assert client.post('/scan', headers=headers, json={'samples': [[[2] * 32] * 25], 'action': 'in'}).status_code == 404
    assert client.post('/scan', headers=headers, json={'samples': [[[1] * 32] * 25], 'action': 'in'}).status_code == 200
    db.employees.update_one({'_id': kano['_id']}, {'$set': {'status': 'inactive'}})
    assert client.post('/scan', headers=headers, json={'samples': [[[1] * 32] * 25], 'action': 'in'}).status_code == 404


def test_query_code_and_unauthenticated_access_rejected(system):
    client, db, kano, abuja = system
    assert client.post('/read', json={'collection': 'employees'}).status_code in (401, 403)
    assert client.post('/read', headers=auth(client), json={'collection': 'employees',
                       'query': {'$where': 'return true'}}).status_code == 400


def test_generated_passwords_are_ten_characters():
    passwords = {generate_password() for _ in range(100)}
    assert len(passwords) == 100
    for password in passwords:
        assert len(password) == 10
        assert any(c.isalpha() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(not c.isalnum() for c in password)
