# Three slides – Pro-Alert / IoT Security Platform

Use each **Slide** block as one slide (title + bullets). Adjust owner/dates as needed.

---

## Slide 1 – Project final risk register

**Title:** Final risk register – Pro-Alert (IoT security monitoring platform)

| Risk ID | Risk | Likelihood | Impact | Mitigation (implemented / planned) | Owner |
|--------|------|------------|--------|-----------------------------------|--------|
| R1 | **Secrets in repo or weak JWT** – compromise of all sessions | Med | Critical | `JWT_SECRET` generated via script; production gate; never commit `.env`; rotate on breach | DevOps |
| R2 | **Unauthenticated or unverified access** – dashboard/API abuse | Med | High | Email verification required before login; bcrypt passwords; lockout after failed attempts; rate limits on signup/login | Dev |
| R3 | **MongoDB exposure or no TLS** – data breach | Low–Med | Critical | TLS/`mongodb+srv`; auth; minimal DB user; backups and restore tested | DevOps |
| R4 | **SMTP / notification abuse** – spam or credential leak | Med | Med | Rate limits; app passwords; no secrets in client; optional Twilio hardening | Dev |
| R5 | **Deployment misconfiguration** – wrong CORS, HTTP only, open admin | Med | High | `CORS_ORIGINS` locked; `FORCE_HTTPS` / HSTS; `ALLOWED_HOSTS`; pre-deploy security checklist | DevOps |
| R6 | **Dependency / container vulnerabilities** | Med | Med | Pinned `requirements.txt`; periodic `pip audit`; rebuild images; MongoDB 7 in Docker | Dev |
| R7 | **Stripe / payment webhook forgery** | Low | High | Webhook secret; validate signatures; test in staging | Dev |
| R8 | **Operational – no backups or failed restores** | Med | High | Atlas backups or volume snapshots; documented restore drill | DevOps |

**Residual:** Accepted only where likelihood × impact is low after controls; critical risks require mitigation before go-live.

---

## Slide 2 – Artefact performance & security

**Title:** Artefact performance & security – Pro-Alert

**Security (defence in depth)**  
- **Authentication:** JWT + HttpOnly cookie option; refresh token rotation and revoke-on-logout; MFA optional at login.  
- **Verification:** Zero-tolerance email verification – only explicit `email_verified: true` allows login/API/dashboard; signup does not issue a session until verify + login.  
- **Passwords:** bcrypt; strong policy (length + complexity); password reset flow separated from session.  
- **Abuse prevention:** Rate limits (e.g. signup 3/min, login 5/min); account lockout after repeated failures.  
- **Transport & headers:** HTTPS in production; CORS restricted to known origins; security checklist before deploy.

**Performance**  
- **Async I/O:** FastAPI + Motor (async MongoDB) to avoid blocking under concurrent alerts and dashboard loads.  
- **Indexing:** Indexed fields (e.g. `users.email`, `devices.deviceId`, `alerts`) to keep lookups fast as data grows.  
- **Scaling path:** Stateless API behind reverse proxy; horizontal scale by adding instances; MongoDB as shared store.  
- **Real-time:** WebSockets where used for dashboard updates without polling every endpoint.

**Takeaway:** Security controls are layered (verify → login → JWT → optional MFA); performance relies on async DB and indexes, with a clear path to scale out.

---

## Slide 3 – Artefact deployment and maintenance

**Title:** Artefact deployment and maintenance – Pro-Alert

**Deployment**  
- **Containerised stack:** Docker Compose – API + MongoDB 7; `env_file` + `MONGO_URI` for consistent local/prod parity.  
- **Cloud options:** Railway / Render (documented) – build `requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`; health endpoint for platform checks.  
- **Configuration:** Single `.env` pattern – `APP_BASE_URL`, `CORS_ORIGINS`, secrets, SMTP, Twilio, Stripe – no secrets in image layers.  
- **Cutover:** Pre-deployment checklist (JWT, TLS DB, HTTPS redirect, email links pointing to live URL).

**Maintenance**  
- **Operations:** Restart policies (`unless-stopped`); logs for auth/email errors; optional audit logging for sensitive actions.  
- **Data:** MongoDB backups; retention/cleanup jobs where implemented; re-run security gate after env changes.  
- **Upgrades:** Dependency updates in controlled window; test auth + notifications after deploy; rollback via previous image/tag.  
- **Monitoring:** `/api/health` (and readiness if added); alert on failed heartbeat/device offline as product feature, not only infra.

**Takeaway:** Deploy is repeatable (Docker + env); maintenance is checklist-driven with health checks and backup/restore as first-class concerns.

---

## Optional fourth line on slide 1 (if you need “sustainability” instead)

If you must swap **Slide 3** for **Artefact sustainability**, use:

**Title:** Artefact sustainability – Pro-Alert  

- **Resource use:** Single API process + MongoDB; no always-on GPU; optional channels (SMS/voice) user-configurable to reduce cost and noise.  
- **Longevity:** Standard stack (Python/FastAPI/MongoDB); vanilla JS frontend avoids heavy build churn; documented runbooks.  
- **Energy / cost:** Efficient async model reduces CPU wait; indexes reduce DB load; Docker avoids duplicate full VMs for small deployments.  
- **Maintainability:** Clear module layout (`routes/`, `services/`, `middleware/`); security and deployment checklists in repo for handover.

---

*Generated for the IoT-security-app-python (Pro-Alert) codebase – align slide owner/dates with your module submission.*
