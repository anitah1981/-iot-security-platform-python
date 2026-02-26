"""
Security Middleware
Implements comprehensive security measures for the API
"""

import time
import uuid
from typing import Callable

import os
import secrets
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from utils.structured_log import get_logger

log = get_logger("security")


# Rate limiter configuration
default_limit = os.getenv("RATE_LIMIT_DEFAULT", "120/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[default_limit])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if os.getenv("ENABLE_HSTS", "true").lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Set request_id on state for correlation in logs."""
    async def dispatch(self, request: Request, call_next: Callable):
        request.state.request_id = str(uuid.uuid4())[:8]
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request logging with severity and optional request_id."""
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        rid = getattr(request.state, "request_id", None)
        client_host = request.client.host if request.client else "unknown"
        extra = {"request_id": rid} if rid else {}
        log.info("IN %s %s from %s", request.method, request.url.path, client_host, extra=extra)
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            log.info("OUT %s %s %s %.3fs", request.method, request.url.path, response.status_code, process_time, extra=extra)
            return response
        except Exception as e:
            log.error("ERROR %s %s: %s", request.method, request.url.path, str(e), extra=extra)
            raise


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Minimal request hardening: path traversal only.
    XSS/SQL injection are handled by Pydantic validation and context-aware escaping in responses.
    Keep rules here auditable and minimal to avoid false positives/negatives.
    """
    # Path traversal only; do not block query/body by substring (validation is per-endpoint)
    PATH_TRAVERSAL = ("../", "..\\")

    async def dispatch(self, request: Request, call_next: Callable):
        url_path = request.url.path
        for pattern in self.PATH_TRAVERSAL:
            if pattern in url_path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid path",
                )
        return await call_next(request)


class HttpsRedirectMiddleware(BaseHTTPMiddleware):
    """Force HTTPS in production behind a proxy."""
    
    def __init__(self, app, allowed_hosts: list = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or []

    async def dispatch(self, request: Request, call_next: Callable):
        # Check if we should enforce HTTPS
        # Skip for health checks, static files, and internal endpoints
        path = request.url.path
        if path in ["/api/health", "/api/ready", "/health"] or path.startswith("/assets/") or path.startswith("/static/"):
            return await call_next(request)
        
        # Check host header if allowed_hosts specified
        host = request.headers.get("host", "").split(":")[0]
        if self.allowed_hosts and host not in self.allowed_hosts:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Forbidden"}
            )
        
        # Check protocol via X-Forwarded-Proto (when behind proxy) or direct scheme
        forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
        scheme = forwarded_proto or request.url.scheme
        
        if scheme != "https":
            # Build HTTPS URL
            https_url = request.url.replace(scheme="https", port=443 if request.url.port else None)
            return RedirectResponse(url=str(https_url), status_code=307)
        
        return await call_next(request)


def setup_rate_limiting(app):
    """Configure rate limiting for the application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return limiter
