"""
Security Middleware
Implements comprehensive security measures for the API
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from typing import Callable
import os
import secrets


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


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security audit"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Log request (ASCII only for Windows consoles)
        client_host = request.client.host if request.client else "unknown"
        print(f"[IN] {request.method} {request.url.path} from {client_host}")
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            print(f"[OUT] {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
            
            return response
        except Exception as e:
            print(f"[ERROR] {request.method} {request.url.path} - ERROR: {str(e)}")
            raise


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize and validate input data"""
    
    SUSPICIOUS_PATTERNS = [
        "<script", "javascript:", "onerror=", "onload=",
        "../", "..\\", "DROP TABLE", "DELETE FROM",
        "INSERT INTO", "UPDATE ", "UNION SELECT"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check URL for suspicious patterns
        url_path = str(request.url.path).lower()
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.lower() in url_path:
                print(f"[SECURITY] Suspicious pattern detected in URL: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request"
                )
        
        # Check query parameters
        for key, value in request.query_params.items():
            value_lower = str(value).lower()
            for pattern in self.SUSPICIOUS_PATTERNS:
                if pattern.lower() in value_lower:
                    print(f"[SECURITY] Suspicious pattern detected in query param {key}: {pattern}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid request parameters"
                    )
        
        response = await call_next(request)
        return response


class HttpsRedirectMiddleware(BaseHTTPMiddleware):
    """Force HTTPS in production behind a proxy."""
    
    def __init__(self, app, allowed_hosts: list = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or []

    async def dispatch(self, request: Request, call_next: Callable):
        # Check if we should enforce HTTPS
        # Skip for health checks, static files, and internal endpoints
        path = request.url.path
        if path in ["/api/health", "/health"] or path.startswith("/assets/") or path.startswith("/static/"):
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
