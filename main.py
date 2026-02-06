from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
import socketio

from database import init_db, close_db
# from services.websocket_service import sio, socket_app
from middleware.security import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    InputSanitizationMiddleware,
    HttpsRedirectMiddleware,
    setup_rate_limiting
)

# Load environment variables
load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_security")
PORT = int(os.getenv("PORT", 8000))
WEB_DIR = Path(__file__).parent / "web"

def _parse_cors_origins(raw: str | None) -> list[str]:
    """
    CORS_ORIGINS:
    - "*" (dev) OR
    - comma-separated list of origins: "https://app.example.com,https://example.com"
    """
    if not raw:
        env = os.getenv("APP_ENV", "local")
        if env.lower() in ["local", "development"]:
            return ["http://localhost:8000", "http://127.0.0.1:8000"]
        return []
    raw = raw.strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

# Lifespan - runs on startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown"""
    # Startup
    print("Starting IoT Security Backend...")
    await init_db(MONGO_URI)
    # Start background monitoring tasks (best-effort)
    try:
        from services.heartbeat_sweep import start_background_sweep
        start_background_sweep()
        print("[OK] Heartbeat sweep started")
    except Exception as e:
        print(f"[ERROR] Could not start heartbeat sweep: {e}")
    
    # Start alert retention cleanup task
    try:
        from services.retention_cleanup import start_retention_cleanup_task
        start_retention_cleanup_task()
        print("[OK] Alert retention cleanup task started")
    except Exception as e:
        print(f"[ERROR] Could not start retention cleanup: {e}")
    
    # Start network monitoring task (optional)
    try:
        enable_network_monitoring = os.getenv("ENABLE_NETWORK_MONITORING")
        if enable_network_monitoring is None:
            enable_network_monitoring = "false" if os.getenv("APP_ENV", "local").lower() in ["local", "development"] else "true"
        if enable_network_monitoring.lower() == "true":
            from services.network_monitor import start_network_monitoring
            start_network_monitoring()
            print("[OK] Network monitoring started")
        else:
            print("[INFO] Network monitoring disabled (ENABLE_NETWORK_MONITORING=false)")
    except Exception as e:
        print(f"[ERROR] Could not start network monitoring: {e}")
    
    print("Backend ready")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Shutdown complete")

# Create FastAPI app
# Disable public docs - require authentication
app = FastAPI(
    title="IoT Security Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable public Swagger UI
    redoc_url=None  # Disable public ReDoc
)

# Static web UI
if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")

# Security Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(InputSanitizationMiddleware)

# Rate Limiting
limiter = setup_rate_limiting(app)

# Trusted hosts (enable only outside local/dev)
app_env = os.getenv("APP_ENV", "local").lower()
force_https = os.getenv("FORCE_HTTPS", "true").lower() == "true"
if app_env == "production" and force_https:
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
    allowed_hosts = [h.strip() for h in allowed_hosts if h.strip()]
    app.add_middleware(HttpsRedirectMiddleware, allowed_hosts=allowed_hosts if allowed_hosts else None)
if app_env not in ["local", "development"]:
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    allowed_hosts = [h.strip() for h in allowed_hosts if h.strip()]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

if app_env == "production":
    @app.exception_handler(Exception)
    async def production_exception_handler(request: Request, exc: Exception):
        print(f"[ERROR] Unhandled exception: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# CORS - Allow frontend to connect (set CORS_ORIGINS in prod)
cors_origins = _parse_cors_origins(os.getenv("CORS_ORIGINS"))
allow_credentials = "*" not in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/cybersecurity-threats")
async def cybersecurity_threats_page():
    f = WEB_DIR / "cybersecurity-threats.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": f"File not found: {f}"})
    return FileResponse(str(f), media_type="text/html")

@app.get("/security-threats")  # Alternative shorter route
async def security_threats_page():
    f = WEB_DIR / "cybersecurity-threats.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": f"File not found: {f}"})
    return FileResponse(str(f), media_type="text/html")

@app.get("/")
def root():
    landing = WEB_DIR / "landing.html"
    if landing.exists():
        return FileResponse(str(landing))
    index = WEB_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "IoT Security Platform API", "version": "2.0.0", "status": "running"}

@app.get("/login")
def login_page():
    f = WEB_DIR / "login.html"
    return FileResponse(str(f))

@app.get("/signup")
def signup_page():
    f = WEB_DIR / "signup.html"
    return FileResponse(str(f))

