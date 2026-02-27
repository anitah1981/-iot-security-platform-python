# Live environment verification sign-off

Use this checklist to explicitly verify and sign off security and behaviour **against the live app** (not local). Fill in **Env URL** and **Verified on** when done.

**Env URL:** `https://iot-security-platform-python-production.up.railway.app`  
**Verified on (date):** _________________________ (e.g. 2026-02-28)

**Automated checks (2026-02-27):** Health 200 OK; /docs unauthenticated → 401; backup script ran successfully.

---

## Must verify on live

- [ ] **HTTPS** – HTTP redirects to HTTPS; `curl -I http://<env-url>` returns 307.
- [ ] **Security headers** – `curl -I https://<env-url>` shows X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, Content-Security-Policy, Referrer-Policy.
- [ ] **API docs protection** – Unauthenticated `GET /docs` and `GET /redoc` return 401 (or redirect to login).
- [ ] **Rate limiting** – 6 rapid `POST /api/auth/login` with wrong credentials; 6th returns 429.
- [ ] **Account lockout** – 5 failed logins → lockout; after 15 min, login works again.
- [ ] **MFA flow** – Enable MFA → login requires code; backup code works once; MFA can be disabled.
- [ ] **Password reset** – Forgot password → email → reset → login with new password works.
- [ ] **Admin: unlock account** – Admin user can unlock a locked account (test with admin role).
- [ ] **Admin: network monitoring** – Only admin can access network monitoring enable/disable/status.
- [ ] **Audit (Business plan)** – Non-Business user gets 403 on audit logs; Business user can access.
- [ ] **Health/ready/startup** – `GET /api/health`, `/api/ready`, `/api/startup` return 200 with expected body.

---

## Optional

- [ ] Notifications (email/SMS/WhatsApp) work from live app.
- [ ] Payment flow (Stripe) works in live (test mode or live as appropriate).

---

Run this after go-live and after any major security or auth change. Keep a copy of the completed checklist (e.g. in your runbook or internal docs).
