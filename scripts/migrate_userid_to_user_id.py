#!/usr/bin/env python3
"""
Backfill userId -> user_id and createdAt -> created_at.

Run this once against your production MongoDB after deploying the
compatibility code. Safe to run multiple times; it only updates docs
missing the new fields.
"""
import os

from pymongo import MongoClient

from database import _db_name_from_uri


def get_db():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_security")
    client = MongoClient(uri)
    db_name = _db_name_from_uri(uri)
    return client[db_name]


def backfill_user_id(db, collection_name):
    coll = db[collection_name]
    cursor = coll.find(
        {"userId": {"$exists": True}, "user_id": {"$exists": False}},
        {"userId": 1},
    )
    count = 0
    for doc in cursor:
        coll.update_one({"_id": doc["_id"]}, {"$set": {"user_id": doc["userId"]}})
        count += 1
    print(f"[{collection_name}] backfilled user_id from userId on {count} documents")


def backfill_created_at(db, collection_name):
    coll = db[collection_name]
    cursor = coll.find(
        {"createdAt": {"$exists": True}, "created_at": {"$exists": False}},
        {"createdAt": 1},
    )
    count = 0
    for doc in cursor:
        coll.update_one(
            {"_id": doc["_id"]},
            {"$set": {"created_at": doc["createdAt"]}},
        )
        count += 1
    print(f"[{collection_name}] backfilled created_at from createdAt on {count} documents")


COLLECTIONS = [
    "devices",
    "alerts",
    "network_settings",
    "notification_preferences",
    "family_members",
    "audit_logs",
    "incidents",
]


def main():
    db = get_db()
    print(f"[MIGRATION] Connected to DB: {db.name}")
    for name in COLLECTIONS:
        backfill_user_id(db, name)
        backfill_created_at(db, name)
    print("[MIGRATION] Completed userId/user_id backfill.")


if __name__ == "__main__":
    main()

