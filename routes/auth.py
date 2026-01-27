# routes/auth.py - Authentication Routes
from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
import os
import bcrypt as bcrypt_lib
import hashlib
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64

from models import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordChange,
    RefreshTokenRequest,
    LogoutRequest,
    ResendVerificationRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    MfaDisableRequest,
    MfaBackupCodesResponse,
)
from database import get_database
from middleware.security import limiter
from services.notification_service import NotificationService
from services.audit_logger import AuditLogger
try:
    from utils.password_validator import password_validator
except ImportError:
    password_validator = None

router = APIRouter()
security = HTTPBearer()

# Password hashing - use bcrypt directly with proper byte handling
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # bcrypt has a 72 byte limit
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt_lib.gensalt()
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt_lib.checkpw(password_bytes, hashed_bytes)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = os.getenv("JWT_ISSUER", "iot-security-platform")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "1440"))
REFRESH_EXPIRES_DAYS = int(os.getenv("REFRESH_EXPIRES_DAYS", "30"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "15"))
REQUIRE_EMAIL_VERIFICATION = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() == "true"
EMAIL_VERIFICATION_ENABLED = os.getenv("EMAIL_VERIFICATION_ENABLED", "").lower()
VERIFICATION_EXPIRES_HOURS = int(os.getenv("VERIFICATION_EXPIRES_HOURS", "24"))
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
MFA_ISSUER = os.getenv("MFA_ISSUER", "IoT Security Platform")
MFA_BACKUP_CODES = int(os.getenv("MFA_BACKUP_CODES", "8"))
MFA_BACKUP_CODE_LENGTH = int(os.getenv("MFA_BACKUP_CODE_LENGTH", "10"))
if os.getenv("APP_ENV", "local").lower() == "production" and JWT_SECRET == "your-super-secret-key-change-in-production":
    raise RuntimeError("JWT_SECRET must be set in production")

def create_access_token(user_id: str, role: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iss": JWT_ISSUER
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)

async def _issue_refresh_token(db, user_id: str) -> str:
    token = _generate_refresh_token()
    token_hash = _hash_refresh_token(token)
    now = datetime.utcnow()
    expires_at = now + timedelta(days=REFRESH_EXPIRES_DAYS)
    await db.refresh_tokens.insert_one({
        "user_id": user_id,
        "token_hash": token_hash,
        "created_at": now,
        "expires_at": expires_at,
        "revoked": False
    })
    return token

async def _revoke_refresh_token(db, token_hash: str):
    await db.refresh_tokens.update_one(
        {"token_hash": token_hash},
        {"$set": {"revoked": True, "revoked_at": datetime.utcnow()}}
    )

async def _revoke_all_refresh_tokens(db, user_id: str):
    await db.refresh_tokens.update_many(
        {"user_id": user_id, "revoked": False},
        {"$set": {"revoked": True, "revoked_at": datetime.utcnow()}}
    )

def _hash_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def _generate_verification_token() -> str:
    return secrets.token_urlsafe(32)

def _normalize_mfa_code(code: str) -> str:
    return "".join(str(code or "").split()).strip()

def _hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()

def _generate_backup_codes() -> list[str]:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return [
        "".join(secrets.choice(alphabet) for _ in range(MFA_BACKUP_CODE_LENGTH))
        for _ in range(MFA_BACKUP_CODES)
    ]

async def _verify_mfa_code(db, user: dict, code: str) -> bool:
    code = _normalize_mfa_code(code)
    if not code:
        return False
    secret = user.get("mfa_secret")
    if secret:
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            return True
    backup_codes = user.get("mfa_backup_codes", []) or []
    code_hash = _hash_backup_code(code)
    if code_hash in backup_codes:
        updated = [c for c in backup_codes if c != code_hash]
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"mfa_backup_codes": updated, "updatedAt": datetime.utcnow()}}
        )
        return True
    return False

