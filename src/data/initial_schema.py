from pymongo.database import Database
import pymongo

def up(db: Database):
    
    if 'departments' not in db.list_collection_names():
        db.create_collection('departments', validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["name", "is_active", "created_at"],
                "properties": {
                    "name": {"bsonType": "string"},
                    "is_active": {"bsonType": "bool"},
                    "created_at": {"bsonType": "date"}
                }
            }
        })
        db.departments.create_index("name", unique=True)

    
    if 'employees' not in db.list_collection_names():
        db.create_collection('employees', validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["employee_no", "full_name", "department_id", "status", "created_at"],
                "properties": {
                    "employee_no": {"bsonType": "string"},
                    "full_name": {"bsonType": "string"},
                    "department_id": {"bsonType": "objectId"},
                    "line_manager_id": {"bsonType": ["objectId", "null"]},
                    "phone": {"bsonType": ["string", "null"]},
                    "status": {"enum": ["active", "inactive"]},
                    "created_at": {"bsonType": "date"},
                    "deactivated_at": {"bsonType": ["date", "null"]}
                }
            }
        })
        db.employees.create_index("employee_no", unique=True)

    
    if 'users' not in db.list_collection_names():
        db.create_collection('users', validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["username", "password_hash", "role", "must_change_password", "failed_attempts", "is_active"],
                "properties": {
                    "employee_id": {"bsonType": ["objectId", "null"]},
                    "username": {"bsonType": "string"},
                    "password_hash": {"bsonType": "string"},
                    "role": {"enum": ["main_admin", "line_manager"]},
                    "must_change_password": {"bsonType": "bool"},
                    "failed_attempts": {"bsonType": "int"},
                    "locked_until": {"bsonType": ["date", "null"]},
                    "is_active": {"bsonType": "bool"},
                    "last_login_at": {"bsonType": ["date", "null"]}
                }
            }
        })
        db.users.create_index("username", unique=True)
        
        db.users.create_index(
            "employee_id", 
            unique=True, 
            partialFilterExpression={"employee_id": {"$exists": True, "$type": "objectId"}}
        )

    
    if 'attendance_records' not in db.list_collection_names():
        db.create_collection('attendance_records', validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["employee_id", "work_date", "status", "day_type", "source", "is_edited", "created_at", "updated_at"],
                "properties": {
                    "employee_id": {"bsonType": "objectId"},
                    "work_date": {"bsonType": "string"},
                    "department_id_snapshot": {"bsonType": ["objectId", "null"]},
                    "line_manager_id_snapshot": {"bsonType": ["objectId", "null"]},
                    "clock_in_at": {"bsonType": ["date", "null"]},
                    "clock_out_at": {"bsonType": ["date", "null"]},
                    "minutes_worked": {"bsonType": ["int", "null"]},
                    "status": {"enum": ["present", "incomplete", "absent", "on_leave", "system_down"]},
                    "day_type": {"enum": ["working", "off_day", "holiday"]},
                    "source": {"enum": ["scanner", "manual", "system"]},
                    "is_edited": {"bsonType": "bool"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        })
        db.attendance_records.create_index([("employee_id", pymongo.ASCENDING), ("work_date", pymongo.ASCENDING)], unique=True)
        
    
    
    
    if 'settings' not in db.list_collection_names():
        db.create_collection('settings')
        db.settings.create_index("key", unique=True)
