"""
Change Password Script
Updates user password with strong security requirements
"""

import requests
import sys
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"

def change_password():
    print("="*60)
    print("  IoT Security Platform - Change Password")
    print("="*60)
    
    # Get credentials
    email = input("\nEmail: ").strip()
    current_password = input("Current Password: ").strip()
    new_password = input("New Password: ").strip()
    confirm_password = input("Confirm New Password: ").strip()
    
    if new_password != confirm_password:
        print("\n❌ Passwords do not match!")
        return
    
    print("\n🔐 Logging in...")
    
    # Login
    try:
        login_response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={"email": email, "password": current_password}
        )
        
        if login_response.status_code != 200:
            print(f"\n❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["token"]
        print("✅ Logged in successfully!")
        
    except Exception as e:
        print(f"\n❌ Login error: {e}")
        return
    
    # Change password
    print("\n🔄 Changing password...")
    
    try:
        change_response = requests.post(
            f"{API_BASE}/api/auth/change-password",
            json={
                "current_password": current_password,
                "new_password": new_password
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if change_response.status_code == 200:
            print("\n✅ Password changed successfully!")
            print(f"\nTimestamp: {change_response.json()['timestamp']}")
            print("\n🔐 Your new password meets all security requirements:")
            print("  ✓ Minimum 12 characters")
            print("  ✓ Contains uppercase letters")
            print("  ✓ Contains lowercase letters")
            print("  ✓ Contains numbers")
            print("  ✓ Contains special characters")
        else:
            error_data = change_response.json()
            print(f"\n❌ Password change failed!")
            
            if isinstance(error_data.get('detail'), dict):
                print(f"\n{error_data['detail']['message']}")
                print("\nErrors:")
                for error in error_data['detail']['errors']:
                    print(f"  • {error}")
                print(f"\n{error_data['detail']['requirements']}")
            else:
                print(f"\nError: {error_data.get('detail', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: uvicorn main:app --reload --port 8000\n")
    change_password()
    print("\n")
