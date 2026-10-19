"""Connection diagnostic with no credentials or database contents in output."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.database import DatabaseManager

try:
    db = DatabaseManager.get_db()
    print({name: db[name].count_documents({}) for name in ('users', 'employees', 'attendance_records')})
except Exception as exc:
    print('Database connection failed: ' + type(exc).__name__)
    sys.exit(1)
