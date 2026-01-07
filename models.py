# models.py - Data Models for IoT Security Platform
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from bson import ObjectId

# ============================================================
# USER MODELS
# ============================================================

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: Literal["consumer", "business", "admin", "user"] = "consumer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    role: str
    organization: Optional[Dict[str, Any]] = None
    organization_role: Optional[str] = None
    created_at: datetime

class TokenResponse(BaseModel):
    token: str
    user: UserResponse
    message: str = "Authentication successful"

# ============================================================
# DEVICE MODELS
# ============================================================

class DeviceBase(BaseModel):
    device_id: str = Field(..., description="Logical device ID like 'dev-001'")
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Camera, Router, Sensor, etc.")
    ip_address: str = Field(..., pattern=r'^(\d{1,3}\.){3}\d{1,3}$')

class DeviceCreate(DeviceBase):
    heartbeat_interval: int = Field(30, ge=10, description="Seconds between heartbeats")
    alerts_enabled: bool = True
    organization: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[Literal["online", "offline", "error", "suspected_jamming"]] = None
    signal_strength: Optional[int] = None
    alerts_enabled: Optional[bool] = None

class DeviceResponse(DeviceBase):
    id: str
    status: str
    last_seen: Optional[datetime] = None
    heartbeat_interval: int
    alerts_enabled: bool
    signal_strength: Optional[int] = None
    ip_address_history: Optional[List[str]] = []
    organization: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DeviceListResponse(BaseModel):
    page: int
    total: int
    devices: List[DeviceResponse]

# ============================================================
# ALERT MODELS
# ============================================================

class AlertBase(BaseModel):
    device_id: str = Field(..., description="Device MongoDB ObjectId")
    message: str = Field(..., min_length=1)
    severity: Literal["low", "medium", "high", "critical"]
    type: Literal["connectivity", "power", "security", "system"]

class AlertCreate(AlertBase):
    context: Optional[Dict[str, Any]] = {}

class AlertResponse(AlertBase):
    id: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    context: Dict[str, Any] = {}
    created_at: datetime
    device: Optional[Dict[str, Any]] = None

class AlertListResponse(BaseModel):
    page: int
    total: int
    alerts: List[AlertResponse]

# ============================================================
# ORGANIZATION MODELS
# ============================================================

class OrganizationSettings(BaseModel):
    max_devices: int = 10
    alert_retention_days: int = 30
    allowed_device_types: List[str] = ["Camera", "Sensor", "Router"]

class OrganizationBilling(BaseModel):
    stripe_customer_id: Optional[str] = None
    subscription_status: str = "inactive"

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    subdomain: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-z0-9]+$')

class OrganizationCreate(OrganizationBase):
    plan: Literal["free", "pro", "enterprise"] = "free"

class OrganizationResponse(OrganizationBase):
    id: str
    plan: str
    settings: OrganizationSettings
    billing: OrganizationBilling
    created_at: datetime
    member_count: int = 0
    device_count: int = 0

# ============================================================
# MONITORING MODELS
# ============================================================

class HeartbeatData(BaseModel):
    device_id: str = Field(..., description="Logical device ID")
    ip_address: Optional[str] = None
    signal_strength: Optional[int] = Field(None, ge=-100, le=0)
    status: Literal["online", "offline", "error"] = "online"
    metadata: Optional[Dict[str, Any]] = None

class HeartbeatResponse(BaseModel):
    success: bool
    device_id: str
    status: str
    message: str
    last_seen: datetime

# ============================================================
# PAGINATION & FILTERS
# ============================================================

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)

class DeviceFilters(PaginationParams):
    type: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None
    organization: Optional[str] = None

class AlertFilters(PaginationParams):
    device_id: Optional[str] = None
    severity: Optional[str] = None
    type: Optional[str] = None
    since: Optional[datetime] = None
    organization: Optional[str] = None