@app.get("/dashboard")
def dashboard_page():
    f = WEB_DIR / "dashboard.html"
    return FileResponse(str(f))

@app.get("/settings")
def settings_page():
    f = WEB_DIR / "settings.html"
    return FileResponse(str(f))

@app.get("/pricing")
def pricing_page():
    f = WEB_DIR / "pricing.html"
    return FileResponse(str(f))

@app.get("/forgot-password")
def forgot_password_page():
    f = WEB_DIR / "forgot-password.html"
    return FileResponse(str(f))

@app.get("/reset-password")
def reset_password_page():
    f = WEB_DIR / "reset-password.html"
    return FileResponse(str(f))

@app.get("/verify-email")
def verify_email_page():
    f = WEB_DIR / "verify-email.html"
    return FileResponse(str(f))

@app.get("/terms")
def terms_page():
    f = WEB_DIR / "terms.html"
    return FileResponse(str(f))

@app.get("/privacy")
def privacy_page():
    f = WEB_DIR / "privacy.html"
    return FileResponse(str(f))

@app.get("/family")
def family_page():
    f = WEB_DIR / "family.html"
    return FileResponse(str(f))

@app.get("/audit-logs")
def audit_logs_page():
    f = WEB_DIR / "audit-logs.html"
    return FileResponse(str(f))

@app.get("/incidents")
def incidents_page():
    f = WEB_DIR / "incidents.html"
    return FileResponse(str(f))

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "iot-security-platform",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }

# Include authentication routes
from routes.auth import router as auth_router
from routes.auth import get_current_user
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

# Protected API Documentation - Only for authenticated users
@app.get("/docs")
async def get_docs(user: dict = Depends(get_current_user)):
    """API documentation - requires authentication"""
    from fastapi.openapi.docs import get_swagger_ui_html
    
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
    )

@app.get("/redoc")
async def get_redoc(user: dict = Depends(get_current_user)):
    """ReDoc API documentation - requires authentication"""
    from fastapi.openapi.docs import get_redoc_html
    
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )

# Include device routes
from routes.devices import router as devices_router
app.include_router(devices_router, prefix="/api/devices", tags=["Devices"])

# Network settings routes
from routes.network_settings import router as network_settings_router
app.include_router(network_settings_router, prefix="/api/network-settings", tags=["Network Settings"])

# Include alert routes
from routes.alerts import router as alerts_router
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])

# Include heartbeat routes
from routes.heartbeat import router as heartbeat_router
app.include_router(heartbeat_router, prefix="/api/heartbeat", tags=["Heartbeat"])

# Device agent API key (for connecting real devices via heartbeats)
from routes.device_agent_key import router as device_agent_key_router
app.include_router(device_agent_key_router, prefix="/api/device-agent-key", tags=["Device Agent Key"])

# Discovery (agent posts devices found on network; app fetches for "Discover devices")
from routes.discovery import router as discovery_router
app.include_router(discovery_router, prefix="/api/discovery", tags=["Discovery"])

# Include notification preferences routes
from routes.notification_preferences import router as notification_prefs_router
app.include_router(notification_prefs_router, prefix="/api/notification-preferences", tags=["Notification Preferences"])

# 6) Payments (Stripe)
from routes.payments import router as payments_router
app.include_router(payments_router)

# 7) Password Reset
from routes.password_reset import router as password_reset_router
app.include_router(password_reset_router)

# 8) Analytics & Dashboard Charts
from routes.analytics import router as analytics_router
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

# 9) Family/Household Sharing
from routes.family import router as family_router
app.include_router(family_router, prefix="/api/family", tags=["Family Sharing"])

# 10) Alert Exports (PDF & CSV)
from routes.exports import router as exports_router
app.include_router(exports_router, prefix="/api/alerts/export", tags=["Exports"])

# 11) Device Grouping/Tags
from routes.groups import router as groups_router
app.include_router(groups_router, prefix="/api/groups", tags=["Device Groups"])

# 12) Audit Logs
from routes.audit import router as audit_router
app.include_router(audit_router, prefix="/api/audit", tags=["Audit Logs"])

from routes.incidents import router as incidents_router
app.include_router(incidents_router, prefix="/api/incidents", tags=["Incidents"])

# Network monitoring routes
from routes.network import router as network_router
app.include_router(network_router, prefix="/api/network", tags=["Network Monitoring"])

# Mount Socket.IO for real-time updates - Temporarily disabled
# app.mount("/socket.io", socket_app)
