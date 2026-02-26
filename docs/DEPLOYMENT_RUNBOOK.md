# Deployment Runbook

Single entry point for deploying and operating Alert-Pro in production.

## Before you deploy

1. **Security checklist (mandatory)**  
   [docs/SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) — JWT_SECRET, HTTPS, env vars, MFA, backups.

2. **Release gate**  
   Run before every release:
   ```bash
   python scripts/security_gate.py
   ```
   CI runs this on push/PR (see [.github/workflows/ci.yml](../.github/workflows/ci.yml)).

3. **Configuration**  
   [.env.example](../.env.example) — copy to `.env` and set all production values.  
   [docs/API_KEYS_SETUP.md](API_KEYS_SETUP.md) — SendGrid, Twilio, Stripe.

## Deploy steps

- **Full deployment guide**: [docs/DEPLOYMENT.md](DEPLOYMENT.md)  
- **Make the app live (Railway/Render)**: [docs/MAKE_APP_LIVE.md](MAKE_APP_LIVE.md)  
- **HTTPS / reverse proxy**: [docs/REVERSE_PROXY_SETUP.md](REVERSE_PROXY_SETUP.md)  
- **Local production-style config**: [docs/LOCAL_PRODUCTION_CONFIG.md](LOCAL_PRODUCTION_CONFIG.md)

## After deploy

- **Health**: `GET /api/health` (liveness), `GET /api/ready` (readiness), `GET /api/startup` (task status).
- **API docs**: `/docs` and `/redoc` require authentication — see [README](../README.md) “Access the application”.
- **Audit**: Review [docs/SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) and fix any unchecked items.

## Quick links

| Doc | Purpose |
|-----|--------|
| [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) | Pre-production security checks |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Full deployment options and steps |
| [MAKE_APP_LIVE.md](MAKE_APP_LIVE.md) | Get live quickly (Railway/Render) |
| [REVERSE_PROXY_SETUP.md](REVERSE_PROXY_SETUP.md) | HTTPS and reverse proxy |
| [API_KEYS_SETUP.md](API_KEYS_SETUP.md) | API keys (email, SMS, payments) |
