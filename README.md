# IoT Security Platform (Python Backend)

FastAPI + MongoDB backend for an IoT security monitoring platform.

## What this does (today)
- JWT auth (`/api/auth/*`)
- Device management (`/api/devices/*`)
- Alerts (`/api/alerts/*`)
- Heartbeat receiver (`/api/heartbeat`)
- Background heartbeat sweep + notification service scaffolding (in `services/`)

## Run locally

### 1) Install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
Copy `.env.example` to `.env` (do not commit it). Minimal:
```bash
MONGO_URI=mongodb://localhost:27017/iot_security
JWT_SECRET=change-me
```

For production, set `CORS_ORIGINS` to your real site origins (comma-separated). Avoid `*` in production.

Optional (notifications):
```bash
SENDGRID_API_KEY=...
FROM_EMAIL=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
```

### 3) Start API
```bash
uvicorn main:app --reload --port 8000
```

Health check: `GET /api/health`

## Run with Docker (recommended for launch)
```bash
cp .env.example .env
docker compose up --build
```

Open the web UI at `/` and API docs at `/docs`.

## Project context
See `docs/claude-context.md` for the full project vision and feature roadmap.

