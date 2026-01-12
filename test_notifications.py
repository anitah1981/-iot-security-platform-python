"""
Test Notification System - Quick verification script
Run this after setting up your .env file to test email notifications
"""

import requests
import sys
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
TEST_USER_EMAIL = "anitah1981@gmail.com"  # ✅ Your email
TEST_USER_PASSWORD = "Test123!"           # Change if you want a different password

def print_step(step, message):
    """Print colored step messages"""
    print(f"\n{'='*60}")
    print(f"  Step {step}: {message}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def main():
    print("\n🚀 IoT Security Platform - Notification Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check server health
    print_step(1, "Checking server health")
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is running!")
            print_info(f"Response: {response.json()}")
        else:
            print_error(f"Server returned status {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running?")
        print_info("Run: uvicorn main:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)
    
    # Step 2: Create test user (or login if exists)
    print_step(2, "Setting up test user")
    signup_response = requests.post(
        f"{API_BASE}/api/auth/signup",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test User"
        }
    )
    
    if signup_response.status_code == 201:
        print_success("New user created!")
        token = signup_response.json()["token"]
    elif signup_response.status_code in [400, 409]:
        print_info("User already exists, logging in...")
        login_response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        if login_response.status_code == 200:
            print_success("Logged in successfully!")
            token = login_response.json()["token"]
        else:
            print_error(f"Login failed: {login_response.text}")
            sys.exit(1)
    else:
        print_error(f"Signup failed (status {signup_response.status_code}): {signup_response.text}")
        print_info("Trying to login instead...")
        login_response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        if login_response.status_code == 200:
            print_success("Logged in successfully!")
            token = login_response.json()["token"]
        else:
            print_error(f"Login also failed: {login_response.text}")
            sys.exit(1)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Set notification preferences
    print_step(3, "Configuring notification preferences")
    prefs = {
        "emailEnabled": True,
        "smsEnabled": False,  # Set to True if you have Twilio configured
        "whatsappEnabled": False,
        "voiceEnabled": False,
        "emailSeverities": ["low", "medium", "high", "critical"],
        "smsSeverities": ["high", "critical"],
        "quietHoursEnabled": False
    }
    
    prefs_response = requests.put(
        f"{API_BASE}/api/notification-preferences",
        json=prefs,
        headers=headers
    )
    
    if prefs_response.status_code in [200, 201]:
        print_success("Notification preferences updated!")
    else:
        print_error(f"Failed to update preferences: {prefs_response.text}")
    
    # Step 4: Create test device
    print_step(4, "Creating test device")
    import random
    test_ip = f"192.168.1.{random.randint(100, 254)}"
    device_response = requests.post(
        f"{API_BASE}/api/devices",
        json={
            "device_id": "test-camera-001",
            "name": "Test Security Camera",
            "type": "Camera",
            "ip_address": test_ip
        },
        headers=headers
    )
    
    if device_response.status_code == 201:
        device_data = device_response.json()
        device_id = device_data.get("_id") or device_data.get("id")
        print_success(f"Device created! ID: {device_id}")
    elif device_response.status_code == 400 and "already exists" in device_response.text:
        print_info("Device already exists, fetching it...")
        devices_response = requests.get(f"{API_BASE}/api/devices", headers=headers)
        devices = devices_response.json()
        test_device = next((d for d in devices if d.get("device_id") == "test-camera-001"), None)
        if test_device:
            device_id = test_device.get("_id") or test_device.get("id")
            print_success(f"Using existing device! ID: {device_id}")
        else:
            print_error("Could not find test device")
            sys.exit(1)
    else:
        print_error(f"Failed to create device: {device_response.text}")
        sys.exit(1)
    
    # Step 5: Create test alert (THIS WILL TRIGGER EMAIL!)
    print_step(5, "Creating test alert - EMAIL WILL BE SENT!")
    print_info(f"Sending notification to: {TEST_USER_EMAIL}")
    
    alert_response = requests.post(
        f"{API_BASE}/api/alerts",
        json={
            "device_id": device_id,
            "type": "security",
            "severity": "high",
            "message": "Test Alert - Suspicious activity detected on Test Security Camera"
        },
        headers=headers
    )
    
    if alert_response.status_code == 201:
        print_success("Test alert created successfully!")
        print_info("📧 Email should be sent to your inbox")
        print_info("Check your email (might take 10-30 seconds)")
        alert_data = alert_response.json()
        print_info(f"Alert ID: {alert_data.get('_id') or alert_data.get('id')}")
    else:
        print_error(f"Failed to create alert: {alert_response.text}")
        sys.exit(1)
    
    # Step 6: Verify alert in system
    print_step(6, "Verifying alert in system")
    alerts_response = requests.get(f"{API_BASE}/api/alerts", headers=headers)
    
    if alerts_response.status_code == 200:
        alerts = alerts_response.json()
        print_success(f"Found {len(alerts)} alert(s) in system")
        if alerts:
            latest = alerts[0]
            print_info(f"Latest alert: {latest.get('message')}")
            print_info(f"Severity: {latest.get('severity')}")
            print_info(f"Status: {latest.get('status')}")
    
    # Final summary
    print("\n" + "="*60)
    print("  🎉 TEST COMPLETE!")
    print("="*60)
    print(f"\n✅ Server: Running")
    print(f"✅ User: {TEST_USER_EMAIL}")
    print(f"✅ Device: Test Security Camera")
    print(f"✅ Alert: Created with HIGH severity")
    print(f"📧 Email: Should arrive in {TEST_USER_EMAIL}")
    print(f"\n📊 View dashboard: {API_BASE}/dashboard")
    print(f"📖 API docs: {API_BASE}/docs")
    
    print("\n💡 What to check:")
    print("   1. Check your email inbox (and spam folder)")
    print("   2. Email should have nice HTML formatting with orange/yellow badge")
    print("   3. Login to dashboard and see the alert")
    print("   4. Try resolving the alert from the UI")
    
    print("\n🎯 Next steps:")
    print("   - If email arrived: Email notifications working! ✅")
    print("   - If no email: Check server console for error messages")
    print("   - Deploy to production: See docs/DEPLOYMENT.md")
    print("\n")

if __name__ == "__main__":
    print("⚠️  Make sure to update TEST_USER_EMAIL at the top of this file!")
    print("⚠️  Make sure the server is running: uvicorn main:app --reload --port 8000")
    print("\nStarting test...\n")
    main()
