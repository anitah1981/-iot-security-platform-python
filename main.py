from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="IoT Security Platform")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "IoT Security Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "iot-security-platform",
        "timestamp": datetime.utcnow().isoformat()
    }