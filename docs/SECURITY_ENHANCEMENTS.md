# Security Enhancements Implemented

This document describes the four recommended enhancements that are now in the codebase.

## 1. Refresh token in httpOnly cookie

- **What:** On login and on `/api/auth/refresh`, the server sets cookie `iot_refresh_token` with **HttpOnly**, **SameSite=Lax**, and **Secure** in production.
- **Why:** JavaScript cannot read the refresh token, reducing impact of XSS.
- **API:** `POST /api/auth/refresh` accepts either:
  - JSON body `{ "refresh_token": "..." }` (legacy), or
  - **No body** — token is read from the cookie (browser must send `credentials: 'include'`).
- **Frontend:** `app.js` uses `credentials: "include"` on all `fetch` calls and calls refresh with an empty body when `localStorage` has no refresh token, so the cookie is used automatically.

## 2. Enhanced audit logging

- **Failed logins:** `login_failed` entries in `audit_logs` with `user_email`, `reason` (`user_not_found`, `bad_password`, `mfa_invalid`), `ip_address`, `user_agent`.
- **Successful logins:** `login` with IP and user agent.
- **MFA:** `mfa_enabled` / `mfa_disabled` via `AuditLogger.log_security_event`.
- **Session revoke:** `session_revoked` with `session_id` in details.
- **Helpers:** `AuditLogger.log_failed_login`, `AuditLogger.log_security_event` in `services/audit_logger.py`.

## 3. Session management UI

- **Storage:** Each refresh token row in `refresh_tokens` now has:
  - `session_public_id` — opaque id safe to expose to the client
  - `ip_address`, `user_agent` (truncated) for display
- **API:**
  - `GET /api/auth/sessions` — list active (non-revoked, non-expired) sessions.
  - `POST /api/auth/sessions/revoke` — body `{ "session_id": "<session_public_id>" }` revokes that session only.
- **UI:** Settings → **Active sessions** card lists sessions with Revoke buttons.

## 4. Per-user rate limiting

- **What:** The global SlowAPI limiter key is **per user** when the request includes a valid `Authorization: Bearer <jwt>` header; otherwise it remains **per IP**.
- **Why:** Authenticated abuse is capped per account; login/signup stay IP-based.
- **Where:** `middleware/security.py` — `rate_limit_key_user_or_ip` decodes JWT `sub` and returns `user:<id>`.

## Configuration

- **CORS:** Same-origin UI already sends cookies; if you use a separate frontend origin, set `CORS_ORIGINS` and ensure `allow_credentials` is true (main.py does this when origins are not `*`).
- **Production:** `APP_ENV=production` sets **Secure** on cookies so they are only sent over HTTPS.

## Indexes

`database.create_indexes()` ensures indexes on `refresh_tokens` for `token_hash`, `user_id`+`revoked`, `session_public_id`, and `expires_at`.
