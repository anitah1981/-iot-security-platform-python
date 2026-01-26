"""
Password Reset Routes
Handles forgot password and reset password functionality
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import secrets
import hashlib
import os

from database import get_database
from routes.auth import hash_password, _revoke_all_refresh_tokens
from services.notification_service import NotificationService

router = APIRouter(prefix="/api/auth", tags=["password-reset"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


def generate_reset_token() -> str:
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash the token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


async def send_reset_email(email: str, token: str, user_name: str):
    """Send password reset email"""
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    reset_link = f"{base_url}/reset-password?token={token}"
    
    subject = "Password Reset Request - IoT Security Platform"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #2f6bff 0%, #1e4ed8 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Password Reset Request</h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px;">
                <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                    Hi {user_name},
                </p>
                
                <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 20px;">
                    We received a request to reset your password for your IoT Security Platform account. 
                    If you didn't make this request, you can safely ignore this email.
                </p>
                
                <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 30px;">
                    To reset your password, click the button below:
                </p>
                
                <!-- Reset Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="display: inline-block; background: #2f6bff; color: white; padding: 14px 32px; 
                              text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
                        Reset Password
                    </a>
                </div>
                
                <p style="font-size: 13px; color: #999; line-height: 1.6; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    Or copy and paste this link into your browser:<br/>
                    <a href="{reset_link}" style="color: #2f6bff; word-break: break-all;">{reset_link}</a>
                </p>
                
                <p style="font-size: 13px; color: #999; line-height: 1.6; margin-top: 20px;">
                    <strong>This link will expire in 1 hour.</strong>
                </p>
                
                <p style="font-size: 13px; color: #999; line-height: 1.6; margin-top: 20px;">
                    If you didn't request a password reset, please ignore this email or contact support if you have concerns.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="font-size: 12px; color: #6b7280; margin: 0;">
                    IoT Security Platform<br/>
                    Secure your IoT devices with confidence
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Send email using notification service
    notification_service = NotificationService()
    try:
        await notification_service._send_email(
            to_email=email,
            subject=subject,
            message=html_content,
            severity="info",
            alert_id="password-reset"
        )
        print(f"[OK] Password reset email sent to {email}")
    except Exception as e:
        print(f"[ERROR] Failed to send password reset email: {e}")
        raise


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks
):
    """
    Request a password reset link
    
    - Validates email exists
    - Generates secure reset token
    - Sends email with reset link
    - Token expires in 1 hour
    """
    db = await get_database()
    
    # Find user by email
    user = await db.users.find_one({"email": request.email.lower()})
    
    # Always return success to prevent email enumeration
    # But only send email if user exists
    if user:
        # Generate reset token
        token = generate_reset_token()
        token_hash = hash_token(token)
        
        # Store token in database with expiration
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "reset_token": token_hash,
                "reset_token_expires": expires_at,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        # Send reset email in background
        background_tasks.add_task(
            send_reset_email,
            request.email.lower(),
            token,
            user.get("name", "User")
        )
        
        print(f"[OK] Password reset requested for {request.email}")
    else:
        print(f"[INFO] Password reset requested for non-existent email: {request.email}")
    
    # Always return success message
    return {
        "message": "If an account exists with that email, a password reset link has been sent."
    }


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using token from email
    
    - Validates token
    - Checks expiration
    - Updates password
    - Invalidates token
    """
    db = await get_database()
    
    # Hash the provided token
    token_hash = hash_token(request.token)
    
    # Find user with valid token
    user = await db.users.find_one({
        "reset_token": token_hash,
        "reset_token_expires": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate new password strength
    try:
        from utils.password_validator import password_validator
        if password_validator:
            is_valid, errors = password_validator.validate(request.new_password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Password does not meet security requirements",
                        "errors": errors,
                        "requirements": password_validator.get_requirements_text()
                    }
                )
    except ImportError:
        pass
    
    # Hash new password
    new_hashed_password = hash_password(request.new_password)
    
    # Update password and invalidate token
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "password": new_hashed_password,
            "updatedAt": datetime.utcnow()
        },
        "$unset": {
            "reset_token": "",
            "reset_token_expires": ""
        }}
    )
    
    # Revoke all refresh tokens on password reset (security best practice)
    await _revoke_all_refresh_tokens(db, str(user["_id"]))
    
    print(f"[OK] Password reset successful for user {user.get('email')}")
    
    return {
        "message": "Password has been reset successfully. You can now log in with your new password."
    }


@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """
    Verify if a reset token is valid
    Used by frontend to check token before showing reset form
    """
    db = await get_database()
    
    token_hash = hash_token(token)
    
    user = await db.users.find_one({
        "reset_token": token_hash,
        "reset_token_expires": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {
        "valid": True,
        "email": user.get("email")
    }
