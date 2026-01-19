"""
Security Middleware
Implements comprehensive security measures for the API
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
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
        
        # Log request
        print(f"📥 {request.method} {request.url.path} from {request.client.host}")
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            print(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
            
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


def setup_rate_limiting(app):
    """Configure rate limiting for the application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return limiter
