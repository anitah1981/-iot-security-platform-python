# Today Go-Live (One-Pass Runbook)

Use this when you want to go live in one session.

Current known live URL in this project docs:

- `https://iot-security-platform-python-production.up.railway.app`

If your custom domain is not fully ready yet, go live on Railway URL first, then cut over to domain.

---

## 0) Pick your live URL for today

Choose one:

- Option A (fastest): `LIVE_URL=https://iot-security-platform-python-production.up.railway.app`
- Option B (custom domain ready): `LIVE_URL=https://app.yourdomain.com`

---

## 1) Set production env vars in Railway

Set these in Railway service Variables:

- `APP_ENV=production`
- `MONGO_URI=<atlas tls uri>`
- `JWT_SECRET=<strong random>`
- `CSRF_SECRET=<strong random>`
- `APP_BASE_URL=<LIVE_URL>`
- `ALLOWED_HOSTS=<host only, no scheme>`  
  Example: `iot-security-platform-python-production.up.railway.app` or `app.yourdomain.com`
- `CORS_ORIGINS=<LIVE_URL>`
- `FORCE_HTTPS=true`
- `ENABLE_HSTS=true`

Recommended runtime mode now:

- `ENABLE_DEVICE_STATUS_MONITOR=true`
- `ENABLE_NETWORK_MONITORING=false`

If email verification/reset is needed, set SMTP vars too.

---

## 2) Deploy from main branch

- Ensure latest code is on `main`
- Trigger deploy in Railway
- Wait for healthy deployment

---

## 3) Run local release gates (before sign-off)

From repo root:

```powershell
python scripts/security_gate.py
python scripts/release_gate.py
```

Expected:

- security gate passes
- tests pass

---

## 4) Verify the live app URL

Run:

```powershell
python scripts/verify_live.py <LIVE_URL>
```

Examples:

```powershell
python scripts/verify_live.py https://iot-security-platform-python-production.up.railway.app
python scripts/verify_live.py https://app.yourdomain.com
```

Optional authenticated smoke:

```powershell
$env:TEST_EMAIL = "your-test-user@email.com"
$env:TEST_PASSWORD = "your-test-password"
python scripts/verify_live.py <LIVE_URL>
```

---

## 5) Manual checks (5-10 minutes)

- Login works
- Dashboard loads
- Devices tab loads
- Active alerts render
- Settings page loads
- Logout/login cycle works

Mobile:

- Set app server URL to `<LIVE_URL>` (no extra `/api` unless your mobile app explicitly requires it)
- Use in-app connection check
- Login test

---

## 6) Custom domain cutover (when ready)

If you launched first on Railway URL:

1. Add `app.yourdomain.com` in Railway Custom Domains
2. Add GoDaddy DNS record exactly as Railway shows
3. Wait for cert/HTTPS ready
4. Update Railway vars:
   - `APP_BASE_URL=https://app.yourdomain.com`
   - `ALLOWED_HOSTS=app.yourdomain.com`
   - `CORS_ORIGINS=https://app.yourdomain.com`
5. Redeploy
6. Re-run:

```powershell
python scripts/verify_live.py https://app.yourdomain.com
```

---

## 7) Final sign-off statement

Use this text in your ops log:

`Go-live verified on <date> for <LIVE_URL>: security gate pass, release gate pass, live smoke pass, and manual critical-path checks complete.`

