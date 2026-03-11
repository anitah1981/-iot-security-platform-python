# Three slides – Pro-Alert IoT Security Platform

**Ready-to-open PowerPoint (Pro-Alert navy background):** `docs/Pro_Alert_Slides.pptx`  
Regenerate after edits: `pip install python-pptx` then `python scripts/build_pro_alert_slides.py`

Copy into **PowerPoint** or **Google Slides**, or open **`SLIDES_THREE.html`** in a browser (F11 fullscreen, arrow keys to navigate).

---

## Slide 1 – Project final risk register

**Title:** *Final risk register – Pro-Alert (IoT security monitoring platform)*

| Risk ID | Risk | L | I | Mitigation | Owner |
|--------|------|---|---|------------|--------|
| R1 | Weak or leaked JWT / secrets | M | C | Generated `JWT_SECRET`; no `.env` in git; production security gate | DevOps |
| R2 | Access without verification | M | H | Email verify before login; no session on signup until verified | Dev |
| R3 | MongoDB exposed or no TLS | L–M | C | `mongodb+srv` + auth; minimal DB user; backups | DevOps |
| R4 | SMTP / notification abuse | M | M | Rate limits; app passwords; secrets server-side only | Dev |
| R5 | Bad production config (CORS, HTTP) | M | H | `CORS_ORIGINS` locked; `FORCE_HTTPS`; `ALLOWED_HOSTS`; checklist | DevOps |
| R6 | Dependency / image vulnerabilities | M | M | Pinned `requirements.txt`; audit; rebuild images | Dev |
| R7 | Stripe webhook forgery | L | H | Webhook secret; signature validation | Dev |
| R8 | No backup / failed restore | M | H | Atlas backups or snapshots; restore drill | DevOps |

**Footer:** Residual risk accepted only where controls reduce impact; critical items gated before go-live.

*L = Likelihood, I = Impact (L/M/H/C = Low/Med/High/Critical)*

---

## Slide 2 – Artefact performance & security

**Title:** *Artefact performance & security*

**Security**
- JWT + refresh rotation; logout revokes refresh tokens; optional MFA at login
- Zero-tolerance email verification – only explicit verified flag allows API/dashboard
- bcrypt passwords; strong policy; lockout after failed attempts
- Rate limits on signup, login, password reset
- HTTPS, strict CORS, security checklist pre-deploy

**Performance**
- FastAPI + Motor (async MongoDB) for concurrent requests
- Indexes on `users.email`, devices, alerts for scalable lookups
- Stateless API – scale horizontally behind a reverse proxy
- WebSockets for real-time dashboard where used

**Takeaway:** Layered security (verify → login → JWT); performance via async I/O and indexing.

---

## Slide 3 – Artefact deployment & maintenance

**Title:** *Artefact deployment & maintenance*

**Deployment**
- Docker Compose: API + MongoDB 7; `env_file` for secrets
- Railway / Render: `pip install` + `uvicorn`; `/api/health` for checks
- Single `.env` – `APP_BASE_URL`, `CORS_ORIGINS`, SMTP, Twilio, Stripe
- Pre-deploy checklist: TLS DB, HTTPS, email links to live URL

**Maintenance**
- Restart policies; log auth/email failures; audit where implemented
- Backups and retention/cleanup jobs
- Upgrade path: test auth and notifications after deploy; rollback via image tag
- Monitor `/api/health`; product alerts for device offline

**Takeaway:** Repeatable Docker + env deploy; maintenance is checklist-driven with backups and health checks.

---

## Alternative Slide 3 – Artefact sustainability

**Title:** *Artefact sustainability*

- Lean stack: one API + MongoDB; no GPU; optional SMS/voice to control cost
- Long-lived choices: Python/FastAPI/MongoDB; vanilla JS reduces build churn
- Async + DB indexes reduce CPU and query load
- Clear repo layout (`routes/`, `services/`, `middleware/`) and in-repo checklists for handover

Use instead of deployment slide if the brief requires sustainability.
