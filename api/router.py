"""
API router: health/ready/startup and all API sub-routers.
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from routes.auth import router as auth_router
from routes.devices import router as devices_router
from routes.network_settings import router as network_settings_router
from routes.alerts import router as alerts_router
from routes.heartbeat import router as heartbeat_router
from routes.device_agent_key import router as device_agent_key_router
from routes.agent_security import router as agent_security_router
from routes.discovery import router as discovery_router
from routes.notification_preferences import router as notification_prefs_router
from routes.analytics import router as analytics_router
from routes.family import router as family_router
from routes.exports import router as exports_router
from routes.groups import router as groups_router
from routes.audit import router as audit_router
from routes.incidents import router as incidents_router
from routes.network import router as network_router


def get_api_router():
    from core.startup import get_startup_results

    router = APIRouter()

    @router.get("/health")
    def health():
        # Expose whether email (password reset, verification, alerts) can be sent - no secrets
        email_configured = bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD") and os.getenv("FROM_EMAIL"))
        return {
            "ok": True,
            "service": "alert-pro",
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "email_configured": email_configured,
        }

    @router.get("/ready")
    async def ready():
        try:
            from database import get_database
            db = await get_database()
            await db.command("ping")
            return {
                "ok": True,
                "database": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "ok": False,
                    "database": "disconnected",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

    @router.get("/startup")
    def startup_status():
        return {
            "ok": True,
            "tasks": get_startup_results(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    router.include_router(devices_router, prefix="/devices", tags=["Devices"])
    router.include_router(network_settings_router, prefix="/network-settings", tags=["Network Settings"])
    router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
    router.include_router(heartbeat_router, prefix="/heartbeat", tags=["Heartbeat"])
    router.include_router(device_agent_key_router, prefix="/device-agent-key", tags=["Device Agent Key"])
    router.include_router(agent_security_router, prefix="/agent", tags=["Agent Security"])
    router.include_router(discovery_router, prefix="/discovery", tags=["Discovery"])
    router.include_router(notification_prefs_router, prefix="/notification-preferences", tags=["Notification Preferences"])
    router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
    router.include_router(family_router, prefix="/family", tags=["Family Sharing"])
    router.include_router(exports_router, prefix="/alerts/export", tags=["Exports"])
    router.include_router(groups_router, prefix="/groups", tags=["Device Groups"])
    router.include_router(audit_router, prefix="/audit", tags=["Audit Logs"])
    router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
    router.include_router(network_router, prefix="/network", tags=["Network Monitoring"])

    return router
