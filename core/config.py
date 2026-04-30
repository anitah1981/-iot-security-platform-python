"""
Application configuration. Load env once at import; validate on production startup.
"""
import os
from pathlib import Path
from urllib.parse import urlparse

# Load environment as soon as this module is imported
from dotenv import load_dotenv
load_dotenv()

# Sentry (optional) - init when SENTRY_DSN is set
_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
sentry_enabled = False
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(
            dsn=_sentry_dsn,
            environment=os.getenv("APP_ENV", "local"),
            release=os.getenv("SENTRY_RELEASE", "pro-alert@2.0.0"),
            traces_sample_rate=0.1,
            integrations=[FastApiIntegration()],
        )
        sentry_enabled = True
    except Exception as e:
        # Log explicitly so Sentry misconfiguration is visible in logs.
        print(f"[SENTRY] Initialization failed: {e}")

# Paths and core settings
BASE_DIR = Path(__file__).resolve().parent.parent
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/iot_security")
PORT = int(os.getenv("PORT", "8000"))
WEB_DIR = BASE_DIR / "web"


def get_app_env() -> str:
    return os.getenv("APP_ENV", "local").lower()


def get_public_app_base_url() -> str:
    """
    Base URL for browser redirects (Stripe checkout, customer portal, etc.).
    No trailing slash. Uses APP_BASE_URL; falls back to local dev URL.
    """
    raw = (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")
    if raw:
        return raw
    return "http://localhost:8000"


def check_production_config() -> None:
    """Fail fast if critical production config is missing. Single startup validator."""
    env = get_app_env()
    if env != "production":
        return
    errors = []
    if not MONGO_URI or "localhost" in MONGO_URI or "127.0.0.1" in MONGO_URI:
        errors.append(
            "MONGO_URI is not set or points to localhost. Set to MongoDB Atlas (e.g. mongodb+srv://...)."
        )
    jwt_secret = os.getenv("JWT_SECRET", "")
    if not jwt_secret or jwt_secret.strip() in ("change-me-in-production", "changeme", "secret"):
        errors.append("JWT_SECRET must be set to a strong random value in production.")
    app_base = os.getenv("APP_BASE_URL", "").strip()
    if not app_base:
        errors.append("APP_BASE_URL must be set (e.g. https://your-app.up.railway.app).")
    elif not app_base.lower().startswith("https://"):
        errors.append("APP_BASE_URL should use https:// in production.")
    cors = os.getenv("CORS_ORIGINS", "").strip()
    if not cors:
        errors.append("CORS_ORIGINS should be set to your frontend origin(s), e.g. https://your-app.example.com")
    allowed = os.getenv("ALLOWED_HOSTS", "").strip()
    if not allowed and not app_base:
        errors.append("ALLOWED_HOSTS or APP_BASE_URL must be set for host validation.")
    if errors:
        print("[FATAL] Production config validation failed:")
        for e in errors:
            print(f"  - {e}")
        print("Fix the above and restart. See .env.example and deployment docs.")
        raise SystemExit(1)


def _expand_www_apex_variants(hosts: list[str]) -> list[str]:
    """
    Allow both www and bare apex when either is listed or derived from APP_BASE_URL,
    so https://pro-alert.co.uk and https://www.pro-alert.co.uk both pass host checks.
    Skips Railway and local dev hostnames.
    """
    out: list[str] = []
    seen: set[str] = set()
    for h in hosts:
        h = (h or "").strip().lower()
        if not h or h in seen:
            continue
        seen.add(h)
        out.append(h)
        if h == "healthcheck.railway.app" or h.endswith(".railway.app"):
            continue
        if h in ("localhost", "127.0.0.1"):
            continue
        if h.startswith("www."):
            bare = h[4:]
            if bare and bare not in seen:
                seen.add(bare)
                out.append(bare)
        else:
            www_h = "www." + h
            if www_h not in seen:
                seen.add(www_h)
                out.append(www_h)
    return out


def parse_cors_origins(raw: str | None) -> list[str]:
    """
    CORS_ORIGINS: "*" (dev) or comma-separated origins.
    """
    if not raw:
        if get_app_env() in ("local", "development"):
            return ["http://localhost:8000", "http://127.0.0.1:8000"]
        return []
    raw = raw.strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def get_allowed_hosts_for_https() -> list[str] | None:
    """For HttpsRedirectMiddleware in production."""
    app_env = get_app_env()
    if app_env != "production" or os.getenv("FORCE_HTTPS", "true").lower() != "true":
        return None
    raw = os.getenv("ALLOWED_HOSTS", "").split(",")
    hosts = [h.strip() for h in raw if h.strip()]
    app_base = os.getenv("APP_BASE_URL", "").strip()
    if app_base:
        try:
            host = urlparse(app_base).hostname
            if host:
                h_lower = host.lower()
                if h_lower not in {x.lower() for x in hosts}:
                    hosts.append(host)
        except Exception:
            pass
    if not hosts:
        return None
    return _expand_www_apex_variants(hosts)


def get_trusted_hosts() -> list[str]:
    """For TrustedHostMiddleware when not local/dev."""
    app_env = get_app_env()
    if app_env in ("local", "development"):
        return []
    hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    hosts = [h.strip() for h in hosts if h.strip()]
    app_base = os.getenv("APP_BASE_URL", "").strip()
    if app_base:
        try:
            host = urlparse(app_base).hostname
            if host:
                h_lower = host.lower()
                if h_lower not in {x.lower() for x in hosts}:
                    hosts.append(host)
        except Exception:
            pass
    return _expand_www_apex_variants(hosts)


def get_cors_origins() -> list[str]:
    return parse_cors_origins(os.getenv("CORS_ORIGINS"))
