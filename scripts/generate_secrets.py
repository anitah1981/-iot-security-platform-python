#!/usr/bin/env python3
"""
Generate secure secrets for production deployment
"""
import secrets
import sys

def generate_jwt_secret():
    """Generate a secure JWT secret (32+ bytes)"""
    return secrets.token_urlsafe(32)

def generate_mfa_issuer():
    """Default MFA issuer name"""
    return "IoT Security Platform"

def main():
    print("=" * 60)
    print("SECURE SECRET GENERATOR")
    print("=" * 60)
    print()
    print("Copy these to your .env file for production:")
    print()
    
    jwt_secret = generate_jwt_secret()
    print(f"JWT_SECRET={jwt_secret}")
    print()
    
    print("Recommended production settings:")
    print(f"APP_ENV=production")
    print(f"FORCE_HTTPS=true")
    print(f"ENABLE_HSTS=true")
    print(f"JWT_EXPIRES_MINUTES=60")
    print(f"REFRESH_EXPIRES_DAYS=7")
    print(f"RATE_LIMIT_DEFAULT=100/minute")
    print()
    
    print("SECURITY NOTES:")
    print("  - Store JWT_SECRET securely (use secrets manager in production)")
    print("  - Never commit secrets to git")
    print("  - Rotate JWT_SECRET if compromised (invalidates all sessions)")
    print("  - Set ALLOWED_HOSTS to your production domain(s)")
    print("  - Set CORS_ORIGINS to your frontend domain(s)")
    print()

if __name__ == "__main__":
    main()
