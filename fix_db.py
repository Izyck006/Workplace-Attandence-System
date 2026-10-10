import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.data.database import DatabaseManager

def fix_db():
    db = DatabaseManager.get_db()
    
    
    result = db.employees.update_many(
        {"fingerprint_descriptors": {"$exists": True}},
        {"$set": {"has_fingerprint": True}}
    )
    print(f"Retroactively fixed {result.modified_count} employee records in MongoDB.")

if __name__ == "__main__":
    fix_db()
