"""
Alert-Pro FastAPI application. Config, startup, middleware, and routes are in core/, web/, api/.
"""
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles

from core.config import WEB_DIR, PORT, MONGO_URI
from core.startup import lifespan
from core.middleware import setup_middleware
from web.routes import register_web_routes
from api.router import get_api_router

# Build app
app = FastAPI(
    title="Alert-Pro",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# Static assets
if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")

# Security, rate limit, trusted host, CORS, production exception handler
setup_middleware(app)

# HTML page routes (/, /login, /dashboard, ...)
register_web_routes(app, WEB_DIR)

# API routes (/api/health, /api/ready, /api/startup, /api/auth, ...)
api_router = get_api_router()
app.include_router(api_router, prefix="/api")

# Payments and password-reset use their own full prefix
from routes.payments import router as payments_router
from routes.password_reset import router as password_reset_router
app.include_router(payments_router)
app.include_router(password_reset_router)

# Protected docs (require auth)
from routes.auth import get_current_user

@app.get("/docs")
async def get_docs(user: dict = Depends(get_current_user)):
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
    )

@app.get("/redoc")
async def get_redoc(user: dict = Depends(get_current_user)):
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )


if __name__ == "__main__":
    import os
    import uvicorn
    print(f"[INFO] Starting IoT Security Platform on http://localhost:{PORT}")
    print(f"[INFO] Environment: {os.getenv('APP_ENV', 'local')}")
    print(f"[INFO] MongoDB: {MONGO_URI.split('@')[1] if '@' in MONGO_URI else 'localhost'}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
