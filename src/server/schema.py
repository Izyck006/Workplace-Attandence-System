from datetime import datetime
from src.offices import OFFICES


def initialize(db):
    # Run on the server during deployment, never on an office workstation.
    from src.data.initial_schema import up
    up(db)
    validator = db.users.options().get('validator', {})
    schema = validator.setdefault('$jsonSchema', {'bsonType': 'object'})
    schema.setdefault('properties', {})['role'] = {'enum': ['main_admin', 'line_manager', 'office_admin']}
    db.command('collMod', 'users', validator=validator)
    db.users.create_index('username', unique=True)
    db.departments.create_index('name', unique=True)
    db.employees.create_index('employee_no', unique=True)
    for office in OFFICES:
        db.offices.update_one({"_id": office["_id"]}, {"$setOnInsert": office}, upsert=True)
    db.sessions.create_index("expires_at", expireAfterSeconds=0)
    db.employees.create_index([("office_id", 1), ("status", 1)])
    db.attendance_records.create_index([("office_id", 1), ("work_date", -1)])
    db.attendance_records.create_index([("employee_id", 1), ("work_date", 1)], unique=True)
    db.audit_events.create_index("created_at")


def assign_legacy(db, office_id, normalize_timestamps=False):
    from src.offices import OFFICE_MAP
    if office_id not in OFFICE_MAP:
        raise ValueError("Unknown office")
    unassigned = {"$or": [{"office_id": {"$exists": False}}, {"office_id": None}, {"office_id": ""}]}
    db.employees.update_many(unassigned, {"$set": {"office_id": office_id}})
    for emp in db.employees.find({}, {"office_id": 1}):
        db.attendance_records.update_many(
            {"employee_id": emp["_id"], "$or": [{"office_id": {"$exists": False}}, {"office_id": None}, {"office_id": ""}]},
            {"$set": {"office_id": emp["office_id"]}}
        )
    if normalize_timestamps:
        from datetime import timedelta
        for rec in db.attendance_records.find({"clock_in_at": {"$ne": None}, "_legacy_normalized": {"$exists": False}}):
            updates = {"_legacy_normalized": True}
            if rec.get("clock_in_at"):
                updates["clock_in_at"] = rec["clock_in_at"] - timedelta(hours=1)
            if rec.get("clock_out_at"):
                updates["clock_out_at"] = rec["clock_out_at"] - timedelta(hours=1)
            db.attendance_records.update_one({"_id": rec["_id"]}, {"$set": updates})
    db.audit_events.insert_one({"action": "assign_legacy", "office_id": office_id,
                                "normalize_timestamps": bool(normalize_timestamps),
                                "created_at": datetime.utcnow()})
