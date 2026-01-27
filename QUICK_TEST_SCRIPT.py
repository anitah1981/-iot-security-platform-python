#!/usr/bin/env python3
"""
Quick test script to verify all imports and basic functionality
"""
import sys
import asyncio

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        import main
        print("[OK] main.py imports OK")
    except Exception as e:
        print(f"[FAIL] main.py import failed: {e}")
        return False
    
    try:
        from routes import auth, devices, alerts, groups, audit, incidents
        print("[OK] All route modules import OK")
    except Exception as e:
        print(f"[FAIL] Route import failed: {e}")
        return False
    
    try:
        from services import audit_logger, incident_correlator, notification_service
        print("[OK] All service modules import OK")
    except Exception as e:
        print(f"[FAIL] Service import failed: {e}")
        return False
    
    try:
        from models import UserResponse, DeviceResponse, AlertResponse, IncidentResponse, AuditLogEntry
        print("[OK] All models import OK")
    except Exception as e:
        print(f"[FAIL] Model import failed: {e}")
        return False
    
    try:
        from middleware import plan_limits, security
        print("[OK] All middleware imports OK")
    except Exception as e:
        print(f"[FAIL] Middleware import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    try:
        import asyncio
        from database import get_database
        
        async def test():
            try:
                db = await get_database()
                # Try a simple operation
                result = await db.users.count_documents({})
                print(f"[OK] Database connection OK (found {result} users)")
                return True
            except Exception as e:
                print(f"[FAIL] Database connection failed: {e}")
                return False
        
        return asyncio.run(test())
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def main():
    print("=" * 50)
    print("IoT Security Platform - Quick Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        sys.exit(1)
    
    # Test database (optional - may fail if not configured)
    try:
        test_database_connection()
    except Exception as e:
        print(f"\n⚠ Database test skipped: {e}")
        print("   (This is OK if MongoDB is not configured)")
    
    print("\n" + "=" * 50)
    print("[SUCCESS] All import tests passed!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Start server: python -m uvicorn main:app --reload --port 8000")
    print("2. Test in browser: http://localhost:8000")
    print("3. Test mobile app: cd mobile && npm start")
    print("\nReady to deploy!")

if __name__ == "__main__":
    main()
