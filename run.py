"""
Production entry point - reads PORT from environment (Railway sets this).
Avoids shell variable expansion issues with $PORT.
"""
import os
import uvicorn

port = int(os.environ.get("PORT", 8000))
print(f"[START] Binding to 0.0.0.0:{port} (PORT env={os.environ.get('PORT', 'not set')})")
uvicorn.run("main:app", host="0.0.0.0", port=port)
