# Go-Live and 12-Month Scale Playbook

This playbook captures the current agreed direction:

- Keep cloud deployment (Railway) as the control plane
- Use custom domain from GoDaddy
- Run app-first, consumer-friendly security monitoring now
- Expand architecture in phases without risky rewrites

---

## 1) Core Positioning (Use in report, demo, and pitch)

Pro-Alert is a cloud-first IoT security monitoring service that detects device silence, instability, and suspicious behavior quickly, without requiring extra consumer hardware.

Boundary (explicit and honest):

- Cloud-only deployment is not full packet forensics inside private LANs.
- Future advanced LAN telemetry can be added as an optional tier.

---

## 2) Go-Live Decision

Use both:

- GoDaddy domain = address
- Railway = hosting/runtime

Recommended production URL pattern:

- `app.yourdomain.com` -> Railway app

Do not block go-live waiting for major architecture changes.

---

## 3) Go-Live Checklist (Now)

### A. Platform + Domain

- [ ] Railway project connected to `main` branch
- [ ] Custom domain added in Railway (`app.yourdomain.com`)
- [ ] GoDaddy DNS record points to Railway target (as instructed by Railway)
- [ ] HTTPS certificate shows as valid

### B. Production env vars

Set and verify:

- [ ] `APP_ENV=production`
- [ ] `MONGO_URI` (Atlas/TLS)
- [ ] `JWT_SECRET` (strong random 32+ chars)
- [ ] `CSRF_SECRET` (strong random 32+ chars; stable across deploys)
- [ ] `APP_BASE_URL=https://app.yourdomain.com`
- [ ] `ALLOWED_HOSTS=app.yourdomain.com`
- [ ] `CORS_ORIGINS=https://app.yourdomain.com`
- [ ] `FORCE_HTTPS=true`
- [ ] `ENABLE_HSTS=true`
- [ ] SMTP vars if email verification/reset is required

Optional integrations:

- [ ] Stripe keys/webhook (if payments enabled)
- [ ] Twilio credentials (if SMS/voice/WhatsApp enabled)

### C. Pre-release gates

From repo root:

- [ ] `python scripts/security_gate.py`
- [ ] `python scripts/release_gate.py`

### D. Live verification

- [ ] `python scripts/verify_live.py https://app.yourdomain.com`
- [ ] Browser check: login, dashboard, devices, alerts, settings
- [ ] Mobile check: base URL and sign-in flow

---

## 4) Runtime Mode Recommendation (Current Stage)

Use heartbeat-led monitoring as primary signal.

Recommended defaults for cloud stability:

- `ENABLE_DEVICE_STATUS_MONITOR=true` (keep, but monitor CPU)
- `ENABLE_NETWORK_MONITORING=false` initially in pure cloud mode

Why:

- Heartbeats are the most reliable cloud-friendly signal
- Broad LAN scanning from cloud often adds load with limited home-LAN visibility

If you need LAN-depth later, ship it as optional advanced mode, not a blocker for go-live.

---

## 5) 12-Month Expansion Roadmap

## Months 1-3: Launch + Reliability

Goals:

- Stable production operation
- Repeatable release process
- Evidence-led confidence

Deliverables:

- [ ] Complete go-live checklist above
- [ ] Weekly ops review (incidents, latency, alert quality)
- [ ] Baseline KPIs tracked (see section 6)
- [ ] Signed live verification after each major release

## Months 4-6: Separation + Operational maturity

Goals:

- Reduce coupling between API traffic and background work
- Improve recoverability and observability

Deliverables:

- [ ] Split API service and background worker responsibilities
- [ ] Queue-backed background jobs (where needed)
- [ ] Error tracking + service health alerting
- [ ] Backup + restore runbook tested

## Months 7-9: Product growth + commercial readiness

Goals:

- Better user retention and lower false positives
- Sharper tiering strategy

Deliverables:

- [ ] Alert confidence scoring improvements
- [ ] Plan-tier value mapping (Free/Pro/Business)
- [ ] Improved onboarding and activation funnel
- [ ] Security and tenancy audit pass

## Months 10-12: Advanced detection tier (optional)

Goals:

- Increase confidence on LAN-centric threats
- Keep default product friction low

Deliverables:

- [ ] Optional advanced local telemetry mode design
- [ ] Privacy/consent/retention controls for deeper telemetry
- [ ] Pilot rollout plan for advanced users
- [ ] Keep app-only default unchanged

---

## 6) KPI Starter Set

Track weekly and monthly:

- API p95 latency
- Auth success rate
- Alert delivery time
- False positive rate (alerts dismissed as noise)
- Device heartbeat reliability rate
- Active monitored devices
- Incident MTTR (mean time to recovery)

Use trends, not one-off values, for decision-making.

---

## 7) Messaging Guardrails (Avoid confusion)

Say:

- "Cloud behavioral monitoring with fast actionable alerts."
- "No extra hardware required for baseline protection."

Do not say:

- "Full packet forensics inside every home LAN from cloud only."

---

## 8) Short Viva/Investor-ready Statement

We intentionally prioritized a low-friction, cloud-first architecture to deliver immediate consumer value: fast detection of device silence and suspicious behavior with actionable alerts. We explicitly document packet-level in-home telemetry as an optional future tier, enabling deeper technical coverage without compromising adoption and usability today.
