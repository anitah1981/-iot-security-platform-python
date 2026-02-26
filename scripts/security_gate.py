#!/usr/bin/env python3
"""Executable security release gate. Run before deploy or in CI. See docs/SECURITY_CHECKLIST.md."""
import os
import sys
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass


def main():
    failed = []
    jwt = os.getenv("JWT_SECRET", "")
    if not jwt or jwt.strip() in ("change-me-in-production", "changeme", "secret"):
        failed.append("JWT_SECRET must be set")
    env = os.getenv("APP_ENV", "local").lower()
    if env == "production":
        m = os.getenv("MONGO_URI", "")
        if not m or "localhost" in m:
            failed.append("MONGO_URI not localhost in prod")
        if not os.getenv("APP_BASE_URL", "").strip():
            failed.append("APP_BASE_URL required")
        if not os.getenv("CORS_ORIGINS", "").strip():
            failed.append("CORS_ORIGINS required")
    if failed:
        for f in failed:
            print("[FAIL]", f)
        return 1
    print("Security gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
