"""
Startup and shutdown: DB, background tasks, and startup result tracking.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import init_db, close_db

_startup_results: dict = {}


def get_startup_results() -> dict:
    return _startup_results


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _startup_results
    from core.config import MONGO_URI, check_production_config

    _startup_results = {
        "database": "pending",
        "heartbeat_sweep": "pending",
        "device_status_monitor": "pending",
        "retention_cleanup": "pending",
        "network_monitoring": "pending",
        "twilio": "pending",
    }
    print("Starting Pro-Alert Backend...")

    try:
        import twilio  # noqa: F401
        _startup_results["twilio"] = "ok"
    except ModuleNotFoundError:
        _startup_results["twilio"] = "skipped (not installed)"
        print("[NOTIFICATIONS] Twilio not installed. Add 'twilio' to requirements.txt and rebuild if needed.")

    check_production_config()

    try:
        await init_db(MONGO_URI)
        _startup_results["database"] = "ok"
    except Exception as e:
        _startup_results["database"] = f"fail: {e}"
        raise

    try:
        from services.heartbeat_sweep import start_background_sweep
        start_background_sweep()
        _startup_results["heartbeat_sweep"] = "ok"
        print("[OK] Heartbeat sweep started")
    except Exception as e:
        _startup_results["heartbeat_sweep"] = f"fail: {e}"
        print(f"[ERROR] Could not start heartbeat sweep: {e}")

    enable_monitor = os.getenv("ENABLE_DEVICE_STATUS_MONITOR", "true").lower() == "true"
    if enable_monitor:
        try:
            from services.device_status_monitor import start_device_status_monitor
            start_device_status_monitor(interval_seconds=30)
            _startup_results["device_status_monitor"] = "ok"
            print("[OK] Device status monitor started")
        except Exception as e:
            _startup_results["device_status_monitor"] = f"fail: {e}"
            print(f"[ERROR] Could not start device status monitor: {e}")
    else:
        _startup_results["device_status_monitor"] = "disabled"
        print("[INFO] Device status monitor disabled (ENABLE_DEVICE_STATUS_MONITOR=false).")

    try:
        from services.retention_cleanup import start_retention_cleanup_task
        start_retention_cleanup_task()
        _startup_results["retention_cleanup"] = "ok"
        print("[OK] Alert retention cleanup task started")
    except Exception as e:
        _startup_results["retention_cleanup"] = f"fail: {e}"
        print(f"[ERROR] Could not start retention cleanup: {e}")

    try:
        from core.config import get_app_env
        enable_network_monitoring = os.getenv("ENABLE_NETWORK_MONITORING")
        if enable_network_monitoring is None:
            enable_network_monitoring = "false" if get_app_env() in ("local", "development") else "true"
        if enable_network_monitoring.lower() == "true":
            from services.network_monitor import start_network_monitoring
            start_network_monitoring()
            _startup_results["network_monitoring"] = "ok"
            print("[OK] Network monitoring started")
        else:
            _startup_results["network_monitoring"] = "disabled"
    except Exception as e:
        _startup_results["network_monitoring"] = f"fail: {e}"
        print(f"[ERROR] Could not start network monitoring: {e}")

    try:
        from services.notification_service import get_notification_service
        svc = get_notification_service()
        twilio_ok = bool(svc.twilio_account_sid and svc.twilio_auth_token)
        print("[NOTIFICATIONS] Twilio configured:", twilio_ok, "| SMS enabled:", svc.sms_enabled)
        if not twilio_ok:
            print("[NOTIFICATIONS] Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env.")
    except Exception as e:
        print(f"[NOTIFICATIONS] Status check failed: {e}")
    print("Backend ready")

    yield

    print("Shutting down...")
    await close_db()
    print("Shutdown complete")
