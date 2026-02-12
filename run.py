"""
Production entry point - reads PORT from environment (Railway sets this).
Avoids shell variable expansion issues with $PORT.
"""
import os
import uvicorn

port = int(os.environ.get("PORT", 8000))
uvicorn.run("main:app", host="0.0.0.0", port=port)
