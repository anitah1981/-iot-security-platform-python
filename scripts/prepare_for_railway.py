#!/usr/bin/env python3
"""
Prepare for Railway deployment - generates all env vars you need to paste into Railway.
Run: python scripts/prepare_for_railway.py
Then follow the printed instructions.
"""
import secrets
import sys

def generate_jwt_secret():
    return secrets.token_urlsafe(32)

def main():
    jwt_secret = generate_jwt_secret()
    
    print()
    print("=" * 70)
    print("  RAILWAY DEPLOYMENT - ENVIRONMENT VARIABLES")
    print("=" * 70)
    print()
    print("Copy these into Railway -> Your Service -> Variables:")
    print()
    print("MONGO_URI=<paste your MongoDB Atlas connection string here>")
    print(f"JWT_SECRET={jwt_secret}")
    print("PORT=8000")
    print("APP_ENV=production")
    print("APP_BASE_URL=https://YOUR-RAILWAY-URL.up.railway.app")
    print("CORS_ORIGINS=https://YOUR-RAILWAY-URL.up.railway.app")
    print()
    print("IMPORTANT:")
    print("  1. Replace <paste your MongoDB Atlas connection string here> with your actual MONGO_URI")
    print("  2. After Railway generates your domain, replace YOUR-RAILWAY-URL with the actual domain")
    print("  3. Then redeploy if needed")
    print()
    print("Optional (for email notifications):")
    print("SMTP_HOST=smtp.gmail.com")
    print("SMTP_PORT=587")
    print("SMTP_USER=your@gmail.com")
    print("SMTP_PASSWORD=<Gmail App Password>")
    print("FROM_EMAIL=your@gmail.com")
    print()
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
