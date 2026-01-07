from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import os
from dotenv import load_dotenv

from database import init_db, close_db

# Load environment variables
load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_security")
PORT = int(os.getenv("PORT", 8000))

# Lifespan - runs on startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown"""
    # Startup
    print("🚀 Starting IoT Security Backend...")
    await init_db(MONGO_URI)
    print("✅ Backend ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await close_db()
    print("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="IoT Security Platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "IoT Security Platform API",
        "version": "2.0.0",
        "status": "running"
    }

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
