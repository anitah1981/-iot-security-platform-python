# Deployment Runbook

Single entry point for deploying and operating Alert-Pro in production.

## Immediate next actions (ongoing)

- **CI signal:** Run `python -m pytest tests/ -v -W default` locally; fix any new warnings so CI stays clean.
- **Migration:** After confirming backups, run the naming migration **once per deployed environment** (see [Data migration (naming)](#after-deploy) below).
- **Authz:** Keep using the shared dependencies from `routes.auth`: `get_current_user` for authenticated routes, `require_admin` for **platform** admin-only routes (e.g. unlock account, network monitoring). Family/audit “admin” is per-family role, not platform admin; platform admin = `require_admin` only.
- **Production security (before go-live):**  
  (1) Generate and set a strong `JWT_SECRET` and all production env vars.  
  (2) Enable HTTPS and restrict `ALLOWED_HOSTS` / `CORS_ORIGINS`.  
  (3) Harden MongoDB (auth, TLS, backups).  
  (4) Run `scripts/security_gate.py` before each release.  
  (5) Walk through `docs/SECURITY_CHECKLIST.md` and verify each item in production.

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
- **Data migration (naming)**: After deploying the compatibility code, run the userId→user_id backfill once per environment:
  ```bash
  # Make sure MONGO_URI points at the target cluster
  export MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/iot_security"
  python scripts/migrate_userid_to_user_id.py
  ```
  This only fills in missing `user_id` / `created_at` fields and is safe to re-run.

## When you change the MongoDB password

Update `MONGO_URI` (with the new password) in **every** place the app or scripts read it:

| Where | What to do |
|-------|------------|
| **MongoDB Atlas** | Change the database user password (you did this). |
| **Local `.env`** | Update `MONGO_URI=...` with the new connection string. |
| **Render** | Dashboard → your service → Environment → edit `MONGO_URI`, save. Redeploy if needed so the new value is used. |
| **Railway** (if used) | Variables → set `MONGO_URI` to the new connection string. |
| **Any other host** | Set the `MONGO_URI` environment variable (or secrets) to the new value. |

**Do not push or commit the password to GitHub.** `.env` is in `.gitignore` and must stay that way. Secrets live only in your local `.env` and in each host’s environment (Render, Railway, etc.). There is nothing to commit for a password change.

## Quick links

| Doc | Purpose |
|-----|--------|
| [WHATS_LEFT_NOW.md](WHATS_LEFT_NOW.md) | **What's left to do now** (your actions vs done in code) |
| [GO_LIVE_STEPS.md](GO_LIVE_STEPS.md) | **How to** run migration + five production security steps (copy-paste commands) |
| [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) | Pre-production security checks |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Full deployment options and steps |
| [MAKE_APP_LIVE.md](MAKE_APP_LIVE.md) | Get live quickly (Railway/Render) |
| [REVERSE_PROXY_SETUP.md](REVERSE_PROXY_SETUP.md) | HTTPS and reverse proxy |
| [API_KEYS_SETUP.md](API_KEYS_SETUP.md) | API keys (email, SMS, payments) |
| [MONGODB_MANUAL_BACKUP.md](MONGODB_MANUAL_BACKUP.md) | Manual backup with mongodump (M0 / no Atlas backup) |
