#!/usr/bin/env python3
"""
Test script for Option 1 new features:
1. Dashboard Charts & Analytics
2. Device Grouping
3. Enhanced Notifications
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def get_auth_token(email="test@example.com", password="Test123!Test"):
    """Login and get auth token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            # Try signup if login fails
            print("Attempting signup...")
            signup_response = requests.post(
                f"{BASE_URL}/api/auth/signup",
                json={
                    "email": email,
                    "password": password,
                    "name": "Test User"
                }
            )
            if signup_response.status_code == 201:
                data = signup_response.json()
                return data.get("token")
    except Exception as e:
        print(f"Auth error: {e}")
    return None

def test_analytics_endpoints(token):
    """Test analytics API endpoints"""
    print("\n" + "="*60)
    print("TESTING: Dashboard Charts & Analytics")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test device stats
    print("\n1. Testing /api/analytics/devices/stats")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/devices/stats", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Success! Total devices: {data.get('total_devices', 0)}")
            print(f"   Status breakdown: {data.get('status_breakdown', {})}")
            print(f"   Type breakdown: {data.get('type_breakdown', {})}")
        else:
            print(f"   [FAIL] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    # Test alert trends
    print("\n2. Testing /api/analytics/alerts/trends?days=30")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/alerts/trends?days=30", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Success! Total alerts: {data.get('total_alerts', 0)}")
            print(f"   Severity breakdown: {data.get('severity_breakdown', {})}")
            print(f"   Resolution rate: {data.get('resolution_rate', 0)}%")
            print(f"   Timeline entries: {len(data.get('timeline', []))}")
        else:
            print(f"   [FAIL] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    # Test health metrics
    print("\n3. Testing /api/analytics/health/metrics")
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/health/metrics", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Success! Health score: {data.get('health_score', 0)}%")
            print(f"   Uptime: {data.get('uptime_percentage', 0)}%")
            print(f"   Alerts (24h): {data.get('alerts_last_24h', 0)}")
            print(f"   Top alerting devices: {len(data.get('top_alerting_devices', []))}")
        else:
            print(f"   [FAIL] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

def test_device_groups(token):
    """Test device grouping endpoints"""
    print("\n" + "="*60)
    print("TESTING: Device Grouping")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List groups
    print("\n1. Testing GET /api/groups")
    try:
        response = requests.get(f"{BASE_URL}/api/groups", headers=headers)
        if response.status_code == 200:
            groups = response.json()
            print(f"   [OK] Success! Found {len(groups)} groups")
            for group in groups:
                print(f"      - {group.get('name')} ({group.get('device_count', 0)} devices)")
        else:
            print(f"   [FAIL] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    # Create a test group
    print("\n2. Testing POST /api/groups (create group)")
    test_group_id = None
    try:
        response = requests.post(
            f"{BASE_URL}/api/groups",
            headers=headers,
            json={
                "name": "Test Group",
                "description": "Test group for feature testing",
                "color": "#3b82f6"
            }
        )
        if response.status_code == 201:
            group = response.json()
            test_group_id = group.get("id")
            print(f"   [OK] Success! Created group: {group.get('name')} (ID: {test_group_id})")
        else:
            print(f"   [FAIL] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    # Get devices to potentially add to group
    print("\n3. Testing device list for group assignment")
    try:
        response = requests.get(f"{BASE_URL}/api/devices?limit=5", headers=headers)
        if response.status_code == 200:
            data = response.json()
            devices = data.get("devices", [])
            print(f"   [OK] Found {len(devices)} devices")
            if devices and test_group_id:
                device_id = devices[0].get("id")
                # Try adding device to group
                add_response = requests.post(
                    f"{BASE_URL}/api/groups/{test_group_id}/devices/{device_id}",
                    headers=headers
                )
                if add_response.status_code == 200:
                    print(f"   [OK] Successfully added device to group")
                else:
                    print(f"   [WARN] Could not add device: {add_response.status_code}")
        else:
            print(f"   [WARN] No devices found to test grouping")
    except Exception as e:
        print(f"   [WARN] Error: {e}")
    
    # Clean up - delete test group
    if test_group_id:
        print("\n4. Testing DELETE /api/groups (cleanup)")
        try:
            response = requests.delete(f"{BASE_URL}/api/groups/{test_group_id}", headers=headers)
            if response.status_code == 200:
                print(f"   [OK] Successfully deleted test group")
            else:
                print(f"   [WARN] Could not delete test group: {response.status_code}")
        except Exception as e:
            print(f"   [WARN] Error: {e}")

def test_enhanced_notifications(token):
    """Test enhanced notification preferences"""
    print("\n" + "="*60)
    print("TESTING: Enhanced Notifications")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current preferences
    print("\n1. Testing GET /api/notification-preferences")
    try:
        response = requests.get(f"{BASE_URL}/api/notification-preferences/", headers=headers)
        if response.status_code == 200:
            prefs = response.json()
            print(f"   [OK] Success! Current preferences:")
            print(f"      - Quiet hours enabled: {prefs.get('quiet_hours_enabled', False)}")
            print(f"      - Quiet hours: {prefs.get('quiet_hours_start')} - {prefs.get('quiet_hours_end')}")
        else:
            print(f"   [FAIL] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    # Update preferences with quiet hours
    print("\n2. Testing PUT /api/notification-preferences (update with quiet hours)")
    try:
        response = requests.put(
            f"{BASE_URL}/api/notification-preferences/",
            headers=headers,
            json={
                "email_enabled": True,
                "sms_enabled": False,
                "whatsapp_enabled": False,
                "voice_enabled": False,
                "quiet_hours_enabled": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "07:00",
            }
        )
        if response.status_code == 200:
            prefs = response.json()
            print(f"   [OK] Success! Updated preferences:")
            print(f"      - Quiet hours: {prefs.get('quiet_hours_start')} - {prefs.get('quiet_hours_end')}")
        else:
            print(f"   [FAIL] Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

def main():
    print("="*60)
    print("Testing Option 1 New Features")
    print("="*60)
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get auth token
    print("\n[INFO] Authenticating...")
    token = get_auth_token()
    if not token:
        print("[ERROR] Could not authenticate. Please check:")
        print("   1. Server is running on http://localhost:8000")
        print("   2. You have a test user account")
        print("   3. Database is connected")
        return
    
    print("[OK] Authentication successful!")
    
    # Test all features
    test_analytics_endpoints(token)
    test_device_groups(token)
    test_enhanced_notifications(token)
    
    print("\n" + "="*60)
    print("[OK] Testing Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Open http://localhost:8000/dashboard in your browser")
    print("2. Check the Analytics & Charts tab")
    print("3. Try creating device groups")
    print("4. Test notification settings at /settings")

if __name__ == "__main__":
    main()
