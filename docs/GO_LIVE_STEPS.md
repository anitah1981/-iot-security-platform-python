# How to run the migration and complete production security (go-live)

Follow these in order: **migration** (after backups), then the **five security steps** before go-live.

---

## Part 1: Run the migration in each deployed environment

The migration backfills `user_id` from `userId` and `created_at` from `createdAt` in several collections. It is **safe to run multiple times** (only updates documents that are missing the new fields).

### Before you run it

1. **Confirm backups** for the MongoDB you are about to change (e.g. Atlas automated backups or a manual snapshot). Ensure you can restore if needed.
2. **One environment at a time**: run the migration once per deployment (e.g. staging, then production), each with that environment's `MONGO_URI`.

### Run the migration

From the **project root** (where `scripts/` and `database.py` live), set `MONGO_URI` for the target environment, then run the script.

**Windows (PowerShell):**

```powershell
cd c:\IoT-security-app-python

# Use SINGLE quotes so & and ! in the URI are not interpreted by PowerShell
$env:MONGO_URI = 'mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/iot_security?retryWrites=true&w=majority'

# So the script can import the project's "database" module
$env:PYTHONPATH = "c:\IoT-security-app-python"

# Run the migration (script also loads .env from project root if MONGO_URI is set there)
python scripts/migrate_userid_to_user_id.py
```

**Linux / macOS (bash):**

```bash
cd /path/to/IoT-security-app-python

# Set MONGO_URI for THIS environment (replace with your real connection string)
export MONGO_URI="mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/iot_security"

# So the script can import the project's "database" module (required when run as script)
export PYTHONPATH="/path/to/IoT-security-app-python"

# Run the migration
python scripts/migrate_userid_to_user_id.py
```

**Using a .env file (any OS):**

If the target environment's `.env` already has the correct `MONGO_URI`, the migration script loads it automatically from the project root. From the project root run:

- **PowerShell:** `$env:PYTHONPATH = "c:\IoT-security-app-python"; python scripts/migrate_userid_to_user_id.py`
- **Bash:** `export PYTHONPATH="/path/to/IoT-security-app-python"; python scripts/migrate_userid_to_user_id.py`

You should see lines like `[devices] backfilled user_id from userId on N documents` and finally `[MIGRATION] Completed userId/user_id backfill.`

Repeat for each deployed environment (staging, production, etc.), using that environment's `MONGO_URI` and after confirming backups for that cluster.

---

## Part 2: Five production security steps (before go-live)

Do these **before** opening the app to real users.

### Step 1: Generate and set a strong JWT_SECRET and production env vars

1. **Generate a secret** (run once, then put the value in your production config):

   ```powershell
   cd c:\IoT-security-app-python
   python scripts/generate_secrets.py
   ```

   ```bash
   cd /path/to/IoT-security-app-python
   python scripts/generate_secrets.py
   ```

2. **Copy the printed `JWT_SECRET=` value.** Do not use the default from code (e.g. `your-super-secret-key-change-in-production`).

3. **Set production environment variables** in your host (Railway, Render, your server's .env, or secrets manager). At minimum:

   - `APP_ENV=production`
   - `JWT_SECRET=<the-generated-secret>`
   - `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
   - `CORS_ORIGINS=https://yourdomain.com`
   - `FORCE_HTTPS=true`
   - `APP_BASE_URL=https://yourdomain.com`
   - `MONGO_URI=<your-production-mongo-uri-with-auth>`
   - Plus any API keys you need: SMTP, Twilio, Stripe (see `.env.example` and docs/API_KEYS_SETUP.md).

### Step 2: Enable HTTPS and restrict ALLOWED_HOSTS / CORS_ORIGINS

- **HTTPS:** On Railway/Render/Fly.io, HTTPS is usually automatic. For your own server, use Caddy, Nginx + Let's Encrypt, or Cloudflare (see HTTPS_QUICK_START.md).
- **Restrict hosts and CORS:** Set `ALLOWED_HOSTS` and `CORS_ORIGINS` to your real production domain(s) only (no * in production).

### Step 3: Harden MongoDB

- **Authentication:** MongoDB must require auth (no anonymous access).
- **TLS:** Use a TLS connection string (e.g. `mongodb+srv://...` for Atlas, or `?ssl=true` for self-hosted).
- **Permissions:** Database user has minimal required permissions.
- **Backups:** Automated backups enabled; backup restoration tested at least once.

### Step 4: Run the security gate before each release

From the project root, with production env vars loaded (e.g. from .env or your CI secrets):

```powershell
cd c:\IoT-security-app-python
python scripts/security_gate.py
```

```bash
cd /path/to/IoT-security-app-python
python scripts/security_gate.py
```

You must see **"Security gate passed."** If you see `[FAIL] ...`, fix the reported item and run again before deploying.

### Step 5: Walk through the security checklist in production

1. Open docs/SECURITY_CHECKLIST.md.
2. After the app is deployed and HTTPS is on, go through every section and **verify** each item in the **live** environment (auth flows, rate limiting, headers, MFA, backups).
3. Fix anything that fails until the checklist is satisfied for production.

Quick checks:

- HTTPS redirect: `curl -I http://yourdomain.com`
- Security headers: `curl -I https://yourdomain.com`
- Rate limiting: send 6 rapid POSTs to `/api/auth/login` with wrong credentials; the 6th should return 429.

---

## Summary

| What | When | How |
|------|------|-----|
| Migration | After backups, once per environment | Set MONGO_URI, run `python scripts/migrate_userid_to_user_id.py` |
| 1. JWT + env | Before go-live | `python scripts/generate_secrets.py`, set all production env vars |
| 2. HTTPS + CORS | Before go-live | Enable HTTPS; set ALLOWED_HOSTS and CORS_ORIGINS to your domain |
| 3. MongoDB | Before go-live | Auth + TLS + least privilege + backups tested |
| 4. Security gate | Before every release | `python scripts/security_gate.py` must pass |
| 5. Checklist | After deploy, before go-live | Work through SECURITY_CHECKLIST.md in production |
