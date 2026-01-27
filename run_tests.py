#!/usr/bin/env python3
"""
Quick Test Runner - Tests all features automatically
Uses default test credentials or environment variables
"""

import requests
import sys
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Default test credentials (can be overridden with env vars)
TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "Test123!Test")

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def test(name, func):
    """Run a test and report results"""
    print(f"\n[TEST] {name}")
    try:
        result = func()
        if result:
            print(f"[OK] {name} - PASSED")
            return True
        else:
            print(f"[FAIL] {name} - FAILED")
            return False
    except Exception as e:
        print(f"[FAIL] {name} - ERROR: {e}")
        return False

def get_token():
    """Get authentication token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        print(f"[WARN] Login failed, trying signup...")
        # Try signup
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": "Test User"},
            timeout=5
        )
        if response.status_code == 201:
            data = response.json()
            return data.get("access_token") or data.get("token")
    except Exception as e:
        print(f"[ERROR] Auth error: {e}")
    return None

def test_quiet_hours(token):
    """Test quiet hours"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Enable quiet hours
    response = requests.put(
        f"{BASE_URL}/api/notification-preferences/",
        headers=headers,
        json={
            "email_enabled": True,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00"
        }
    )
    if response.status_code != 200:
        return False
    
    # Verify it saved
    response = requests.get(f"{BASE_URL}/api/notification-preferences/", headers=headers)
    if response.status_code != 200:
        return False
    
    prefs = response.json()
    if not prefs.get("quiet_hours_enabled"):
        return False
    
    # Check no digest fields
    if "digest_enabled" in prefs:
        print("[WARN] Digest fields still present")
    
    return True

def test_device_grouping(token):
    """Test device grouping"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create group
    response = requests.post(
        f"{BASE_URL}/api/groups",
        headers=headers,
        json={
            "name": f"Test Group {datetime.now().strftime('%H%M%S')}",
            "description": "Test",
            "color": "#3b82f6"
        }
    )
    if response.status_code not in [200, 201]:
        return False
    
    group = response.json()
    group_id = group.get("id") or group.get("_id")
    
    # Get groups
    response = requests.get(f"{BASE_URL}/api/groups", headers=headers)
    if response.status_code != 200:
        return False
    
    # Delete group
    if group_id:
        requests.delete(f"{BASE_URL}/api/groups/{group_id}", headers=headers)
    
    return True

def test_charts(token):
    """Test dashboard charts"""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/analytics/devices/stats",
        "/api/analytics/alerts/trends?days=30",
        "/api/analytics/health/metrics"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        if response.status_code != 200:
            return False
    
    return True

def test_notifications(token):
    """Test notifications"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/api/notification-preferences/test/email",
        headers=headers
    )
    # 200 = success, 400 = disabled (acceptable)
    return response.status_code in [200, 400]

def test_general(token):
    """Test general endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/devices",
        "/api/alerts",
        "/api/auth/me"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        if response.status_code != 200:
            return False
    
    return True

def main():
    print_header("IoT Security Platform - Automated Testing")
    print(f"\nUsing credentials: {TEST_EMAIL}")
    print(f"Server: {BASE_URL}\n")
    
    # Check server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print("[ERROR] Server is not responding correctly")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Cannot connect to server: {e}")
        print(f"[INFO] Make sure server is running at {BASE_URL}")
        sys.exit(1)
    
    # Get token
    print("[INFO] Authenticating...")
    token = get_token()
    if not token:
        print("[ERROR] Authentication failed")
        print("[INFO] You may need to:")
        print("  1. Create a test account, OR")
        print("  2. Set TEST_EMAIL and TEST_PASSWORD environment variables")
        sys.exit(1)
    print("[OK] Authenticated")
    
    # Run tests
    results = []
    results.append(("Quiet Hours", test_quiet_hours(token)))
    results.append(("Device Grouping", test_device_grouping(token)))
    results.append(("Dashboard Charts", test_charts(token)))
    results.append(("Notifications", test_notifications(token)))
    results.append(("General Endpoints", test_general(token)))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\n[RESULTS] {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("[WARNING] Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
