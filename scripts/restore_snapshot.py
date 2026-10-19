"""Restore database from a pre-migration JSONL snapshot."""
import argparse
import sys
from pathlib import Path
from bson import json_util

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.database import DatabaseManager


def restore(snapshot_path: str):
    path = Path(snapshot_path)
    if not path.is_file():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

    db = DatabaseManager.get_db()
    db.command('ping')

    # Read all documents grouped by collection
    collections = {}
    with path.open('r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entry = json_util.loads(line)
            col_name = entry['collection']
            doc = entry['document']
            collections.setdefault(col_name, []).append(doc)

    print(f"Snapshot contains records for {len(collections)} collections:")
    for name, docs in collections.items():
        print(f"  - {name}: {len(docs)} documents")

    confirm = input("Type 'RESTORE' to proceed with wiping current target collections and restoring: ")
    if confirm.strip() != 'RESTORE':
        print("Aborted.")
        return False

    for name, docs in collections.items():
        db[name].delete_many({})
        if docs:
            db[name].insert_many(docs)
        print(f"Restored {len(docs)} documents to {name}.")

    print("Restore complete.")
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Restore MongoDB snapshot from JSONL file.")
    parser.add_argument("snapshot", help="Path to JSONL snapshot file")
    args = parser.parse_args()
    restore(args.snapshot)
