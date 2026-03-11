"""
Wire security, rate limiting, trusted host, CORS, and production exception handler.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from middleware.security import (
    SecurityHeadersMiddleware,
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    InputSanitizationMiddleware,
    HttpsRedirectMiddleware,
    setup_rate_limiting,
)
from middleware.csrf import CSRFProtectionMiddleware


def setup_middleware(app: FastAPI) -> None:
    from core.config import (
        get_app_env,
        get_allowed_hosts_for_https,
        get_trusted_hosts,
        get_cors_origins,
        sentry_enabled,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(InputSanitizationMiddleware)
    app.add_middleware(CSRFProtectionMiddleware)

    setup_rate_limiting(app)

    allowed_https = get_allowed_hosts_for_https()
    if allowed_https is not None:
        app.add_middleware(HttpsRedirectMiddleware, allowed_hosts=allowed_https)

    trusted = get_trusted_hosts()
    if trusted:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted)

    app_env = get_app_env()
    if app_env == "production":

        @app.exception_handler(Exception)
        async def production_exception_handler(request: Request, exc: Exception):
            if sentry_enabled:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(exc)
                except Exception:
                    # If Sentry itself fails, fall back to logs only.
                    print(f"[SENTRY] capture_exception failed: {exc}")
            rid = getattr(request.state, "request_id", None)
            print(f"[ERROR] Unhandled exception: {exc} (request_id={rid})")
            payload = {"detail": "Internal server error"}
            if rid:
                payload["request_id"] = rid
            return JSONResponse(status_code=500, content=payload)

    cors_origins = get_cors_origins()
    allow_credentials = "*" not in cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
