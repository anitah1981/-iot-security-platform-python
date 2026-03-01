#!/usr/bin/env python3
"""Set all devices to Offline only when missed heartbeats (reduces false positives). Uses MONGO_URI from .env."""
import os
import sys
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
from database import _db_name_from_uri


def main():
    uri = os.getenv("MONGO_URI") or "mongodb://localhost:27017/iot_security"
    if "localhost" in uri:
        print("Set MONGO_URI in .env (or use local MongoDB); then run again.")
        sys.exit(1)
    db = MongoClient(uri)[_db_name_from_uri(uri)]
    result = db.devices.update_many(
        {"isDeleted": {"$ne": True}},
        {"$set": {"offlineOnlyWhenMissedHeartbeats": True}},
    )
    print(f"Updated {result.modified_count} device(s) to Offline only when missed heartbeats.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
