# models.py - Data Models for Pro-Alert
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
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters with uppercase, lowercase, numbers, and special characters")
    role: Literal["consumer", "business", "admin", "user"] = "consumer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)

class UserResponse(UserBase):
    id: str
    role: str
    organization: Optional[Dict[str, Any]] = None
    organization_role: Optional[str] = None
    plan: str = "free"  # free, pro, business
    subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None  # active, cancelled, past_due, etc.
    stripe_customer_id: Optional[str] = None
    mfa_enabled: bool = False
    created_at: datetime

class TokenResponse(BaseModel):
    # Empty when verification_required (signup) so client cannot use dashboard until verified
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    email_verified: Optional[bool] = None
    verification_required: Optional[bool] = None
    user: UserResponse
    message: str = "Authentication successful"

class RefreshTokenRequest(BaseModel):
    """Refresh token from body (legacy) or omit to use httpOnly cookie."""
    refresh_token: Optional[str] = None


class RevokeSessionRequest(BaseModel):
    """Revoke a single session by public session id (from GET /sessions)."""
    session_id: str = Field(..., min_length=8, description="session_public_id from sessions list")

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str
    qr_code_image: str  # Base64 data URI of the QR code image
    backup_codes: List[str]

class MfaVerifyRequest(BaseModel):
    code: str

class MfaDisableRequest(BaseModel):
    code: str

class MfaBackupCodesResponse(BaseModel):
    backup_codes: List[str]

# ============================================================
# DEVICE MODELS
# ============================================================

class DeviceBase(BaseModel):
    device_id: str = Field(..., description="Logical device ID like 'dev-001'")
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Camera, Router, Sensor, etc.")
    router_ip: Optional[str] = Field(None, description="Router/Gateway IP address")
    device_ip: Optional[str] = Field(None, description="Device's actual IP (optional, auto-detected)")

class DeviceCreate(DeviceBase):
    device_id: Optional[str] = Field(None, description="Optional; auto-generated from name if not provided")
    heartbeat_interval: int = Field(30, ge=10, description="Seconds between heartbeats")
    alerts_enabled: bool = True
    offline_only_when_missed_heartbeats: bool = Field(
        False,
        description="If True, device is marked offline only when heartbeats stop (sweep), not from agent reachability. Use for doorbells/cameras that don't respond to port checks.",
    )
    offline_after_seconds: Optional[int] = Field(
        None,
        ge=30,
        le=300,
        description="Seconds without heartbeats before marking offline (overrides default 2× interval). Use 30–45 for high-security devices.",
    )
    organization: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    router_ip: Optional[str] = None
    device_ip: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[Literal["online", "offline", "error", "suspected_jamming"]] = None
    signal_strength: Optional[int] = None
    alerts_enabled: Optional[bool] = None
    heartbeat_interval: Optional[int] = Field(None, ge=10, description="Seconds between heartbeats")
    offline_only_when_missed_heartbeats: Optional[bool] = Field(
        None,
        description="If True, mark offline only when heartbeats are missed; ignore agent-reported offline (recommended for doorbells, cameras).",
    )
    offline_after_seconds: Optional[int] = Field(
        None,
        ge=30,
        le=300,
        description="Seconds without heartbeats before marking offline (30–300). Lower = faster detection for high-security devices.",
    )

class DeviceResponse(DeviceBase):
    id: str
    status: str
    last_seen: Optional[datetime] = None
    heartbeat_interval: int
    alerts_enabled: bool
    offline_only_when_missed_heartbeats: bool = False
    offline_after_seconds: Optional[int] = None
    signal_strength: Optional[int] = None
    ip_address_history: Optional[List[str]] = []
    organization: Optional[str] = None
    groups: Optional[List[str]] = []  # List of group IDs this device belongs to
    created_at: datetime
    updated_at: datetime
    # Keep ip_address for backward compatibility but it's now device_ip
    ip_address: Optional[str] = None  # Deprecated, use device_ip instead

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


class DiscoveryDeviceItem(BaseModel):
    """Single device found on the network (from agent discovery)"""
    ip: str = Field(..., description="IP address")
    hostname: Optional[str] = None
    mac: Optional[str] = None


class DiscoveryPayload(BaseModel):
    """Payload from device agent when it runs discovery"""
    devices: List[DiscoveryDeviceItem] = Field(default_factory=list)


class DiscoveryResponse(BaseModel):
    """Response for GET /api/discovery - devices found on user's network"""
    devices: List[DiscoveryDeviceItem]
    updated_at: Optional[datetime] = None

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

# ============================================================
# NOTIFICATION PREFERENCES MODELS
# ============================================================

class NotificationChannel(BaseModel):
    """Configuration for a notification channel"""
    enabled: bool = True
    email: Optional[str] = None
    phone: Optional[str] = None  # For SMS
    whatsapp: Optional[str] = None  # WhatsApp number

