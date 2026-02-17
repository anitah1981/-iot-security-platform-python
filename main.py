from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import os
from pathlib import Path
from urllib.parse import urlparse
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


def _check_production_config():
    """Fail fast with clear error if critical production config is missing."""
    if os.getenv("APP_ENV", "local").lower() != "production":
        return
    if not MONGO_URI or "localhost" in MONGO_URI or "127.0.0.1" in MONGO_URI:
        print("[FATAL] MONGO_URI is not set or still points to localhost.")
        print("In Railway: Service -> Variables -> Add MONGO_URI with your MongoDB Atlas connection string.")
        print("Example: mongodb+srv://user:pass@cluster.mongodb.net/iot_security?retryWrites=true&w=majority")
        raise SystemExit(1)

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
    print("Starting Alert-Pro Backend...")
    # Ensure twilio is available in THIS process (fixes "Twilio package not installed" when app is run from IDE/different Python)
    try:
        import twilio  # noqa: F401
    except ModuleNotFoundError:
        import subprocess
        import sys
        print("[NOTIFICATIONS] Twilio not found in this Python - installing with pip...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "twilio"],
                capture_output=True,
                timeout=120,
                check=True,
            )
            print("[NOTIFICATIONS] Twilio installed successfully.")
        except Exception as e:
            print(f"[NOTIFICATIONS] Could not auto-install twilio: {e}. Run: {sys.executable} -m pip install twilio")
    _check_production_config()
    await init_db(MONGO_URI)
    # Start background monitoring tasks (best-effort)
    try:
        from services.heartbeat_sweep import start_background_sweep
        start_background_sweep()
        print("[OK] Heartbeat sweep started")
    except Exception as e:
        print(f"[ERROR] Could not start heartbeat sweep: {e}")
    
    # Start device status monitor (active network checks)
    try:
        from services.device_status_monitor import start_device_status_monitor
        start_device_status_monitor(interval_seconds=30)
        print("[OK] Device status monitor started")
    except Exception as e:
        print(f"[ERROR] Could not start device status monitor: {e}")
        import traceback
        traceback.print_exc()
    
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
    
    # Log notification/Twilio status so user can see why SMS/WhatsApp/Voice might not send
    try:
        from services.notification_service import get_notification_service
        svc = get_notification_service()
        twilio_ok = bool(svc.twilio_account_sid and svc.twilio_auth_token)
        print("[NOTIFICATIONS] Twilio configured:", twilio_ok, "| SMS enabled:", svc.sms_enabled, "| Voice ready:", svc._voice_ready(), "| WhatsApp ready:", svc._whatsapp_ready())
        if not twilio_ok:
            print("[NOTIFICATIONS] Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env for SMS/WhatsApp/Voice. Restart app after changing .env.")
    except Exception as e:
        print(f"[NOTIFICATIONS] Status check failed: {e}")
    print("Backend ready")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Shutdown complete")

# Create FastAPI app
# Disable public docs - require authentication
app = FastAPI(
    title="Alert-Pro",
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
    # Auto-add host from APP_BASE_URL so Railway URL works without setting ALLOWED_HOSTS
    app_base = os.getenv("APP_BASE_URL", "").strip()
    if app_base:
        try:
            host = urlparse(app_base).hostname
            if host and host not in allowed_hosts:
                allowed_hosts.append(host)
        except Exception:
            pass
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

@app.get("/security-compliance")
def security_compliance_page():
    f = WEB_DIR / "security-compliance.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/")
def root():
    landing = WEB_DIR / "landing.html"
    if landing.exists():
        return FileResponse(str(landing))
    index = WEB_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Alert-Pro API", "version": "2.0.0", "status": "running"}

@app.get("/login")
def login_page():
    f = WEB_DIR / "login.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/signup")
def signup_page():
    f = WEB_DIR / "signup.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

def _check_auth_for_page(request: Request) -> bool:
    """Check if user is authenticated for HTML page access"""
    # Check for Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return True
    
    # Check for token in cookie (if we set it)
    token_cookie = request.cookies.get("auth_token")
    if token_cookie:
        return True
    
    # For HTML pages, we'll rely on client-side check
    # But we can check if there's any indication of auth
    return False

@app.get("/dashboard")
def dashboard_page(request: Request):
    f = WEB_DIR / "dashboard.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/settings")
def settings_page(request: Request):
    f = WEB_DIR / "settings.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/pricing")
def pricing_page():
    f = WEB_DIR / "pricing.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/forgot-password")
def forgot_password_page():
    f = WEB_DIR / "forgot-password.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/reset-password")
def reset_password_page():
    f = WEB_DIR / "reset-password.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/verify-email")
def verify_email_page():
    f = WEB_DIR / "verify-email.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/terms")
def terms_page():
    f = WEB_DIR / "terms.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/privacy")
def privacy_page():
    f = WEB_DIR / "privacy.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
    return FileResponse(str(f))

@app.get("/family")
def family_page():
    f = WEB_DIR / "family.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
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
        "service": "alert-pro",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }

# Include authentication routes
from routes.auth import router as auth_router
from routes.auth import get_current_user
from fastapi import Cookie
from fastapi.responses import RedirectResponse
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


if __name__ == "__main__":
    import uvicorn
    print(f"[INFO] Starting IoT Security Platform on http://localhost:{PORT}")
    print(f"[INFO] Environment: {os.getenv('APP_ENV', 'local')}")
    print(f"[INFO] MongoDB: {MONGO_URI.split('@')[1] if '@' in MONGO_URI else 'localhost'}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
