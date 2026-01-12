# routes/auth.py - Authentication Routes
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
import os
import bcrypt as bcrypt_lib

from models import UserCreate, UserLogin, UserResponse, TokenResponse, PasswordChange
from database import get_database
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
JWT_EXPIRES_DAYS = 7

def create_access_token(user_id: str, role: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRES_DAYS)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
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
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
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
    user_doc = {
        "name": user_data.name,
        "email": email,
        "password": hashed_password,
        "role": user_data.role,
        "organization": None,
        "organizationRole": "member",
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
        created_at=user_doc["createdAt"]
    )
    
    # Generate JWT
    token = create_access_token(user_id, user_doc["role"])
    
    return TokenResponse(
        token=token,
        user=safe_user,
        message="Signup successful"
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
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
    
    # Verify password
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
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
        created_at=user.get("createdAt", datetime.utcnow())
    )
    
    # Generate JWT
    token = create_access_token(user_id, user["role"])
    
    return TokenResponse(
        token=token,
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
@router.post("/change-password")
async def change_password(password_data: PasswordChange, user: dict = Depends(get_current_user)):
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

