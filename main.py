from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

from database import init_db, close_db

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
        return ["*"]
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
        print("Heartbeat sweep started")
    except Exception as e:
        print(f"Could not start heartbeat sweep: {e}")
    print("Backend ready")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="IoT Security Platform",
    version="2.0.0",
    lifespan=lifespan
)

# Static web UI
if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")

# CORS - Allow frontend to connect (set CORS_ORIGINS in prod)
cors_origins = _parse_cors_origins(os.getenv("CORS_ORIGINS"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

# Include device routes
from routes.devices import router as devices_router
app.include_router(devices_router, prefix="/api/devices", tags=["Devices"])

# Include alert routes
from routes.alerts import router as alerts_router
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])

# Include heartbeat routes
from routes.heartbeat import router as heartbeat_router
app.include_router(heartbeat_router, prefix="/api/heartbeat", tags=["Heartbeat"])

# Include notification preferences routes
from routes.notification_preferences import router as notification_prefs_router
app.include_router(notification_prefs_router, prefix="/api/notification-preferences", tags=["Notification Preferences"])
