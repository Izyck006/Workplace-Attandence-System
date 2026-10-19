from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from src.client import ClientDatabase as DatabaseManager

class DepartmentRepository:
    def __init__(self):
        self.db = DatabaseManager.get_db()
        self.collection = self.db.departments

    def create(self, name: str, is_active: bool = True) -> ObjectId:
        import datetime
        doc = {
            "name": name,
            "is_active": is_active,
            "created_at": datetime.datetime.utcnow()
        }
        result = self.collection.insert_one(doc)
        return result.inserted_id

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.collection.find())

    def get_by_id(self, dept_id: ObjectId) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": dept_id})

class EmployeeRepository:
    def __init__(self):
        self.db = DatabaseManager.get_db()
        self.collection = self.db.employees

    def create(self, employee_no: str, full_name: str, department_id: ObjectId, 
               line_manager_id: Optional[ObjectId] = None, phone: Optional[str] = None) -> ObjectId:
        import datetime
        doc = {
            "employee_no": employee_no,
            "full_name": full_name,
            "department_id": department_id,
            "line_manager_id": line_manager_id,
            "phone": phone,
            "status": "active",
            "created_at": datetime.datetime.utcnow(),
            "deactivated_at": None
        }
        result = self.collection.insert_one(doc)
        return result.inserted_id

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.collection.find())

    def get_by_id(self, emp_id: ObjectId) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": emp_id})
