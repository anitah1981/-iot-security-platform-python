# Pro-Alert — Artefact Script (Problems, Fixes & Growth by Section)

Use this as **speaker notes**, **video narration**, or **written artefact**.  
**Design choice:** early problems and how we fixed them are **not** in one upfront block — they appear **in the section where they belong**, so the story reads as *we built → we tested → something was missing → we expanded*.

Approx. **15–22 minutes** spoken; trim per section for shorter runs.

---

## How to read this script

- **Current demo** — what to say while showing the screen.
- **From the start** — what the first version looked like or what broke first.
- **Testing showed** — the gap or failure mode we hit.
- **We expanded / fixed** — what we added or changed.

---

## 1. Opening (30–45 sec)

**Current demo**
> *“Most homes run dozens of connected devices. The problem isn’t lack of gear — it’s lack of **one place** to see them all, **one** clear alert when something’s wrong, and **proof** of who did what after an incident. **Pro-Alert** is a full-stack IoT security platform that grew in **iterations**: every round of testing showed something missing, and we expanded — MFA, sessions, audit, honest notification behaviour, and more.”*

**From the start**
> *“We didn’t start with every tab you see now. We started with auth, devices, and alerts — then each test pass exposed the next layer we needed.”*

---

## 2. The real-world problem & market gap (1–2 min)

**Current demo**
> *“Doorbell offline overnight — power, Wi‑Fi, or jamming? Without a unified layer you’re checking five vendor apps. Businesses need the same clarity without enterprise SOC cost.”*

**Testing showed**
> *“Early demos made it obvious: **visibility** alone wasn’t enough. Users asked *how do I know it reached me?* and *how do I prove it later?* That pushed us toward **multi-channel notifications** and **audit/export**, not just a device list.”*

**We expanded**
> *“So the product isn’t only ‘device up/down’ — it’s **alerting with severity**, **preferences**, and **accountability** after the fact.”*

---

## 3. What Pro-Alert is — technical snapshot (45 sec–1 min)

**Current demo**
> *“FastAPI backend, MongoDB, vanilla JS dashboard with real-time updates, optional **device agent** on the LAN, Stripe for plans, Twilio for WhatsApp/voice (SMS where compliant).”*

**From the start**
> *“First runnable version: register, login, add devices manually. No agent yet — so ‘last seen’ was meaningless until we added **heartbeats** and the **agent** story.”*

**Testing showed**
> *“Manual-only devices didn’t reflect real homes. Testing highlighted: **we need something on the network** that actually talks to the API.”*

**We expanded**
> *“Device agent + API key in Settings, heartbeat sweeps, and deduplicated alerts so the dashboard reflects **reality**, not just forms.”*

---

## 4. Landing / Home — first impression (45 sec)

**Current demo**
> *“Landing explains the value proposition and routes to signup or login. SEO and clarity matter — this is where trust starts.”*

**From the start**
> *“Initially we jumped straight into the app; stakeholders asked for a **proper marketing surface** and clear path to try the product.”*

**Testing showed**
> *“Cold users didn’t know what to do first. We needed a **single narrative** before the dashboard.”*

**We expanded**
> *“Dedicated landing, pricing page, and consistent nav so the journey is **landing → signup → verify → dashboard** without dead ends.”*

---

## 5. Signup — password policy & verification (1–2 min)

**Current demo**
> *“Sign-up enforces a **strong password policy** aligned with the API. After submit, email verification and clear errors — no silent failures.”*

**From the start**
> *“First signup was minimal validation; the API already enforced **length and complexity** (e.g. 12+ with mixed character classes). The **frontend lagged** — some builds still said ‘min 8’.”*

**Testing showed**
> *“Users hit **400 from the API** while the page said they were fine. Worse, **Edge and proxies cached old HTML** — so even after we fixed the file, some browsers kept showing the old hint.”*

**We expanded / fixed**
> *“Aligned **signup.html** and **signup.js** with the API; added **cache-control** and **asset version query strings** so deployments don’t lie to the user. Optional **GET /signup** scrub on the server to strip legacy copy if anything slips through.”*

**Line to say**
> *“What you see now is **one source of truth**: the same rules on the wire and on the screen.”*

---

## 6. Login — rate limits, lockout, MFA (1–2 min)

**Current demo**
> *“Login returns clear errors; with MFA enabled you get the **six-digit step** after password. Failed attempts are throttled — account lockout slows brute force.”*

**From the start**
> *“Login was username/password only. First security pass: **JWT only**, long-lived, no rotation — fine for a prototype, not for production.”*

**Testing showed**
> *“Pen-test style checks: **no rate limit** meant scripted guessing; **no audit** meant we couldn’t answer ‘was that me or not?’; **MFA** without backup codes left users locked out if they lost a phone.”*

