#!/usr/bin/env python3
"""
Manual MongoDB backup without mongodump.
Uses pymongo and .env MONGO_URI. Run from project root:
  python scripts/backup_manual.py
Output: backup folder with one JSON file per collection (e.g. backups/mongodb_YYYYMMDD/).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
try:
    from dotenv import load_dotenv
    load_dotenv(_root / ".env")
except ImportError:
    pass

from pymongo import MongoClient
from bson import ObjectId

from database import _db_name_from_uri


def json_default(obj):
    if isinstance(obj, ObjectId):
        return {"$oid": str(obj)}
    if isinstance(obj, datetime):
        return {"$date": obj.isoformat()}
    raise TypeError(repr(obj) + " is not JSON serializable")


def main():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_security")
    if not uri or "localhost" in uri:
        print("Set MONGO_URI in .env to your Atlas connection string.")
        sys.exit(1)
    client = MongoClient(uri)
    db_name = _db_name_from_uri(uri)
    db = client[db_name]
    base = os.getenv("BACKUP_BASE_DIR", "").strip() or (os.environ.get("SystemDrive", "C:") + "\\backups")
    base_path = Path(base)
    out_dir = base_path / f"mongodb_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    collections = [
        "users", "devices", "alerts", "network_settings", "notification_preferences",
        "family_members", "family_invitations", "audit_logs", "incidents",
        "refresh_tokens", "groups", "heartbeats",
    ]
    for cname in collections:
        coll = db[cname]
        try:
            docs = list(coll.find({}))
        except Exception as e:
            print(f"[SKIP] {cname}: {e}")
            continue
        out_file = out_dir / f"{cname}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(docs, f, indent=2, default=json_default)
        print(f"[OK] {cname}: {len(docs)} documents -> {out_file.name}")
    print(f"[DONE] Backup in {out_dir}")
    client.close()


if __name__ == "__main__":
    main()
