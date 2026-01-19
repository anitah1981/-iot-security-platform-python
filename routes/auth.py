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

from models import UserCreate, UserLogin, UserResponse, TokenResponse, PasswordChange, RefreshTokenRequest, LogoutRequest, ResendVerificationRequest
from database import get_database
from middleware.security import limiter
from services.notification_service import NotificationService
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
        created_at=current_user.get("createdAt", datetime.utcnow())
    )

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
    
    return {
        'message': 'Password changed successfully',
        'timestamp': datetime.utcnow().isoformat()
    }

