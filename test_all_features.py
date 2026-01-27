#!/usr/bin/env python3
"""
Comprehensive Feature Testing Script
Tests all features after digest removal and recent additions
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_test(name: str, status: str = "TESTING"):
    """Print test status"""
    icons = {
        "PASS": "[OK]",
        "FAIL": "[FAIL]",
        "WARN": "[WARN]",
        "TESTING": "[TEST]"
    }
    print(f"{icons.get(status, '[TEST]')} {name}")

def print_success(msg: str):
    """Print success message"""
    print(f"   [OK] {msg}")

def print_error(msg: str):
    """Print error message"""
    print(f"   [FAIL] {msg}")

def print_warning(msg: str):
    """Print warning message"""
    print(f"   [WARN] {msg}")

def get_auth_token(email: str, password: str) -> Optional[str]:
    """Get authentication token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

def test_quiet_hours(token: str) -> bool:
    """Test Quiet Hours functionality"""
    print_header("TEST 1: Quiet Hours Functionality")
    headers = {"Authorization": f"Bearer {token}"}
    all_passed = True
    
    try:
        # Get current preferences
        print_test("Getting current notification preferences")
        response = requests.get(f"{BASE_URL}/api/notification-preferences/", headers=headers)
        if response.status_code != 200:
            print_error(f"Failed to get preferences: {response.status_code}")
            return False
        
        prefs = response.json()
        print_success("Retrieved preferences")
        
        # Test 1.1: Enable quiet hours
        print_test("Enabling quiet hours")
        update_data = {
            "email_enabled": prefs.get("email_enabled", True),
            "sms_enabled": prefs.get("sms_enabled", False),
            "whatsapp_enabled": prefs.get("whatsapp_enabled", False),
            "voice_enabled": prefs.get("voice_enabled", False),
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/notification-preferences/",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            updated_prefs = response.json()
            if updated_prefs.get("quiet_hours_enabled") == True:
                print_success("Quiet hours enabled successfully")
                test_results["passed"].append("Quiet Hours: Enable")
            else:
                print_error("Quiet hours not enabled in response")
                test_results["failed"].append("Quiet Hours: Enable")
                all_passed = False
        else:
            print_error(f"Failed to update preferences: {response.status_code}")
            test_results["failed"].append("Quiet Hours: Enable")
            all_passed = False
        
        # Test 1.2: Verify settings persist
        print_test("Verifying settings persist")
        response = requests.get(f"{BASE_URL}/api/notification-preferences/", headers=headers)
        if response.status_code == 200:
            saved_prefs = response.json()
            if (saved_prefs.get("quiet_hours_enabled") == True and
                saved_prefs.get("quiet_hours_start") == "22:00" and
                saved_prefs.get("quiet_hours_end") == "07:00"):
                print_success("Settings persist correctly")
                test_results["passed"].append("Quiet Hours: Persistence")
            else:
                print_error("Settings did not persist correctly")
                test_results["failed"].append("Quiet Hours: Persistence")
                all_passed = False
        else:
            print_error("Failed to retrieve saved preferences")
            all_passed = False
        
        # Test 1.3: Verify no digest fields
        print_test("Verifying digest fields removed")
        if "digest_enabled" not in saved_prefs and "digest_frequency" not in saved_prefs:
            print_success("Digest fields correctly removed")
            test_results["passed"].append("Quiet Hours: No Digest Fields")
        else:
            print_warning("Digest fields still present in response")
            test_results["warnings"].append("Quiet Hours: Digest fields may still exist")
        
        # Test 1.4: Disable quiet hours
        print_test("Disabling quiet hours")
        update_data["quiet_hours_enabled"] = False
        response = requests.put(
            f"{BASE_URL}/api/notification-preferences/",
            headers=headers,
            json=update_data
        )
        if response.status_code == 200:
            print_success("Quiet hours disabled successfully")
            test_results["passed"].append("Quiet Hours: Disable")
        else:
            print_error("Failed to disable quiet hours")
            all_passed = False
        
    except Exception as e:
        print_error(f"Test error: {e}")
        test_results["failed"].append(f"Quiet Hours: {str(e)}")
        all_passed = False
    
    return all_passed

def test_device_grouping(token: str) -> bool:
    """Test Device Grouping functionality"""
    print_header("TEST 2: Device Grouping")
    headers = {"Authorization": f"Bearer {token}"}
    all_passed = True
    test_group_id = None
    
    try:
        # Test 2.1: Get existing groups
        print_test("Getting existing groups")
        response = requests.get(f"{BASE_URL}/api/groups", headers=headers)
        if response.status_code == 200:
            groups = response.json()
            print_success(f"Retrieved {len(groups)} existing groups")
            test_results["passed"].append("Device Grouping: List Groups")
        else:
            print_error(f"Failed to get groups: {response.status_code}")
            test_results["failed"].append("Device Grouping: List Groups")
            all_passed = False
            return False
        
        # Test 2.2: Create a new group
        print_test("Creating a new test group")
        group_data = {
            "name": f"Test Group {datetime.now().strftime('%H%M%S')}",
            "description": "Automated test group",
            "color": "#3b82f6"
        }
        response = requests.post(
            f"{BASE_URL}/api/groups",
            headers=headers,
            json=group_data
        )
        
        if response.status_code == 201:
            created_group = response.json()
            test_group_id = created_group.get("id") or created_group.get("_id")
            print_success(f"Group created with ID: {test_group_id}")
            test_results["passed"].append("Device Grouping: Create Group")
        else:
            print_error(f"Failed to create group: {response.status_code} - {response.text}")
            test_results["failed"].append("Device Grouping: Create Group")
            all_passed = False
            return False
        
        # Test 2.3: Get devices to assign
        print_test("Getting devices for assignment")
        response = requests.get(f"{BASE_URL}/api/devices", headers=headers)
        if response.status_code == 200:
            devices = response.json()
            if devices and len(devices) > 0:
                test_device_id = devices[0].get("id") or devices[0].get("_id")
                print_success(f"Found {len(devices)} devices, using first device")
                
                # Test 2.4: Assign device to group
                print_test("Assigning device to group")
                response = requests.post(
                    f"{BASE_URL}/api/groups/{test_group_id}/devices/{test_device_id}",
                    headers=headers
                )
                if response.status_code in [200, 201]:
                    print_success("Device assigned to group")
                    test_results["passed"].append("Device Grouping: Assign Device")
                else:
                    print_warning(f"Device assignment returned: {response.status_code}")
                    test_results["warnings"].append("Device Grouping: Assign Device")
            else:
                print_warning("No devices found to assign")
                test_results["warnings"].append("Device Grouping: No devices available")
        else:
            print_warning(f"Failed to get devices: {response.status_code}")
            test_results["warnings"].append("Device Grouping: Get Devices")
        
        # Test 2.5: Delete test group
        if test_group_id:
            print_test("Deleting test group")
            response = requests.delete(
                f"{BASE_URL}/api/groups/{test_group_id}",
                headers=headers
            )
            if response.status_code in [200, 204]:
                print_success("Test group deleted")
                test_results["passed"].append("Device Grouping: Delete Group")
            else:
                print_error(f"Failed to delete group: {response.status_code}")
                test_results["failed"].append("Device Grouping: Delete Group")
                all_passed = False
        
    except Exception as e:
        print_error(f"Test error: {e}")
        test_results["failed"].append(f"Device Grouping: {str(e)}")
        all_passed = False
    
    return all_passed

def test_dashboard_charts(token: str) -> bool:
    """Test Dashboard Charts & Analytics"""
    print_header("TEST 3: Dashboard Charts & Analytics")
    headers = {"Authorization": f"Bearer {token}"}
    all_passed = True
    
    try:
        # Test 3.1: Device stats
        print_test("Testing device statistics endpoint")
        response = requests.get(f"{BASE_URL}/api/analytics/devices/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print_success("Device stats retrieved")
            test_results["passed"].append("Charts: Device Stats")
        else:
            print_error(f"Failed to get device stats: {response.status_code}")
            test_results["failed"].append("Charts: Device Stats")
            all_passed = False
        
        # Test 3.2: Alert trends with different date ranges
        print_test("Testing alert trends with date ranges")
        for days in [7, 30, 90]:
            response = requests.get(
                f"{BASE_URL}/api/analytics/alerts/trends?days={days}",
                headers=headers
            )
            if response.status_code == 200:
                trends = response.json()
                print_success(f"Alert trends for {days} days retrieved")
            else:
                print_error(f"Failed to get trends for {days} days: {response.status_code}")
                all_passed = False
        
        test_results["passed"].append("Charts: Alert Trends")
        
        # Test 3.3: Health metrics
        print_test("Testing health metrics endpoint")
        response = requests.get(f"{BASE_URL}/api/analytics/health/metrics", headers=headers)
        if response.status_code == 200:
            metrics = response.json()
            print_success("Health metrics retrieved")
            test_results["passed"].append("Charts: Health Metrics")
        else:
            print_error(f"Failed to get health metrics: {response.status_code}")
            test_results["failed"].append("Charts: Health Metrics")
            all_passed = False
        
    except Exception as e:
        print_error(f"Test error: {e}")
        test_results["failed"].append(f"Charts: {str(e)}")
        all_passed = False
    
    return all_passed

def test_notification_channels(token: str) -> bool:
    """Test Notification Channels"""
    print_header("TEST 4: Notification Channels")
    headers = {"Authorization": f"Bearer {token}"}
    all_passed = True
    
    try:
        # Test 4.1: Test email notification
        print_test("Testing email notification")
        response = requests.post(
            f"{BASE_URL}/api/notification-preferences/test/email",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_success("Email test notification sent")
            test_results["passed"].append("Notifications: Email Test")
        elif response.status_code == 400:
            print_warning("Email notifications may be disabled")
            test_results["warnings"].append("Notifications: Email may be disabled")
        else:
            print_error(f"Email test failed: {response.status_code}")
            test_results["failed"].append("Notifications: Email Test")
            all_passed = False
        
        # Note: SMS, WhatsApp, Voice tests would require phone numbers configured
        # Skipping those for now as they may not be set up
        
    except Exception as e:
        print_error(f"Test error: {e}")
        test_results["failed"].append(f"Notifications: {str(e)}")
        all_passed = False
    
    return all_passed

def test_general_functionality(token: str) -> bool:
    """Test General Functionality"""
    print_header("TEST 5: General Functionality")
    headers = {"Authorization": f"Bearer {token}"}
    all_passed = True
    
    try:
        # Test 5.1: Get devices
        print_test("Testing device list endpoint")
        response = requests.get(f"{BASE_URL}/api/devices", headers=headers)
        if response.status_code == 200:
            devices = response.json()
            print_success(f"Retrieved {len(devices)} devices")
            test_results["passed"].append("General: Get Devices")
        else:
            print_error(f"Failed to get devices: {response.status_code}")
            all_passed = False
        
        # Test 5.2: Get alerts
        print_test("Testing alert list endpoint")
        response = requests.get(f"{BASE_URL}/api/alerts", headers=headers)
        if response.status_code == 200:
            alerts_data = response.json()
            alerts = alerts_data.get("alerts", []) if isinstance(alerts_data, dict) else alerts_data
            print_success(f"Retrieved {len(alerts)} alerts")
            test_results["passed"].append("General: Get Alerts")
        else:
            print_error(f"Failed to get alerts: {response.status_code}")
            all_passed = False
        
        # Test 5.3: Get current user
        print_test("Testing current user endpoint")
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            user = response.json()
            print_success(f"Retrieved user: {user.get('email', 'Unknown')}")
            test_results["passed"].append("General: Get Current User")
        else:
            print_error(f"Failed to get current user: {response.status_code}")
            all_passed = False
        
    except Exception as e:
        print_error(f"Test error: {e}")
        test_results["failed"].append(f"General: {str(e)}")
        all_passed = False
    
    return all_passed

def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
    
    print(f"\n[RESULTS]")
    print(f"   [OK] Passed:  {len(test_results['passed'])}")
    print(f"   [FAIL] Failed:  {len(test_results['failed'])}")
    print(f"   [WARN] Warnings: {len(test_results['warnings'])}")
    print(f"   [INFO] Total:   {total_tests}")
    
    if test_results["passed"]:
        print(f"\n[OK] Passed Tests:")
        for test in test_results["passed"]:
            print(f"   - {test}")
    
    if test_results["failed"]:
        print(f"\n[FAIL] Failed Tests:")
        for test in test_results["failed"]:
            print(f"   - {test}")
    
    if test_results["warnings"]:
        print(f"\n[WARN] Warnings:")
        for test in test_results["warnings"]:
            print(f"   - {test}")
    
    print("\n" + "="*70)
    
    if len(test_results["failed"]) == 0:
        print("[SUCCESS] All critical tests passed!")
        return True
    else:
        print("[WARNING] Some tests failed. Please review the errors above.")
        return False

def main():
    """Main test function"""
    print_header("IoT Security Platform - Comprehensive Feature Testing")
    print("\nThis script will test:")
    print("  1. Quiet Hours functionality")
    print("  2. Device Grouping")
    print("  3. Dashboard Charts & Analytics")
    print("  4. Notification Channels")
    print("  5. General Functionality")
    
    # Get credentials from environment or command line
    import os
    email = os.getenv("TEST_EMAIL") or (sys.argv[1] if len(sys.argv) > 1 else None)
    password = os.getenv("TEST_PASSWORD") or (sys.argv[2] if len(sys.argv) > 2 else None)
    
    if not email or not password:
        print("\nUsage:")
        print("  python test_all_features.py <email> <password>")
        print("  OR set environment variables:")
        print("    TEST_EMAIL=your@email.com")
        print("    TEST_PASSWORD=yourpassword")
        print("\nExample:")
        print("  python test_all_features.py test@example.com Test123!Test")
        sys.exit(1)
    
    # Get auth token
    print_header("Authentication")
    print_test("Logging in...")
    token = get_auth_token(email, password)
    
    if not token:
        print_error("Failed to authenticate. Please check your credentials.")
        sys.exit(1)
    
    print_success("Authentication successful")
    
    # Run all tests
    results = []
    results.append(("Quiet Hours", test_quiet_hours(token)))
    results.append(("Device Grouping", test_device_grouping(token)))
    results.append(("Dashboard Charts", test_dashboard_charts(token)))
    results.append(("Notification Channels", test_notification_channels(token)))
    results.append(("General Functionality", test_general_functionality(token)))
    
    # Print summary
    all_passed = print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
