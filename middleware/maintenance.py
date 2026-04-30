"""
Optional full public outage while keeping liveness endpoints for Railway.
Set MAINTENANCE_MODE=true (or 1, yes, on) on the host.
"""

import os
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _maintenance_enabled() -> bool:
    v = (os.getenv("MAINTENANCE_MODE") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


# Paths that still respond normally (deploy health, ops ping)
_ALLOW_WHEN_MAINTENANCE = frozenset(
    {
        ("/api/health", "GET"),
        ("/api/ready", "GET"),
    }
)


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not _maintenance_enabled():
            return await call_next(request)

        path = request.url.path
        key = (path, request.method.upper())
        if key in _ALLOW_WHEN_MAINTENANCE:
            return await call_next(request)

        return JSONResponse(
            status_code=503,
            content={
                "detail": "Service temporarily unavailable",
                "maintenance": True,
            },
            headers={"Retry-After": "3600"},
        )
