#!/usr/bin/env python3
"""
Do-it-all deployment helper: generates secrets and prints step-by-step
instructions to make the IoT Security web app live (Railway or Render).
Run: python scripts/do_it_all_deploy.py
"""
import os
import secrets
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def generate_jwt_secret():
    return secrets.token_urlsafe(32)


def main():
    jwt_secret = generate_jwt_secret()
    print()
    print("=" * 70)
    print("  IoT SECURITY PLATFORM – MAKE THE WEB APP LIVE")
    print("=" * 70)
    print()
    print("STEP 1 – MongoDB Atlas (if you don't have it)")
    print("-" * 50)
    print("  1. Go to https://www.mongodb.com/cloud/atlas")
    print("  2. Create account -> Create free cluster")
    print("  3. Database Access -> Add user (username + password)")
    print("  4. Network Access -> Add 0.0.0.0/0 (or your host IP)")
    print("  5. Connect -> Drivers -> Copy connection string")
    print("     Example: mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/iot_security")
    print()
    print("STEP 2 – Push code to GitHub")
    print("-" * 50)
    print("  Ensure your project is in a GitHub repo (git push origin main).")
    print()
    print("STEP 3 – Deploy to Railway (easiest)")
    print("-" * 50)
    print("  1. Go to https://railway.app -> Sign in with GitHub")
    print("  2. New Project -> Deploy from GitHub repo -> Select your repo")
    print("  3. After first deploy: Settings -> Networking -> Generate domain")
    print("     You'll get a URL like: https://your-app.up.railway.app")
    print("  4. Variables -> Add these (replace placeholders):")
    print()
    print("     MONGO_URI=<your Atlas connection string>")
    print(f"     JWT_SECRET={jwt_secret}")
    print("     PORT=8000")
    print("     APP_ENV=production")
    print("     APP_BASE_URL=https://YOUR-RAILWAY-URL.up.railway.app")
    print("     CORS_ORIGINS=https://YOUR-RAILWAY-URL.up.railway.app")
    print()
    print("  5. Replace YOUR-RAILWAY-URL with your actual domain from step 3.")
    print("  6. Redeploy if needed. Open the URL -> signup/login should work.")
    print()
    print("STEP 4 – Optional: email (Gmail)")
    print("-" * 50)
    print("  In Railway Variables, add:")
    print("    SMTP_HOST=smtp.gmail.com")
    print("    SMTP_PORT=587")
    print("    SMTP_USER=your@gmail.com")
    print("    SMTP_PASSWORD=<Gmail App Password>")
    print("    FROM_EMAIL=your@gmail.com")
    print("  (Gmail: enable 2FA, then create App Password at myaccount.google.com)")
    print()
    print("STEP 4 (alt) – Deploy to Render")
    print("-" * 50)
    print("  1. Go to https://render.com -> Sign in with GitHub")
    print("  2. New + -> Web Service -> Connect repo")
    print("  3. Build: pip install -r requirements.txt")
    print("  4. Start: uvicorn main:app --host 0.0.0.0 --port $PORT")
    print("  5. Add the same variables as above; set APP_BASE_URL and CORS_ORIGINS to your Render URL.")
    print()
    print("=" * 70)
    print("  Copy JWT_SECRET above into your host's environment variables.")
    print("  Full checklist: DEPLOYMENT_CHECKLIST.md | docs/MAKE_APP_LIVE.md")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
