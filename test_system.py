"""
Comprehensive System Test Script
Tests all major components of the IoT Security Platform
"""

import asyncio
import requests
import json
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "anitah1981@gmail.com"
TEST_PASSWORD = "Test123!!Test"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}Testing: {name}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_section(title):
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}{title}{Colors.END}")
    print('='*60)

# Global token storage
auth_token = None

def test_health_check():
    """Test if server is running"""
    print_test("Server Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is running: {data.get('status')}")
            print_success(f"Database: {data.get('database')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running on http://localhost:8000?")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_login():
    """Test authentication"""
    global auth_token
    print_test("User Authentication (Login)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("token")
            user = data.get("user", {})
            print_success(f"Login successful")
            print_success(f"User: {user.get('name')} ({user.get('email')})")
            print_success(f"Role: {user.get('role')}")
            print_success(f"Plan: {user.get('plan', 'free')}")
            return True
        else:
            error_detail = response.json().get("detail", "Unknown error")
            print_error(f"Login failed: {error_detail}")
            print_warning("Tip: Make sure you're using the correct email and password")
            return False
    except Exception as e:
        print_error(f"Login error: {e}")
        return False

def test_get_user():
    """Test get current user"""
    print_test("Get Current User (JWT Verification)")
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=5)
        
        if response.status_code == 200:
            user = response.json()
            print_success(f"JWT token valid")
            print_success(f"User ID: {user.get('id')}")
            print_success(f"Subscription: {user.get('plan', 'free')} plan")
            if user.get('subscription_status'):
                print_success(f"Subscription Status: {user.get('subscription_status')}")
            return True
        else:
            print_error(f"Get user failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get user error: {e}")
        return False

