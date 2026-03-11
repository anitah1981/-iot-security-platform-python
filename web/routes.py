"""
Register HTML page routes (/, /login, /dashboard, etc.) on the FastAPI app.
Protected pages (dashboard, settings, family, audit-logs, incidents) require authentication;
unauthenticated requests are redirected to /login.
"""
import re
from pathlib import Path
from fastapi import Request, Depends
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse

from routes.auth import get_current_user_for_pages


def register_web_routes(app, web_dir: Path) -> None:
    if not web_dir.exists():
        return

    @app.get("/cybersecurity-threats")
    async def cybersecurity_threats_page():
        f = web_dir / "cybersecurity-threats.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": f"File not found: {f}"})
        return FileResponse(str(f), media_type="text/html")

    @app.get("/security-threats")
    async def security_threats_page():
        f = web_dir / "cybersecurity-threats.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": f"File not found: {f}"})
        return FileResponse(str(f), media_type="text/html")

    @app.get("/security-compliance")
    def security_compliance_page():
        f = web_dir / "security-compliance.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/")
    def root():
        landing = web_dir / "landing.html"
        if landing.exists():
            return FileResponse(str(landing))
        index = web_dir / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"message": "Pro-Alert API", "version": "2.0.0", "status": "running"}

    # HTML pages that must always revalidate (auth forms change often; avoid stale JS/CSS)
    _no_cache_html = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    @app.get("/login")
    def login_page():
        f = web_dir / "login.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f), media_type="text/html", headers=dict(_no_cache_html))

    @app.get("/signup")
    def signup_page():
        """
        Serve signup HTML; always force 12-char password copy (API requires 12+).
        Read signup.html from the same folder as this module first — avoids wrong web_dir.
        """
        f = Path(__file__).resolve().parent / "signup.html"
        if not f.exists():
            f = web_dir / "signup.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        try:
            content = f.read_text(encoding="utf-8")
        except OSError:
            return FileResponse(str(f), media_type="text/html", headers=dict(_no_cache_html))

        # Whole-tag replace: old signup had no other attrs on this input
        content = re.sub(
            r'<input\s+type="password"\s+id="password"\s+name="password"\s+required\s+placeholder="[^"]*"\s*/>',
            '<input type="password" id="password" name="password" required placeholder="Min. 12 characters"/>',
            content,
            flags=re.IGNORECASE,
        )
        # Hint div with no id (legacy)
        content = re.sub(
            r'<div class="hint">\s*Use at least 8 characters with a mix of letters and numbers\s*</div>',
            '<div class="hint" id="passwordHintSignup">Use at least 12 characters with uppercase, lowercase, a number, and a special character</div>',
            content,
            flags=re.IGNORECASE,
        )
        # Any other placeholder variant on password input
        content = re.sub(
            r'placeholder\s*=\s*["\']Min\.\s*8\s*characters["\']',
            'placeholder="Min. 12 characters"',
            content,
            flags=re.IGNORECASE,
        )
        content = content.replace("Min. 8 characters", "Min. 12 characters")
        content = content.replace("min. 8 characters", "Min. 12 characters")
        content = content.replace(
            "Use at least 8 characters with a mix of letters and numbers",
            "Use at least 12 characters with uppercase, lowercase, a number, and a special character",
        )
        content = content.replace("password.length < 8", "password.length < 12")
        if "signup-served-v12" not in content:
            content = content.replace("<body>", "<body><!-- signup-served-v12 -->", 1)
        return HTMLResponse(
            content=content,
            media_type="text/html",
            headers=dict(_no_cache_html),
        )

    @app.get("/dashboard", dependencies=[Depends(get_current_user_for_pages)])
    def dashboard_page(request: Request):
        f = web_dir / "dashboard.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/settings", dependencies=[Depends(get_current_user_for_pages)])
    def settings_page(request: Request):
        f = web_dir / "settings.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/pricing")
    def pricing_page():
        f = web_dir / "pricing.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f), headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"})

    @app.get("/forgot-password")
    def forgot_password_page():
        f = web_dir / "forgot-password.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/reset-password")
    def reset_password_page():
        f = web_dir / "reset-password.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/verify-email")
    def verify_email_page():
        f = web_dir / "verify-email.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/terms")
    def terms_page():
        f = web_dir / "terms.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/privacy")
    def privacy_page():
        f = web_dir / "privacy.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/family", dependencies=[Depends(get_current_user_for_pages)])
    def family_page():
        f = web_dir / "family.html"
        if not f.exists():
            return JSONResponse(status_code=404, content={"detail": "Page not found"})
        return FileResponse(str(f))

    @app.get("/audit-logs", dependencies=[Depends(get_current_user_for_pages)])
    def audit_logs_page():
        f = web_dir / "audit-logs.html"
        return FileResponse(str(f))

    @app.get("/incidents", dependencies=[Depends(get_current_user_for_pages)])
    def incidents_page():
        f = web_dir / "incidents.html"
        return FileResponse(str(f))
