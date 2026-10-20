"""python -m src.server.bootstrap --legacy-office engineering-kano"""
import argparse
import csv
from datetime import datetime
from bson import json_util
from pathlib import Path
from src.data.database import DatabaseManager
from src.offices import OFFICES
from src.server.schema import initialize, assign_legacy
from src.server.security import generate_password, ph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-office", required=True)
    parser.add_argument("--credentials", default="private/office-credentials.csv")
    parser.add_argument("--normalize-legacy-timestamps", action="store_true",
                        help="Subtract 1 hour from legacy timestamps that were stored as naive WAT")
    args = parser.parse_args()
    path = Path(args.credentials)
    db = DatabaseManager.get_db()
    db.command('ping')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Office", "Username", "Temporary password"])
        snapshot = path.parent / ('pre-migration-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.jsonl')
        with snapshot.open('x', encoding='utf-8') as backup:
            for collection in db.list_collection_names():
                for document in db[collection].find():
                    backup.write(json_util.dumps({'collection': collection, 'document': document}) + '\n')
        initialize(db)
        assign_legacy(db, args.legacy_office, normalize_timestamps=args.normalize_legacy_timestamps)
        from src.server.legacy import convert_templates
        converted, failed = convert_templates(db)
        print(f'Legacy fingerprints converted: {converted}; require re-enrollment: {failed}.')
        accounts = [(o["name"], o["_id"], "office_admin", o["_id"]) for o in OFFICES]
        if not db.users.find_one({"role": "main_admin", "is_active": True}):
            accounts.insert(0, ("Master admin", "master.admin", "main_admin", None))
        for name, username, role, office_id in accounts:
            existing = db.users.find_one({"username": username})
            if existing:
                if existing.get('role') != role or existing.get('office_id') != office_id:
                    raise ValueError(f'Username {username} already belongs to a different account. Resolve the collision before provisioning.')
                continue
            password = generate_password()
            db.users.insert_one({"username": username, "password_hash": ph.hash(password),
                "role": role, "office_id": office_id, "is_active": True,
                "must_change_password": True, "failed_attempts": 0})
            writer.writerow([name, username, password])
            handle.flush()
    print(f"Provisioning complete. Deliver credentials privately from {path}. Existing accounts were preserved.")


if __name__ == "__main__":
    main()