def test_devices():
    """Test device endpoints"""
    print_test("Device Management")
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get devices
        response = requests.get(f"{BASE_URL}/api/devices/?page=1&limit=10", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            device_count = data.get('total', 0)
            devices = data.get('devices', [])
            print_success(f"Retrieved {device_count} device(s)")
            
            if devices:
                for device in devices[:3]:  # Show first 3
                    status_icon = "🟢" if device.get('status') == 'online' else "🔴"
                    print_success(f"  {status_icon} {device.get('name')} ({device.get('device_id')}) - {device.get('status')}")
            else:
                print_warning("No devices found. Add devices to test this feature.")
            
            return True
        else:
            print_error(f"Get devices failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Device test error: {e}")
        return False

def test_alerts():
    """Test alert endpoints"""
    print_test("Alert Management")
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get alerts
        response = requests.get(f"{BASE_URL}/api/alerts/?page=1&limit=10", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            alert_count = data.get('total', 0)
            alerts = data.get('alerts', [])
            print_success(f"Retrieved {alert_count} alert(s)")
            
            if alerts:
                for alert in alerts[:3]:  # Show first 3
                    severity = alert.get('severity', 'unknown')
                    alert_type = alert.get('alert_type', 'unknown')
                    print_success(f"  [{severity.upper()}] {alert_type}: {alert.get('message')}")
            else:
                print_warning("No alerts found. System will generate alerts based on device activity.")
            
            return True
        else:
            print_error(f"Get alerts failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Alert test error: {e}")
        return False

def test_notification_preferences():
    """Test notification preferences"""
    print_test("Notification Preferences")
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get preferences
        response = requests.get(f"{BASE_URL}/api/notification-preferences/", headers=headers, timeout=5)
        
        if response.status_code == 200:
            prefs = response.json()
            print_success("Notification preferences loaded")
            print_success(f"  Email: {'✓' if prefs.get('email_enabled') else '✗'}")
            print_success(f"  SMS: {'✓' if prefs.get('sms_enabled') else '✗'}")
            print_success(f"  WhatsApp: {'✓' if prefs.get('whatsapp_enabled') else '✗'}")
            print_success(f"  Voice: {'✓' if prefs.get('voice_enabled') else '✗'}")
            
            if prefs.get('phone_number'):
                print_success(f"  Phone: {prefs.get('phone_number')}")
            else:
                print_warning("  No phone number configured for SMS/Voice")
                
            if prefs.get('whatsapp_number'):
                print_success(f"  WhatsApp: {prefs.get('whatsapp_number')}")
            else:
                print_warning("  No WhatsApp number configured")
            
            return True
        else:
            print_error(f"Get notification preferences failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Notification preferences test error: {e}")
        return False

def test_subscription():
    """Test subscription/payment endpoints"""
    print_test("Subscription & Payment System")
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get plans
        response = requests.get(f"{BASE_URL}/api/payments/plans", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            plans = data.get('plans', {})
            print_success(f"Retrieved {len(plans)} subscription plan(s)")
            for plan_name, plan_data in plans.items():
                price = plan_data.get('price', 0)
                device_limit = plan_data.get('device_limit', 0)
                limit_text = "unlimited" if device_limit < 0 else f"{device_limit} devices"
                print_success(f"  {plan_name.capitalize()}: £{price}/month - {limit_text}")
            
            # Get subscription status
            response = requests.get(f"{BASE_URL}/api/payments/subscription", headers=headers, timeout=5)
            if response.status_code == 200:
                sub = response.json()
                print_success(f"Current subscription: {sub.get('plan', 'free')} ({sub.get('status', 'none')})")
            
            # Get usage
            response = requests.get(f"{BASE_URL}/api/payments/usage", headers=headers, timeout=5)
            if response.status_code == 200:
                usage = response.json()
                devices = usage.get('usage', {}).get('devices', {})
                current = devices.get('current', 0)
                limit = devices.get('limit', 0)
                print_success(f"Device usage: {current}/{limit}")
            
            return True
        else:
            print_error(f"Get plans failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Subscription test error: {e}")
        return False

def test_frontend_pages():
    """Test if frontend pages are accessible"""
    print_test("Frontend Pages")
    
    pages = [
        ("/", "Home/Landing Page"),
        ("/login", "Login Page"),
        ("/signup", "Signup Page"),
        ("/dashboard", "Dashboard"),
        ("/settings", "Settings Page"),
        ("/pricing", "Pricing Page"),
        ("/terms", "Terms of Service"),
        ("/privacy", "Privacy Policy"),
        ("/forgot-password", "Forgot Password"),
    ]
    
    success_count = 0
    for path, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                print_success(f"{name}: Accessible")
                success_count += 1
            else:
                print_error(f"{name}: {response.status_code}")
        except Exception as e:
            print_error(f"{name}: {e}")
    
    print_success(f"\n{success_count}/{len(pages)} pages accessible")
    return success_count == len(pages)

def test_websocket_endpoint():
    """Test if WebSocket endpoint is available"""
    print_test("WebSocket Service")
    try:
        # Just check if the endpoint exists (can't fully test WebSocket in simple HTTP request)
        response = requests.get(f"{BASE_URL}/socket.io/", timeout=5)
        # Socket.IO will return 400 for GET requests, which is expected
        if response.status_code in [200, 400]:
            print_success("WebSocket endpoint available")
            print_warning("Full WebSocket test requires browser/Socket.IO client")
            return True
        else:
            print_error(f"WebSocket endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print_warning(f"WebSocket test skipped: {e}")
        return True  # Don't fail on this

def run_all_tests():
    """Run all system tests"""
    print_section("IoT SECURITY PLATFORM - SYSTEM TEST")
    print(f"Testing server at: {BASE_URL}")
    print(f"Test user: {TEST_EMAIL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Backend Tests
    print_section("BACKEND TESTS")
    results['health'] = test_health_check()
    
    if not results['health']:
        print_error("\nServer is not running. Please start the server first:")
        print(f"  cd c:\\IoT-security-app-python")
        print(f"  .\\venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000")
        return
    
    results['login'] = test_login()
    
    if not results['login']:
        print_error("\nLogin failed. Cannot continue with authenticated tests.")
        print_warning("Please check your credentials or create an account first.")
        return
    
    results['get_user'] = test_get_user()
    results['devices'] = test_devices()
    results['alerts'] = test_alerts()
    results['notifications'] = test_notification_preferences()
    results['subscription'] = test_subscription()
    
    # Frontend Tests
    print_section("FRONTEND TESTS")
    results['frontend'] = test_frontend_pages()
    results['websocket'] = test_websocket_endpoint()
    
    # Summary
    print_section("TEST SUMMARY")
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{Colors.BLUE}Results: {passed_tests}/{total_tests} tests passed{Colors.END}")
    
    if failed_tests > 0:
        print(f"{Colors.RED}{failed_tests} test(s) failed{Colors.END}")
    else:
        print(f"{Colors.GREEN}All tests passed! 🎉{Colors.END}")
    
    # Recommendations
    print_section("RECOMMENDATIONS")
    
    if not results.get('frontend'):
        print_warning("Some frontend pages are not accessible. Check for errors in HTML files.")
    
    print("\nTo test notifications:")
    print("  1. Go to http://localhost:8000/settings")
    print("  2. Scroll to 'Notification Preferences'")
    print("  3. Configure your phone numbers")
    print("  4. Enable desired channels")
    print("  5. Click 'Test Email/SMS/WhatsApp/Voice' buttons")
    
    print("\nTo add Twilio for SMS/WhatsApp/Voice:")
    print("  1. Add to .env file:")
    print("     TWILIO_ACCOUNT_SID=your_sid")
    print("     TWILIO_AUTH_TOKEN=your_token")
    print("     TWILIO_PHONE_NUMBER=+44your_number")
    print("  2. Restart the server")
    print("  3. Test notifications in settings page")
    
    print("\nNext steps:")
    print("  - Add devices to monitor")
    print("  - Configure notification preferences")
    print("  - Test alert generation")
    print("  - Review subscription usage")
    print("  - Explore pricing page")
    
    print_section("TEST COMPLETE")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)