**We expanded**
> *“**Rate limiting** per IP for anonymous endpoints; when a **Bearer token** is present, limits can be **per user** so shared IPs don’t punish legitimate households. **Account lockout** after repeated failures. **MFA** with **TOTP + backup codes**; enabling MFA **revokes refresh tokens** so old sessions can’t bypass the new bar.”*

---

## 7. Dashboard — hub, websocket, tabs (1–2 min)

**Current demo**
> *“Dashboard is the hub: **Devices & Alerts** tab for live status and **Analytics & Charts** for trends. Sidebar reaches Family, Settings, Audit, Incidents, Security pages, Pricing.”*

**From the start**
> *“First dashboard was a flat list — no tabs, no charts, no sidebar story. Refresh was manual or naive polling.”*

**Testing showed**
> *“Users asked for **at-a-glance health** and **history**. Pure lists don’t answer ‘is this getting worse?’ We also saw **stale UI** when the token expired mid-session — redirect to login with no context.”*

**We expanded**
> *“Tabs for devices vs analytics; **Chart.js** for trends; **WebSocket** status so you know you’re live; **no-cache meta** on dashboard HTML; **redirect to login with return path** so the flow isn’t frustrating.”*

---

## 8. Devices & alerts — heartbeats, agent, dedupe (1–2 min)

**Current demo**
> *“Add devices, see severity-based alerts, heartbeat and last seen. Optional **device agent** on the LAN so real gear reports in — Settings has API key for the agent.”*

**From the start**
> *“Devices were CRUD only — no heartbeat pipeline, so ‘online’ was guesswork.”*

**Testing showed**
> *“Without heartbeats, every demo looked fake. Alert **spam** without deduplication made people mute notifications — the opposite of what we want.”*

**We expanded**
> *“**Heartbeat sweep** job, agent documentation, **deduplication** on alerts, severity levels, and **notification preferences** so only the right severities hit each channel.”*

---

## 9. Analytics & charts — “is it getting worse?” (45 sec–1 min)

**Current demo**
> *“Charts show trends over time — not just current state.”*

**From the start**
> *“Analytics tab didn’t exist; dashboard was snapshot-only.”*

**Testing showed**
> *“Stakeholders asked for **evidence over time** for reports and for ‘has this happened before?’”*

**We expanded**
> *“Analytics tab with Chart.js, fed from the same API — one backend, richer frontend story.”*

---

## 10. Family — sharing without password sharing (1 min)

**Current demo**
> *“Family invitations and shared visibility — households collaborate without handing over one password.”*

**From the start**
> *“Single-user only. Real homes are multi-person.”*

**Testing showed**
> *“‘Can my partner see the alerts?’ — without family sharing, the answer was no or unsafe (shared credentials).”*

**We expanded**
> *“Family routes, invitation flow, and UI so access is **explicit** and **revocable**.”*

---

## 11. Settings — MFA QR, notifications, sessions (2–3 min)

**Current demo**
> *“Settings: **MFA** setup with QR and backup codes; **notification preferences** per channel and severity; **session list** to revoke devices; **API key** for the agent; password change.”*

**From the start**
> *“Settings was minimal — password change at best. No MFA UI, no session list.”*

**Testing showed**
> *“**MFA**: first integration threw **ModuleNotFoundError** when dependencies weren’t in the active venv — classic ‘works on my machine’ until we standardized **venv + requirements**. **QR** didn’t show or users scanned into the wrong field — we fixed layout/timing and **copy** (‘authenticator app’, not password field). **Sessions**: lost laptop scenario — changing password everywhere is painful; we needed **per-session revoke**. **Notifications**: Twilio **SMS** in some regions returns **21612** (geo/regulatory) — silent failure looks like ‘SMS is broken’; users need a **clear banner** and **WhatsApp/voice** where SMS isn’t viable.”*

**We expanded / fixed**
> *“Documented venv activation; MFA flow with backup codes; **refresh token in httpOnly cookie** so XSS can’t trivially steal long-lived tokens; **session revoke API + UI**; **SMS disabled** until compliant bundle — honest UX over fake sends; **test send** per channel in preferences.”*

---

## 12. Audit logs — accountability after the fact (1 min)

**Current demo**
> *“Audit logs show logins, failed logins, MFA changes, session revocations — IP and user agent where appropriate.”*

**From the start**
> *“No audit trail — we couldn’t answer ‘what happened?’ after an incident.”*

**Testing showed**
> *“Compliance and trust questions: *who logged in when?* *was MFA disabled?*”*

**We expanded**
> *“**AuditLogger** hooked into auth and security events; dedicated **Audit Logs** page in the nav.”*

---

## 13. Incidents — from noise to narrative (45 sec–1 min)

**Current demo**
> *“Incidents help group or review alert history — moving from raw feed to story.”*

**From the start**
> *“Only a flat alert list.”*

**Testing showed**
> *“Users wanted to **review** and **correlate** without exporting everything manually every time.”*

**We expanded**
> *“Incidents surface so post-event review is possible inside the app, not only in exports.”*

---