async def _send_verification_email(email: str, token: str, user_name: str):
    verify_link = f"{APP_BASE_URL}/verify-email?token={token}"
    subject = "Verify your email - IoT Security Platform"
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
          <div style="background: linear-gradient(135deg, #2f6bff 0%, #1e4ed8 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">Verify your email</h1>
          </div>
          <div style="padding: 30px;">
            <p style="font-size: 16px; color: #333; margin-bottom: 20px;">Hi {user_name},</p>
            <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 20px;">
              Please verify your email to activate your IoT Security Platform account.
            </p>
            <div style="text-align: center; margin: 30px 0;">
              <a href="{verify_link}" style="display: inline-block; background: #2f6bff; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
                Verify Email
              </a>
            </div>
            <p style="font-size: 13px; color: #999; line-height: 1.6; margin-top: 20px;">
              Or copy and paste this link into your browser:<br/>
              <a href="{verify_link}" style="color: #2f6bff; word-break: break-all;">{verify_link}</a>
            </p>
            <p style="font-size: 13px; color: #999; line-height: 1.6; margin-top: 20px;">
              <strong>This link will expire in {VERIFICATION_EXPIRES_HOURS} hours.</strong>
            </p>
          </div>
        </div>
      </body>
    </html>
    """
    notification_service = NotificationService()
    await notification_service._send_email(
        to_email=email,
        subject=subject,
        message=html_content,
        severity="info",
        alert_id="verify-email"
    )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        db = await get_database()
        from bson import ObjectId
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if REQUIRE_EMAIL_VERIFICATION and user.get("email_verified") is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )

        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def signup(user_data: UserCreate, request: Request, background_tasks: BackgroundTasks):
    """
    Register a new user
    - Creates new user account
    - Hashes password securely with strong requirements
    - Returns JWT token for immediate login
    
    Password Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    db = await get_database()
    
    # Normalize email
    email = user_data.email.lower()
    
    # Validate password strength
    if password_validator:
        is_valid, errors = password_validator.validate(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet security requirements",
                    "errors": errors,
                    "requirements": password_validator.get_requirements_text()
                }
            )
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user document
    verification_token = _generate_verification_token()
    verification_token_hash = _hash_verification_token(verification_token)
    verification_expires = datetime.utcnow() + timedelta(hours=VERIFICATION_EXPIRES_HOURS)

    user_doc = {
        "name": user_data.name,
        "email": email,
        "password": hashed_password,
        "role": user_data.role,
        "organization": None,
        "organizationRole": "member",
        "plan": "free",  # All new users start on free plan
        "subscription_id": None,
        "subscription_status": None,
        "stripe_customer_id": None,
        "failed_login_count": 0,
        "lock_until": None,
        "email_verified": False,
        "email_verification_token": verification_token_hash,
        "email_verification_expires": verification_expires,
        "mfa_enabled": False,
        "mfa_secret": None,
        "mfa_backup_codes": [],
        "mfa_pending_secret": None,
        "mfa_pending_backup_codes": [],
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    # Insert into database
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create response user object (no password)
    safe_user = UserResponse(
        id=user_id,
        name=user_doc["name"],
        email=user_doc["email"],
        role=user_doc["role"],
        organization=user_doc.get("organization"),
        organization_role=user_doc.get("organizationRole"),
        plan=user_doc.get("plan", "free"),
        subscription_id=user_doc.get("subscription_id"),
        subscription_status=user_doc.get("subscription_status"),
        stripe_customer_id=user_doc.get("stripe_customer_id"),
        mfa_enabled=user_doc.get("mfa_enabled", False),
        created_at=user_doc["createdAt"]
    )
    
    # Send verification email if enabled
    env = os.getenv("APP_ENV", "local").lower()
    verification_enabled = EMAIL_VERIFICATION_ENABLED == "true" or REQUIRE_EMAIL_VERIFICATION or env == "production"
    if verification_enabled:
        background_tasks.add_task(
            _send_verification_email,
            email,
            verification_token,
            user_doc["name"]
        )

    # Generate JWT and refresh token
    token = create_access_token(user_id, user_doc["role"])
    refresh_token = await _issue_refresh_token(db, user_id)
    
    signup_message = "Signup successful. Please verify your email." if verification_enabled else "Signup successful"

    return TokenResponse(
        token=token,
        refresh_token=refresh_token,
        email_verified=False,
        verification_required=verification_enabled,
        user=safe_user,
        message=signup_message
    )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(credentials: UserLogin, request: Request):
    """
    Authenticate user and return JWT token
    - Verifies email and password
    - Returns JWT for subsequent requests
    """
    db = await get_database()
    
    # Find user by email (normalized)
    email = credentials.email.lower()
    user = await db.users.find_one({"email": email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    lock_until = user.get("lock_until")
    if lock_until and isinstance(lock_until, datetime) and lock_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to failed attempts. Please try again later."
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password"]):
        failed_count = int(user.get("failed_login_count", 0)) + 1
        update = {"failed_login_count": failed_count, "updatedAt": datetime.utcnow()}
        if failed_count >= MAX_LOGIN_ATTEMPTS:
            update["lock_until"] = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            update["failed_login_count"] = 0
        await db.users.update_one({"_id": user["_id"]}, {"$set": update})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Reset lockout counters on success
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"failed_login_count": 0, "lock_until": None, "updatedAt": datetime.utcnow()}}
    )

    if REQUIRE_EMAIL_VERIFICATION and user.get("email_verified") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox."
        )

    # MFA check - REQUIRED if user has MFA enabled
    if user.get("mfa_enabled"):
        if not credentials.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "MFA code required. Please enter the 6-digit code from your authenticator app.", "mfa_required": True}
            )
        valid = await _verify_mfa_code(db, user, credentials.mfa_code)
        if not valid:
            # Increment failed attempts for MFA too
            failed_count = int(user.get("failed_login_count", 0)) + 1
            update = {"failed_login_count": failed_count, "updatedAt": datetime.utcnow()}
            if failed_count >= MAX_LOGIN_ATTEMPTS:
                update["lock_until"] = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                update["failed_login_count"] = 0
            await db.users.update_one({"_id": user["_id"]}, {"$set": update})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Invalid MFA code. Please try again.", "mfa_required": True}
            )
    
    # Get organization details if user belongs to one
    org = None
    if user.get("organization"):
        from bson import ObjectId
        org_doc = await db.organizations.find_one({"_id": ObjectId(user["organization"])})
        if org_doc:
            org = {
                "id": str(org_doc["_id"]),
                "name": org_doc["name"],
                "subdomain": org_doc["subdomain"],
                "plan": org_doc["plan"]
            }
    
    # Create safe user response
    user_id = str(user["_id"])
    safe_user = UserResponse(
        id=user_id,
        name=user["name"],
        email=user["email"],
        role=user["role"],
        organization=org,
        organization_role=user.get("organizationRole"),
        plan=user.get("plan", "free"),
        subscription_id=user.get("subscription_id"),
        subscription_status=user.get("subscription_status"),
        stripe_customer_id=user.get("stripe_customer_id"),
        mfa_enabled=user.get("mfa_enabled", False),
        created_at=user.get("createdAt", datetime.utcnow())
    )
    
    # Generate JWT and refresh token
    token = create_access_token(user_id, user["role"])
    refresh_token = await _issue_refresh_token(db, user_id)
    
    return TokenResponse(
        token=token,
        refresh_token=refresh_token,
        email_verified=user.get("email_verified", True),
        verification_required=REQUIRE_EMAIL_VERIFICATION,
        user=safe_user,
        message="Login successful"
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current authenticated user's information
    Requires valid JWT token in Authorization header
    """
    db = await get_database()
    user_id = str(current_user["_id"])
    
    # Get organization if exists
    org = None
    if current_user.get("organization"):
        from bson import ObjectId
        org_doc = await db.organizations.find_one({"_id": ObjectId(current_user["organization"])})
        if org_doc:
            org = {
                "id": str(org_doc["_id"]),
                "name": org_doc["name"],
                "subdomain": org_doc["subdomain"],
                "plan": org_doc["plan"]
            }
    
    return UserResponse(
        id=user_id,
        name=current_user["name"],
        email=current_user["email"],
        role=current_user["role"],
        organization=org,
        organization_role=current_user.get("organizationRole"),
        mfa_enabled=current_user.get("mfa_enabled", False),
        created_at=current_user.get("createdAt", datetime.utcnow())
    )

@router.get("/mfa/status")
@limiter.limit("10/minute")
async def get_mfa_status(request: Request, current_user = Depends(get_current_user)):
    backup_codes = current_user.get("mfa_backup_codes", []) or []
    return {
        "mfa_enabled": bool(current_user.get("mfa_enabled", False)),
        "backup_codes_remaining": len(backup_codes)
    }

@router.post("/mfa/setup", response_model=MfaSetupResponse)
@limiter.limit("5/minute")
async def setup_mfa(request: Request, current_user = Depends(get_current_user)):
    if current_user.get("mfa_enabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled")
    db = await get_database()
    secret = pyotp.random_base32()
    backup_codes = _generate_backup_codes()
    hashed_codes = [_hash_backup_code(c) for c in backup_codes]

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "mfa_pending_secret": secret,
            "mfa_pending_backup_codes": hashed_codes,
            "mfa_pending_created_at": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }}
    )
    totp = pyotp.TOTP(secret)
    otpauth_uri = totp.provisioning_uri(name=current_user["email"], issuer_name=MFA_ISSUER)
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(otpauth_uri)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 data URI
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    qr_code_data_uri = f"data:image/png;base64,{img_str}"
    
    return MfaSetupResponse(
        secret=secret,
        otpauth_uri=otpauth_uri,
        qr_code_image=qr_code_data_uri,
        backup_codes=backup_codes
    )

@router.post("/mfa/verify")
@limiter.limit("5/minute")
async def verify_mfa(body: MfaVerifyRequest, request: Request, current_user = Depends(get_current_user)):
    pending_secret = current_user.get("mfa_pending_secret")
    pending_codes = current_user.get("mfa_pending_backup_codes", []) or []
    if not pending_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No MFA setup in progress")
    code = _normalize_mfa_code(body.code)
    totp = pyotp.TOTP(pending_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    db = await get_database()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "mfa_enabled": True,
            "mfa_secret": pending_secret,
            "mfa_backup_codes": pending_codes,
            "updatedAt": datetime.utcnow()
        }, "$unset": {
            "mfa_pending_secret": "",
            "mfa_pending_backup_codes": "",
            "mfa_pending_created_at": ""
        }}
    )
    # Revoke all refresh tokens when MFA is enabled (force re-authentication)
    await _revoke_all_refresh_tokens(db, str(current_user["_id"]))
    return {"ok": True}

@router.post("/mfa/disable")
@limiter.limit("5/minute")
async def disable_mfa(body: MfaDisableRequest, request: Request, current_user = Depends(get_current_user)):
    if not current_user.get("mfa_enabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")
    db = await get_database()
    valid = await _verify_mfa_code(db, current_user, body.code)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "mfa_enabled": False,
            "mfa_secret": None,
            "mfa_backup_codes": [],
            "updatedAt": datetime.utcnow()
        }, "$unset": {
            "mfa_pending_secret": "",
            "mfa_pending_backup_codes": "",
            "mfa_pending_created_at": ""
        }}
    )
    # Revoke all refresh tokens when MFA is disabled (security best practice)
    await _revoke_all_refresh_tokens(db, str(current_user["_id"]))
    return {"ok": True}

@router.post("/mfa/backup-codes", response_model=MfaBackupCodesResponse)
@limiter.limit("5/minute")
async def regenerate_backup_codes(body: MfaVerifyRequest, request: Request, current_user = Depends(get_current_user)):
    if not current_user.get("mfa_enabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")
    db = await get_database()
    valid = await _verify_mfa_code(db, current_user, body.code)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    backup_codes = _generate_backup_codes()
    hashed_codes = [_hash_backup_code(c) for c in backup_codes]
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"mfa_backup_codes": hashed_codes, "updatedAt": datetime.utcnow()}}
    )
    return MfaBackupCodesResponse(backup_codes=backup_codes)

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(body: RefreshTokenRequest, request: Request):
    from bson import ObjectId
    db = await get_database()
    token_hash = _hash_refresh_token(body.refresh_token)
    stored = await db.refresh_tokens.find_one({"token_hash": token_hash})
    if not stored or stored.get("revoked"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if stored.get("expires_at") and stored["expires_at"] < datetime.utcnow():
        await _revoke_refresh_token(db, token_hash)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    # Convert user_id to ObjectId if it's a string
    user_id = stored["user_id"]
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token")
    
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate refresh token
    await _revoke_refresh_token(db, token_hash)
    new_refresh = await _issue_refresh_token(db, str(user["_id"]))
    new_access = create_access_token(str(user["_id"]), user.get("role", "consumer"))

    safe_user = UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user["role"],
        organization=None,
        organization_role=user.get("organizationRole"),
        plan=user.get("plan", "free"),
        subscription_id=user.get("subscription_id"),
        subscription_status=user.get("subscription_status"),
        stripe_customer_id=user.get("stripe_customer_id"),
        mfa_enabled=user.get("mfa_enabled", False),
        created_at=user.get("createdAt", datetime.utcnow())
    )

    return TokenResponse(
        token=new_access,
        refresh_token=new_refresh,
        user=safe_user,
        message="Token refreshed"
    )

@router.get("/verify-email")
async def verify_email(request: Request, token: str = Query(..., description="Verification token")):
    db = await get_database()
    token_hash = _hash_verification_token(token)
    user = await db.users.find_one({
        "email_verification_token": token_hash,
        "email_verification_expires": {"$gt": datetime.utcnow()}
    })
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification link")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_verified": True, "updatedAt": datetime.utcnow()},
         "$unset": {"email_verification_token": "", "email_verification_expires": ""}}
    )

    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(request: Request, body: ResendVerificationRequest, background_tasks: BackgroundTasks):
    db = await get_database()
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if user and not user.get("email_verified", False):
        token = _generate_verification_token()
        token_hash = _hash_verification_token(token)
        expires_at = datetime.utcnow() + timedelta(hours=VERIFICATION_EXPIRES_HOURS)
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"email_verification_token": token_hash, "email_verification_expires": expires_at}}
        )
        background_tasks.add_task(
            _send_verification_email,
            email,
            token,
            user.get("name", "User")
        )
    return {"message": "If an account exists, a verification email has been sent."}

@router.post("/logout")
@limiter.limit("10/minute")
async def logout(body: LogoutRequest, request: Request, current_user = Depends(get_current_user)):
    db = await get_database()
    user_id = str(current_user["_id"])
    await _revoke_all_refresh_tokens(db, user_id)

    if body and body.refresh_token:
        token_hash = _hash_refresh_token(body.refresh_token)
        await _revoke_refresh_token(db, token_hash)

    return {"message": "Logged out"}

@router.post("/unlock/{user_id}")
@limiter.limit("5/minute")
async def unlock_account(user_id: str, request: Request, current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    db = await get_database()
    from bson import ObjectId
    try:
        target_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

    result = await db.users.update_one(
        {"_id": target_id},
        {"$set": {"failed_login_count": 0, "lock_until": None, "updatedAt": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "Account unlocked"}
@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(password_data: PasswordChange, request: Request, user: dict = Depends(get_current_user)):
    '''
    Change user password
    - Validates current password
    - Enforces strong password requirements
    - Updates password securely
    '''
    db = await get_database()
    
    # Verify current password
    if not verify_password(password_data.current_password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Current password is incorrect'
        )
    
    # Validate new password strength
    if password_validator:
        is_valid, errors = password_validator.validate(password_data.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'message': 'New password does not meet security requirements',
                    'errors': errors,
                    'requirements': password_validator.get_requirements_text()
                }
            )
    
    # Check that new password is different from current
    if verify_password(password_data.new_password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='New password must be different from current password'
        )
    
    # Hash new password
    new_hashed_password = hash_password(password_data.new_password)
    
    # Update password in database
    result = await db.users.update_one(
        {'_id': user['_id']},
        {
            '$set': {
                'password': new_hashed_password,
                'updatedAt': datetime.utcnow(),
                'lastPasswordChange': datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update password'
        )
    
    # Revoke all refresh tokens on password change (security best practice)
    await _revoke_all_refresh_tokens(db, str(user['_id']))
    
    # Log password change
    try:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await AuditLogger.log(
            db=db,
            user_id=user['_id'],
            user_email=user.get('email', ''),
            user_name=user.get('name', ''),
            action="password_change",
            resource_type="user",
            resource_id=str(user['_id']),
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Failed to log password change: {e}")
    
    return {
        'message': 'Password changed successfully',
        'timestamp': datetime.utcnow().isoformat()
    }

