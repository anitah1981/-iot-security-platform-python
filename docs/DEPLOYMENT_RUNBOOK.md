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

## Final launch gate (every time before deploy)

Run the full pre-release gate locally so it matches CI. Then verify the deployed app.

1. **One-command gate (security + lint + tests):**
   ```bash
   python scripts/release_gate.py
   ```
   This runs: `scripts/security_gate.py`, `ruff check .`, `pytest tests/ -v --tb=short -W default`. CI runs the same on push/PR (see [.github/workflows/ci.yml](../.github/workflows/ci.yml)).

2. **After deploy: health/readiness/startup on the live app**
   - `GET <live-url>/api/health` → 200, `"ok": true`
   - `GET <live-url>/api/ready` → 200, database connected
   - `GET <live-url>/api/startup` → 200, tasks status

If any step fails, fix before considering the release done.

3. **Manual verification (live environment)**  
   Explicit sign-off against the **live** app. Before go-live and after major changes, verify on the deployed URL:
   - **HTTPS** – HTTP redirects to HTTPS; security headers present.
   - **API docs** – `/docs` and `/redoc` return 401 when unauthenticated.
   - **Rate limiting** – 6th rapid failed login returns 429.
   - **Lockout** – 5 failed logins → lockout; after 15 min, login works.
   - **MFA** – Enable MFA, login with code, backup code once, disable MFA.
   - **Password reset** – Forgot password → email → reset → login works.
   - **Admin** – Unlock account and network monitoring only for admin.
   - **Audit** – Business plan only; non-Business gets 403.
   - **Health** – `/api/health`, `/api/ready`, `/api/startup` return 200.
   Document completion (e.g. “Verified on &lt;date&gt; for &lt;env-url&gt;”) and keep with your runbook. Full checklist: [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md).

## Before you deploy

1. **Security checklist (mandatory)**  
   [docs/SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) — JWT_SECRET, HTTPS, env vars, MFA, backups.

2. **Release gate**  
   Run before every release: `python scripts/release_gate.py` (or at least `python scripts/security_gate.py`).  
   CI runs security_gate + ruff + pytest on push/PR (see [.github/workflows/ci.yml](../.github/workflows/ci.yml)).

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

### Post-migration validation (per environment)

After running the migration in each environment (staging, prod):

- [ ] Migration completed without errors (backfill counts as expected).
- [ ] App flows verified: login, devices list, alerts list, settings, audit (if Business).
- [ ] No query regressions: dashboard and key pages load; no 500s from missing `user_id`/`created_at`.

See [GO_LIVE_STEPS.md](GO_LIVE_STEPS.md) for migration commands per environment.

## Backup and restore operational readiness

- **Schedule:** Run a manual backup regularly (e.g. weekly). Use `python scripts/backup_manual.py` (output under `C:\backups` or `BACKUP_BASE_DIR`). On Windows, a weekly task **"MongoDB backup IoT app"** can run `scripts/run_backup.ps1` (e.g. Sunday 02:00). See [MONGODB_MANUAL_BACKUP.md](MONGODB_MANUAL_BACKUP.md) and [RESTORE_NOTES.md](RESTORE_NOTES.md).
- **Restore drill:** At least once, restore from a backup (e.g. use backup JSON or mongorestore) into a test DB and confirm app works against it. Document the steps in [RESTORE_NOTES.md](RESTORE_NOTES.md).
- **Retention:** Decide how many backup copies to keep (e.g. last 4 weekly) and where they are stored; prune older ones. See [RESTORE_NOTES.md](RESTORE_NOTES.md).

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
| [TASKS_2_3_4_WALKTHROUGH.md](TASKS_2_3_4_WALKTHROUGH.md) | **Tasks 2–4** – What was done for you and what you still do (live verification, backups, post-migration) |
| [WHATS_LEFT_NOW.md](WHATS_LEFT_NOW.md) | **What's left to do now** (your actions vs done in code) |
| [GO_LIVE_STEPS.md](GO_LIVE_STEPS.md) | **How to** run migration + five production security steps (copy-paste commands) |
| [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) | Pre-production security checks |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Full deployment options and steps |
| [MAKE_APP_LIVE.md](MAKE_APP_LIVE.md) | Get live quickly (Railway/Render) |
| [REVERSE_PROXY_SETUP.md](REVERSE_PROXY_SETUP.md) | HTTPS and reverse proxy |
| [API_KEYS_SETUP.md](API_KEYS_SETUP.md) | API keys (email, SMS, payments) |
| [PRODUCTION_EMAIL_SETUP.md](PRODUCTION_EMAIL_SETUP.md) | **Production email** – set SMTP in Railway so password reset and verification work |
| [MONGODB_MANUAL_BACKUP.md](MONGODB_MANUAL_BACKUP.md) | Manual backup (Python script or mongodump), restore drill, retention |
| [RESTORE_NOTES.md](RESTORE_NOTES.md) | Restore from Python backup (JSON) and retention policy |
| [TAKE_SITE_OFFLINE.md](TAKE_SITE_OFFLINE.md) | How to take the website offline on Railway (stop/pause service) |