## 14. Security threats & compliance pages — education + trust (1 min)

**Current demo**
> *“Security Threats and Security & Compliance pages frame how we think about jamming, IP changes, and proportionate controls — not fear-mongering, but **transparent**.”*

**From the start**
> *“Features existed in code but weren’t **explained** to non-experts.”*

**Testing showed**
> *“Assessors asked *where is this documented for the user?*”*

**We expanded**
> *“Dedicated pages linked from the sidebar so security behaviour is **visible** not hidden in middleware only.”*

---

## 15. Pricing & Stripe — honest tiers (1 min)

**Current demo**
> *“Pricing connects to **Stripe** checkout and webhooks; plan limits enforced in middleware so tiers are real.”*

**From the start**
> *“Free-for-all prototype — no billing, no limits.”*

**Testing showed**
> *“Without enforcement, ‘plans’ are cosmetic. Testing required **real limits** and **webhook-driven** state.”*

**We expanded**
> *“Stripe integration, webhook handler, **plan_limits** middleware — free vs paid behaviour is consistent.”*

---

## 16. Mobile — same story, smaller screen (30–45 sec)

**Current demo**
> *“Mobile app mirrors core flows — you’re not tied to a desktop when something critical happens.”*

**From the start**
> *“Web-only; on-call users complained.”*

**Testing showed**
> *“Real incidents don’t wait until you’re at a desk.”*

**We expanded**
> *“Mobile app for login, dashboard, alerts, settings — same API, same security model.”*

---

## 17. Security in depth — layered, grown over time (2–3 min)

Speak this as a **summary** after the walkthrough, or interleave with section 11.

| Layer | From the start | Testing showed | We expanded |
|-------|----------------|----------------|-------------|
| **Auth** | JWT only | Token theft, no rotation | Short-lived access + rotating refresh; httpOnly cookie option |
| **MFA** | None | Brute force, credential stuffing | TOTP + backup codes; revoke on MFA change |
| **Rate limit** | None | Scripted login | Per IP + per user when authenticated |
| **Audit** | None | No accountability | Failed login, MFA, session revoke logged |
| **Transport** | HTTP local only | Prod needs hardening | HTTPS redirect, HSTS, CSP, X-Frame-Options, trusted hosts |
| **Notifications** | Email only | SMS blocked in regions | WhatsApp/voice; SMS off + banner; preferences + test send |
| **CI** | Ad-hoc | Ruff/pytest failures | Fixed E741-style issues; async test mocks in conftest |

**Closing line**
> *“Security isn’t one ticket — it’s **layers** we added because **testing and real use** kept showing the next gap.”*

---

## 18. Closing — problem → gap → growth → outcome (1 min)

> *“Pro-Alert solves **visibility, timeliness, and accountability** without forcing every household into an enterprise SOC. The **market gap** — too heavy vs too fragmented — is addressed with proportionate controls and honest notification behaviour. The **artefact story** is iterative: **we built, we tested, something was missing, we expanded** — from signup copy and cache to MFA and sessions, from flat lists to analytics and audit. That’s the narrative: a **working system** that **grew on evidence**, not on assumptions.”*

---

## One-page summary (appendix)

| Area | What Pro-Alert does | How it grew |
|------|---------------------|-------------|
| **Onboarding** | Strong signup + verification | API/UI alignment; cache-bust; no stale “min 8” |
| **Auth** | JWT + MFA + lockout | Rate limits; refresh rotation; httpOnly; session revoke |
| **Devices** | Agent + heartbeats | From manual CRUD to real LAN reporting |
| **Alerts** | Severity + dedupe | From spam to preferences + quiet hours |
| **Family** | Invitations | From single-user to shared households |
| **Audit** | Security events | From blind to accountable |
| **Billing** | Stripe + limits | From cosmetic tiers to enforced middleware |

---

## Suggested deliverables

- **Video:** Record in **nav order** — landing → signup → login → dashboard tabs → family → settings (MFA + sessions + test send) → audit → pricing.  
- **Report:** Use each section’s **From the start / Testing showed / We expanded** as evaluation/evidence.  
- **Slides:** One slide per major section; optional timeline slide: *prototype → heartbeats → MFA → sessions → audit → Stripe → mobile*.

---

## Repo pointers

| Topic | Location |
|-------|----------|
| Auth, MFA, sessions | `routes/auth.py` |
| Rate limiting | `middleware/security.py` |
| Plan limits | `middleware/plan_limits.py` |
| Notifications | `services/notification_service.py`, `routes/notification_preferences.py` |
| Audit | `services/audit_logger.py` |
| Security enhancements | `docs/SECURITY_ENHANCEMENTS.md` |
| Device agent | `agent/README.md`, `docs/HOW_DEVICES_CONNECT.md` |
| Signup alignment | `web/signup.html`, `web/assets/signup.js`, `main.py` |

---

*Script version: January 2026 — problems and fixes are **embedded per section**; update as the product evolves.*
