"""
Pro-Alert FastAPI application. Config, startup, middleware, and routes are in core/, web/, api/.
"""
import re
from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from core.config import WEB_DIR, PORT, MONGO_URI
from core.startup import lifespan
from core.middleware import setup_middleware
from web.routes import register_web_routes
from api.router import get_api_router

# Build FastAPI app
fastapi_app = FastAPI(
    title="Pro-Alert",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# Static assets
if WEB_DIR.exists():
    fastapi_app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")

# Security, rate limit, trusted host, CORS, production exception handler
setup_middleware(fastapi_app)

# HTML page routes (/, /login, /dashboard, ...)
register_web_routes(fastapi_app, WEB_DIR)

# /signup MUST be served from repo root web/signup.html only — never a stale copy elsewhere
_no_cache = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


@fastapi_app.get("/signup")
def signup_page():
    """Single handler for /signup; scrubs any legacy 8-char copy before respond."""
    root = Path(__file__).resolve().parent
    f = root / "web" / "signup.html"
    if not f.exists():
        return JSONResponse(status_code=404, content={"detail": "signup.html not found"})
    content = f.read_text(encoding="utf-8")
    # Aggressive scrub — old placeholder had no space variants sometimes
    content = re.sub(
        r'placeholder\s*=\s*["\'][^"\']*8[^"\']*character[^"\']*["\']',
        'placeholder="Min. 12 characters"',
        content,
        flags=re.IGNORECASE,
    )
    content = content.replace("Min. 8 characters", "Min. 12 characters")
    content = content.replace("min. 8 characters", "Min. 12 characters")
    content = re.sub(
        r"<div[^>]*class=\"hint\"[^>]*>[^<]*8[^<]*character[^<]*</div>",
        '<div class="hint" id="passwordHintSignup">Use at least 12 characters with uppercase, lowercase, a number, and a special character</div>',
        content,
        count=1,
        flags=re.IGNORECASE,
    )
    content = content.replace(
        "Use at least 8 characters with a mix of letters and numbers",
        "Use at least 12 characters with uppercase, lowercase, a number, and a special character",
    )
    if "Min. 8" in content or "at least 8 characters" in content.lower():
        # Last resort: inject password field HTML so response can never show 8
        content = re.sub(
            r'<input[^>]*id="password"[^>]*/?>',
            '<input type="password" id="password" name="password" required placeholder="Min. 12 characters"/>',
            content,
            count=1,
        )
    if "<!-- signup-main-py -->" not in content:
        content = content.replace("<body>", "<body><!-- signup-main-py -->", 1)
    return HTMLResponse(content=content, media_type="text/html", headers=dict(_no_cache))

# API routes (/api/health, /api/ready, /api/startup, /api/auth, ...)
api_router = get_api_router()
fastapi_app.include_router(api_router, prefix="/api")

# Payments and password-reset use their own full prefix
from routes.payments import router as payments_router
from routes.password_reset import router as password_reset_router
fastapi_app.include_router(payments_router)
fastapi_app.include_router(password_reset_router)

# Protected docs (require auth)
from routes.auth import get_current_user

@fastapi_app.get("/docs")
async def get_docs(user: dict = Depends(get_current_user)):
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url=fastapi_app.openapi_url,
        title=fastapi_app.title + " - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
    )

@fastapi_app.get("/redoc")
async def get_redoc(user: dict = Depends(get_current_user)):
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=fastapi_app.openapi_url,
        title=fastapi_app.title + " - API Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )

# Wrap FastAPI app with Socket.IO so /socket.io is handled for real-time updates (web + mobile)
from services.websocket_service import sio
import socketio
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")

if __name__ == "__main__":
    import os
    import uvicorn
    print(f"[INFO] Starting IoT Security Platform on http://localhost:{PORT}")
    print(f"[INFO] Environment: {os.getenv('APP_ENV', 'local')}")
    print(f"[INFO] MongoDB: {MONGO_URI.split('@')[1] if '@' in MONGO_URI else 'localhost'}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
