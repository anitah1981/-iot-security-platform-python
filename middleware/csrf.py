"""
CSRF Protection Middleware
Implements Cross-Site Request Forgery protection for state-changing operations
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import secrets
import hashlib
import os


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection for state-changing HTTP methods (POST, PUT, DELETE, PATCH).
    
    CIA Principle: Integrity - Ensures requests originate from legitimate sources.
    """
    
    # Methods that require CSRF protection
    PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
    
    # Endpoints that are exempt from CSRF (e.g., webhooks, public APIs)
    EXEMPT_PATHS = [
        "/api/heartbeat",  # Device agent endpoints
        "/api/webhooks",   # External webhooks
        "/api/health",     # Health checks
    ]
    
    def __init__(self, app):
        super().__init__(app)
        self.csrf_secret = os.getenv("CSRF_SECRET", secrets.token_urlsafe(32))
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection"""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)
    
    def _generate_token(self) -> str:
        """Generate a CSRF token"""
        return secrets.token_urlsafe(32)
    
    def _get_token_from_header(self, request: Request) -> str:
        """Extract CSRF token from X-CSRF-Token header"""
        return request.headers.get("X-CSRF-Token", "").strip()
    
    def _get_token_from_cookie(self, request: Request) -> str:
        """Extract CSRF token from csrftoken cookie"""
        return request.cookies.get("csrftoken", "").strip()
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip CSRF check for exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)
        
        # Only protect state-changing methods
        if request.method not in self.PROTECTED_METHODS:
            return await call_next(request)
        
        # Get tokens
        header_token = self._get_token_from_header(request)
        cookie_token = self._get_token_from_cookie(request)
        
        # Validate CSRF token
        if not header_token or not cookie_token:
            print(f"[CSRF] Missing CSRF token for {request.method} {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing"
            )
        
        if header_token != cookie_token:
            print(f"[CSRF] CSRF token mismatch for {request.method} {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token mismatch"
            )
        
        return await call_next(request)


def get_csrf_token(request: Request) -> str:
    """Get CSRF token from cookie (for templates)"""
    return request.cookies.get("csrftoken", "")
