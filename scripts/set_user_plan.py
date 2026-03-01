#!/usr/bin/env python3
"""Set user plan/role by email. Uses MONGO_URI from .env."""
import argparse, os, sys
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
    ap = argparse.ArgumentParser()
    ap.add_argument("email")
    ap.add_argument("--plan", choices=["free","pro","business"])
    ap.add_argument("--role", choices=["consumer","user","business","admin"])
    ap.add_argument("--plan-override", choices=["pro","business"], help="Give full plan access without Stripe (for beta testers)")
    ap.add_argument("--allow-local", action="store_true", help="Allow running against localhost MongoDB")
    args = ap.parse_args()
    if not (args.plan or args.role or args.plan_override):
        print("Use at least one of: --plan, --role, --plan-override"); sys.exit(1)
    uri = os.getenv("MONGO_URI") or "mongodb://localhost:27017/iot_security"
    if "localhost" in uri and not args.allow_local:
        print("Set MONGO_URI in .env (or use --allow-local to run against local MongoDB)"); sys.exit(1)
    db = MongoClient(uri)[_db_name_from_uri(uri)]
    user = db.users.find_one({"email": args.email.strip().lower()})
    if not user:
        print("User not found"); sys.exit(1)
    updates = {}
    if args.plan: updates["plan"] = args.plan
    if args.role: updates["role"] = args.role
    if args.plan_override: updates["plan_override"] = args.plan_override
    db.users.update_one({"_id": user["_id"]}, {"$set": updates})
    print("Updated", args.email, updates)

if __name__ == "__main__":
    main()