class NotificationPreferences(BaseModel):
    """User notification preferences"""
    email_enabled: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    voice_enabled: bool = False
    
    # Severity thresholds - which severities trigger which channels
    email_severities: List[Literal["low", "medium", "high", "critical"]] = ["low", "medium", "high", "critical"]
    sms_severities: List[Literal["low", "medium", "high", "critical"]] = ["high", "critical"]
    whatsapp_severities: List[Literal["low", "medium", "high", "critical"]] = ["medium", "high", "critical"]
    voice_severities: List[Literal["low", "medium", "high", "critical"]] = ["critical"]
    
    # Contact details
    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    
    # Quiet hours (24h format)
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # e.g., "22:00"
    quiet_hours_end: Optional[str] = None    # e.g., "07:00"
    
    # Escalation settings
    escalation_enabled: bool = True
    escalation_delay_minutes: int = 15  # Wait time before escalating

class NotificationPreferencesResponse(NotificationPreferences):
    """Response model with user ID"""
    user_id: str
    updated_at: datetime


class NotificationPreferencesSaveResponse(NotificationPreferencesResponse):
    """Response when saving preferences: includes verification send results for each channel."""
    verification_sent: Optional[Dict[str, bool]] = None  # e.g. {"email": True, "sms": True, "whatsapp": False, "voice": True}
    verification_failed: Optional[List[Dict[str, str]]] = None  # e.g. [{"channel": "whatsapp", "message": "..."}]

# ============================================================
# FAMILY/HOUSEHOLD SHARING MODELS
# ============================================================

class FamilyBase(BaseModel):
    """Base model for family/household"""
    name: str = Field(..., min_length=1, max_length=100, description="e.g., 'Smith Family' or 'My Home'")
    description: Optional[str] = Field(None, max_length=500)

class FamilyCreate(FamilyBase):
    """Create a new family/household"""
    pass

class FamilyUpdate(BaseModel):
    """Update family details"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class FamilyMember(BaseModel):
    """Family member information"""
    user_id: str
    email: str
    name: str
    role: Literal["admin", "member"] = "member"
    joined_at: datetime
    can_manage_devices: bool = True
    can_resolve_alerts: bool = True
    can_invite_members: bool = False  # Only admin by default

class FamilyResponse(FamilyBase):
    """Family/household with members"""
    id: str
    owner_id: str
    owner_name: str
    owner_email: str
    members: List[FamilyMember] = []
    total_devices: int = 0
    created_at: datetime
    updated_at: datetime

class FamilyInvitationCreate(BaseModel):
    """Invite someone to join family"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: Literal["admin", "member"] = "member"
    can_manage_devices: bool = True
    can_resolve_alerts: bool = True
    can_invite_members: bool = False

class FamilyInvitationResponse(BaseModel):
    """Invitation details"""
    id: str
    family_id: str
    family_name: str
    invited_by_name: str
    invited_by_email: str
    invitee_email: str
    invitee_name: str
    role: str
    status: Literal["pending", "accepted", "declined", "expired"] = "pending"
    token: str
    expires_at: datetime
    created_at: datetime

class AcceptInvitationRequest(BaseModel):
    """Accept family invitation"""
    token: str
    password: Optional[str] = Field(None, min_length=12, description="Password if creating new account")

# ============================================================
# DEVICE GROUPING/TAGS MODELS
# ============================================================

class DeviceGroupBase(BaseModel):
    """Base model for device groups"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: str = Field("#3b82f6", description="Hex color for group badge")

class DeviceGroupCreate(DeviceGroupBase):
    """Create a device group"""
    pass

class DeviceGroupUpdate(BaseModel):
    """Update device group"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = None

class DeviceGroupResponse(DeviceGroupBase):
    """Device group with device count"""
    id: str
    user_id: str
    device_count: int = 0
    created_at: datetime
    updated_at: datetime

# ============================================================
# AUDIT LOG MODELS
# ============================================================

class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: str
    user_id: str
    user_email: str
    user_name: str
    action: str  # login, logout, device_create, device_delete, alert_resolve, etc.
    resource_type: str  # user, device, alert, family, etc.
    resource_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

# ============================================================
# INCIDENT MODELS
# ============================================================

class IncidentNote(BaseModel):
    """Note/comment on an incident"""
    id: str
    incident_id: str
    user_id: str
    user_name: str
    content: str
    created_at: datetime

class IncidentBase(BaseModel):
    """Base incident model"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["open", "investigating", "resolved", "closed"] = "open"

class IncidentCreate(IncidentBase):
    """Create incident request"""
    alert_ids: Optional[List[str]] = []  # Alerts to associate with this incident

class IncidentUpdate(BaseModel):
    """Update incident request"""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    status: Optional[Literal["open", "investigating", "resolved", "closed"]] = None

class IncidentResponse(IncidentBase):
    """Incident response model"""
    id: str
    user_id: str
    alert_ids: List[str] = []
    notes: List[IncidentNote] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    time_to_resolution_minutes: Optional[int] = None

class IncidentNoteCreate(BaseModel):
    """Create incident note request"""
    content: str = Field(..., min_length=1, max_length=5000)

class IncidentListResponse(BaseModel):
    """Paginated incident list response"""
    page: int
    total: int
    incidents: List[IncidentResponse]

class TimelineEvent(BaseModel):
    """Timeline event for incident visualization"""
    id: str
    type: str  # alert, note, status_change, etc.
    timestamp: datetime
    title: str
    description: Optional[str] = None
    severity: Optional[str] = None
    user_name: Optional[str] = None
    metadata: Dict[str, Any] = {}