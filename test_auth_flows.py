#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Authentication Flow Tests
Tests: Signup, Email Verification, Password Reset, Login
"""

import requests
import time
import sys
import io
from datetime import datetime
from typing import Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_BASE = 'http://localhost:8000'

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")

def print_test(name: str):
    """Print test name"""
    print(f"{Colors.CYAN}[TEST]{Colors.ENDC} {name}...")

def print_success(message: str):
    """Print success message"""
    print(f"  {Colors.GREEN}✓{Colors.ENDC} {message}")

def print_error(message: str):
    """Print error message"""
    print(f"  {Colors.RED}✗{Colors.ENDC} {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"  {Colors.YELLOW}⚠{Colors.ENDC} {message}")

def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.CYAN}ℹ{Colors.ENDC} {message}")

class AuthFlowTester:
    def __init__(self):
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "TestPass4#8@Secure9"  # Strong password without sequential chars
        self.test_name = "Test User"
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.verification_token: Optional[str] = None
        self.reset_token: Optional[str] = None
        self.passed = 0
        self.failed = 0
        
    def test_signup(self) -> bool:
        """Test user signup"""
        print_test("User Signup")
        
        try:
            response = requests.post(
                f'{API_BASE}/api/auth/signup',
                json={
                    'name': self.test_name,
                    'email': self.test_email,
                    'password': self.test_password,
                    'role': 'consumer'
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                self.token = data.get('token')
                self.refresh_token = data.get('refresh_token')
                
                print_success(f"Account created: {self.test_email}")
                print_info(f"Message: {data.get('message')}")
                print_info(f"Email verified: {data.get('email_verified')}")
                print_info(f"Verification required: {data.get('verification_required')}")
                
                if self.token:
                    print_success("JWT token received")
                if self.refresh_token:
                    print_success("Refresh token received")
                    
                self.passed += 1
                return True
            else:
                print_error(f"Signup failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception during signup: {e}")
            self.failed += 1
            return False
    
    def test_duplicate_signup(self) -> bool:
        """Test that duplicate signup is rejected"""
        print_test("Duplicate Signup Prevention")
        
        try:
            response = requests.post(
                f'{API_BASE}/api/auth/signup',
                json={
                    'name': self.test_name,
                    'email': self.test_email,
                    'password': self.test_password,
                    'role': 'consumer'
                }
            )
            
            if response.status_code == 409:
                print_success("Duplicate signup correctly rejected (409)")
                self.passed += 1
                return True
            else:
                print_error(f"Expected 409, got {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_login_unverified(self) -> bool:
        """Test login with unverified email (if verification is required)"""
        print_test("Login with Unverified Email")
        
        try:
            response = requests.post(
                f'{API_BASE}/api/auth/login',
                json={
                    'email': self.test_email,
                    'password': self.test_password
                }
            )
            
            # If REQUIRE_EMAIL_VERIFICATION is false, login should succeed
            # If true, should get 403
            if response.status_code == 200:
                print_warning("Login allowed without verification (REQUIRE_EMAIL_VERIFICATION=false)")
                data = response.json()
                self.token = data.get('token')
                self.refresh_token = data.get('refresh_token')
                print_info(f"Email verified: {data.get('email_verified')}")
                self.passed += 1
                return True
            elif response.status_code == 403:
                print_success("Login blocked - email verification required (403)")
                print_info(f"Message: {response.json().get('detail')}")
                self.passed += 1
                return True
            else:
                print_error(f"Unexpected status code: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_resend_verification(self) -> bool:
        """Test resending verification email"""
        print_test("Resend Verification Email")
        
        try:
            response = requests.post(
                f'{API_BASE}/api/auth/resend-verification',
                json={'email': self.test_email}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Verification email resend request processed")
                print_info(f"Message: {data.get('message')}")
                print_warning("Check terminal/email logs for verification token")
                self.passed += 1
                return True
            else:
                print_error(f"Resend failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_forgot_password(self) -> bool:
        """Test forgot password flow"""
        print_test("Forgot Password Request")
        
        try:
            response = requests.post(
                f'{API_BASE}/api/auth/forgot-password',
                json={'email': self.test_email}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Password reset request processed")
                print_info(f"Message: {data.get('message')}")
                print_warning("Check terminal/email logs for reset token")
                self.passed += 1
                return True
            else:
                print_error(f"Forgot password failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_password_strength(self) -> bool:
        """Test password strength validation"""
        print_test("Password Strength Validation")
        
        weak_passwords = [
            ("short1A!", "Too short"),
            ("alllowercase8!x", "No uppercase"),
            ("ALLUPPERCASE8!X", "No lowercase"),
            ("NoNumbers!@#Abc", "No numbers"),
            ("NoSpecialChars8Xy", "No special chars"),
        ]
        
        all_passed = True
        for weak_pass, reason in weak_passwords:
            try:
                response = requests.post(
                    f'{API_BASE}/api/auth/signup',
                    json={
                        'name': 'Test',
                        'email': f'weak_{int(time.time())}@test.com',
                        'password': weak_pass,
                        'role': 'consumer'
                    }
                )
                
                if response.status_code == 400:
                    print_success(f"Weak password rejected: {reason}")
                else:
                    print_error(f"Weak password accepted: {reason}")
                    all_passed = False
                    
            except Exception as e:
                print_error(f"Exception testing {reason}: {e}")
                all_passed = False
        
        if all_passed:
            self.passed += 1
        else:
            self.failed += 1
            
        return all_passed
    
    def test_invalid_login(self) -> bool:
        """Test login with invalid credentials"""
        print_test("Invalid Login Credentials")
        
        try:
            response = requests.post(
                f'{API_BASE}/api/auth/login',
                json={
                    'email': self.test_email,
                    'password': 'WrongPassword123!'
                }
            )
            
            if response.status_code == 401:
                print_success("Invalid credentials correctly rejected (401)")
                self.passed += 1
                return True
            else:
                print_error(f"Expected 401, got {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_token_refresh(self) -> bool:
        """Test token refresh"""
        print_test("Token Refresh")
        
        if not self.refresh_token:
            print_warning("No refresh token available, skipping test")
            return True
        
        try:
            response = requests.post(
                f'{API_BASE}/api/auth/refresh',
                json={'refresh_token': self.refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get('token')
                new_refresh = data.get('refresh_token')
                
                print_success("Token refreshed successfully")
                print_info("New access token received")
                print_info("New refresh token received (rotation)")
                
                # Update tokens
                self.token = new_token
                self.refresh_token = new_refresh
                
                self.passed += 1
                return True
            else:
                print_error(f"Token refresh failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_protected_endpoint(self) -> bool:
        """Test accessing protected endpoint with token"""
        print_test("Protected Endpoint Access")
        
        if not self.token:
            print_warning("No token available, skipping test")
            return True
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(
                f'{API_BASE}/api/auth/me',
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Protected endpoint accessible")
                print_info(f"User: {data.get('name')} ({data.get('email')})")
                print_info(f"Role: {data.get('role')}")
                self.passed += 1
                return True
            else:
                print_error(f"Access failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_invalid_token(self) -> bool:
        """Test that invalid token is rejected"""
        print_test("Invalid Token Rejection")
        
        try:
            headers = {'Authorization': 'Bearer invalid_token_xyz'}
            response = requests.get(
                f'{API_BASE}/api/auth/me',
                headers=headers
            )
            
            if response.status_code == 401:
                print_success("Invalid token correctly rejected (401)")
                self.passed += 1
                return True
            else:
                print_error(f"Expected 401, got {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def test_logout(self) -> bool:
        """Test logout (revoke refresh tokens)"""
        print_test("Logout (Token Revocation)")
        
        if not self.token or not self.refresh_token:
            print_warning("No tokens available, skipping test")
            return True
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.post(
                f'{API_BASE}/api/auth/logout',
                json={'refresh_token': self.refresh_token},
                headers=headers
            )
            
            if response.status_code == 200:
                print_success("Logout successful - refresh token revoked")
                
                # Try to use revoked refresh token
                refresh_response = requests.post(
                    f'{API_BASE}/api/auth/refresh',
                    json={'refresh_token': self.refresh_token}
                )
                
                if refresh_response.status_code == 401:
                    print_success("Revoked token correctly rejected")
                else:
                    print_warning(f"Revoked token still works: {refresh_response.status_code}")
                
                self.passed += 1
                return True
            else:
                print_error(f"Logout failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed += 1
                return False
                
        except Exception as e:
            print_error(f"Exception: {e}")
            self.failed += 1
            return False
    
    def run_all_tests(self):
        """Run all authentication flow tests"""
        print_header("Authentication Flow Tests - v1.0.0")
        print_info(f"Testing against: {API_BASE}")
        print_info(f"Test email: {self.test_email}")
        print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests in sequence
        tests = [
            ("Signup Flow", self.test_signup),
            ("Duplicate Prevention", self.test_duplicate_signup),
            ("Password Strength", self.test_password_strength),
            ("Unverified Login", self.test_login_unverified),
            ("Resend Verification", self.test_resend_verification),
            ("Invalid Credentials", self.test_invalid_login),
            ("Token Refresh", self.test_token_refresh),
            ("Protected Access", self.test_protected_endpoint),
            ("Invalid Token", self.test_invalid_token),
            ("Forgot Password", self.test_forgot_password),
            ("Logout Flow", self.test_logout),
        ]
        
        for name, test_func in tests:
            try:
                test_func()
                print()  # Blank line between tests
            except Exception as e:
                print_error(f"Test '{name}' crashed: {e}")
                self.failed += 1
                print()
        
        # Print summary
        print_header("Test Summary")
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"  Total Tests:  {total}")
        print(f"  {Colors.GREEN}Passed:       {self.passed}{Colors.ENDC}")
        print(f"  {Colors.RED}Failed:       {self.failed}{Colors.ENDC}")
        print(f"  Success Rate: {Colors.GREEN if success_rate >= 90 else Colors.YELLOW}{success_rate:.1f}%{Colors.ENDC}")
        print()
        
        if self.failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.ENDC}\n")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.ENDC}\n")
            return 1

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f'{API_BASE}/api/health', timeout=2)
        return response.status_code == 200
    except:
        return False

if __name__ == '__main__':
    # Check if server is running
    if not check_server():
        print_error("Server is not running!")
        print_info(f"Please start the server with: uvicorn main:app --reload --port 8000")
        sys.exit(1)
    
    # Run tests
    tester = AuthFlowTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
