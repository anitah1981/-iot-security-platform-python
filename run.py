"""
Production entry point - reads PORT from environment (Railway sets this).
Avoids shell variable expansion issues with $PORT.
"""
import os
from pathlib import Path
import uvicorn

port = int(os.environ.get("PORT", 8000))
print(f"[START] Binding to 0.0.0.0:{port} (PORT env={os.environ.get('PORT', 'not set')})")
# So you can confirm which signup.html is on disk (must contain Min. 12, not 8)
_signup = Path(__file__).resolve().parent / "web" / "signup.html"
if _signup.exists():
    _txt = _signup.read_text(encoding="utf-8", errors="replace")
    _has8 = "Min. 8 characters" in _txt or "at least 8 characters with a mix" in _txt
    print(f"[START] signup.html path: {_signup} (contains legacy 8-char text: {_has8})")
else:
    print(f"[START] signup.html NOT FOUND at {_signup}")
uvicorn.run("main:app", host="0.0.0.0", port=port)
