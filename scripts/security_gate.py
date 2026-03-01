#!/usr/bin/env python3
"""Executable security release gate. Run before deploy or in CI. See docs/SECURITY_CHECKLIST.md and docs/LIVE_VERIFICATION_CHECKLIST.md."""
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
    env = os.getenv("APP_ENV", "local").lower()

    # JWT: require set and not a placeholder; length 32+ only in production
    jwt = (os.getenv("JWT_SECRET") or "").strip()
    forbidden = ("change-me-in-production", "changeme", "secret", "your-super-secret-key-change-in-production", "your_secret")
    if not jwt or jwt in forbidden:
        failed.append("JWT_SECRET must be set and not a placeholder")
    elif env == "production" and len(jwt) < 32:
        failed.append("JWT_SECRET should be at least 32 characters for production")

    # Production-only checks
    if env == "production":
        m = os.getenv("MONGO_URI", "")
        if not m or "localhost" in m.lower():
            failed.append("MONGO_URI must point to production DB (not localhost)")
        if not (os.getenv("APP_BASE_URL") or "").strip():
            failed.append("APP_BASE_URL required (e.g. https://your-domain.com)")
        cors = (os.getenv("CORS_ORIGINS") or "").strip()
        if not cors:
            failed.append("CORS_ORIGINS required")
        elif cors == "*":
            failed.append("CORS_ORIGINS should not be * in production; use your domain(s)")
        # Email: required for verification/reset reliability
        if not all([os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"), os.getenv("FROM_EMAIL")]):
            failed.append("SMTP_USER, SMTP_PASSWORD, FROM_EMAIL required for real email delivery (verification/reset)")
        # Stripe: if taking payments, live keys and webhook
        sk = os.getenv("STRIPE_SECRET_KEY", "")
        if sk and sk.startswith("sk_test_") and os.getenv("STRIPE_LIVE_MODE", "").lower() == "true":
            failed.append("STRIPE_SECRET_KEY should be sk_live_ when STRIPE_LIVE_MODE=true")

    if failed:
        for f in failed:
            print("[FAIL]", f)
        print("\nFix the above, then run again. For live checks (HTTPS, headers, rate limit), see docs/LIVE_VERIFICATION_CHECKLIST.md")
        return 1
    print("Security gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
