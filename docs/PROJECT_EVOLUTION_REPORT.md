# Pro-Alert: Full Project Evolution Report

**Report date:** January 2026  
**Repository:** https://github.com/anitah1981/-iot-security-platform-python

---

## 1. How the App Started

### Origins
The project began as an **IoT Security Monitoring Platform** – a web application to monitor smart home and IoT devices, track their online/offline status, and alert users when devices go offline or behave suspiciously.

### Initial Technology Stack
- **Backend:** FastAPI (Python)
- **Database:** MongoDB (Atlas for production)
- **Frontend:** Vanilla JavaScript + HTML/CSS
- **Auth:** JWT + bcrypt
- **Email:** Gmail SMTP

### Core MVP (Minimum Viable Product)
- User signup/login
- Device registration (CRUD)
- Alert system with severity levels
- Heartbeat endpoint for device status
- Basic dashboard showing devices and alerts
- Email notifications when alerts were created

---

## 2. Evolution Timeline & Major Phases

### Phase 1: Foundation & Notifications (Early Development)
**What was built:**
- Email notifications via Gmail SMTP with HTML templates
- Dashboard auto-refresh (every 10 seconds) with "Last Updated" indicator
- Real-time WebSocket updates (Socket.IO)
- Green flash animation on refresh, connection status (Live/Disconnected)
- Basic security: strong password validation, rate limiting, security headers

**Why:** To make the app usable for real monitoring – users needed live feedback and notifications when devices went offline.

---

### Phase 2: Revenue & Subscriptions
**What was built:**
- Stripe integration (checkout, subscriptions, webhooks)
- Three tiers: Free (5 devices), Pro (£4.99/mo, 25 devices), Business (£9.99/mo, unlimited)
- Pricing page with plan comparison
- Subscription management UI and Stripe Customer Portal
- Plan limits middleware (device count, history retention)
- Automatic alert cleanup by plan (30/90/365 days)
- Usage dashboard in Settings

**Why:** To turn the app into a SaaS business capable of generating revenue. The roadmap called for payments before other advanced features.

---

### Phase 3: Multi-Channel Notifications & Device Agent
**What was built:**
- Twilio integration: SMS, WhatsApp, voice calls
- Notification preferences (per-user, per-channel, per-severity)
- **Device agent** (`agent/`): A Python script that runs on the user's LAN (Raspberry Pi, PC, NAS), checks devices by TCP port, and sends heartbeats to the platform. Real devices (Alexa, Ring, cameras) can then show as online/offline.
- Device agent API key (Settings → Connect real devices)
- Auto-enrollment of devices when the agent sends heartbeats with a new device_id

**Why:** Users needed multiple ways to be alerted (not just email), and the platform needed a way to connect to real IoT devices that don't have native APIs (Ring, Alexa, etc.). The agent fills that gap by running on the same network and probing devices.

---

### Phase 4: Family Sharing, Groups & Advanced Features
**What was built:**
- Family sharing: invite members, shared device view, shared alerts
- Device groups for organization
- Audit logs (Business plan)
- Incident timeline and correlation (Pro/Business)
- Alert exports (PDF, CSV)
- Network discovery: scan subnet, add discovered devices
- Network settings (router IP configuration)

**Why:** To support households and small businesses, improve organization of devices, and meet compliance/audit needs for higher tiers.

---

### Phase 5: Security & Production Hardening
**What was built:**
- Email verification (signup flow)
- Password reset (forgot password, token-based reset links)
- Account lockout after failed logins
- MFA (2FA) support
- Security monitor: suspicious IP detection, rapid IP change alerts, WiFi jamming patterns
- Network monitor: DNS hostname change detection, unknown device alerts (cloud-side; limited for private LANs)

**Why:** Production readiness required proper auth flows, password recovery, and basic threat detection.

---

### Phase 6: Deployment & Operations
**What was built:**
- Railway deployment support (Procfile, railway.json)
- Docker Compose setup
- Production email setup (SMTP, FROM_EMAIL, App Passwords)
- HTTPS setup and security checklists
- Runbooks: deployment, take site offline, backup, restore

**Why:** To get the app live and operable in production with clear procedures.

---

### Phase 7: Accuracy & UX Improvements (Recent)
**What was built:**
- **Device offline accuracy:** Devices (e.g. doorbells) were often shown offline because the agent checks TCP port 80; many IoT devices don't listen there. Changes:
  - `"check": "none"` in agent config – skip port check for cloud-only devices
  - `offlineOnlyWhenMissedHeartbeats` – mark offline only when heartbeats stop, not from agent reachability
  - Shorter offline threshold (30–90s instead of 120s) for faster detection
  - Per-device `offlineAfterSeconds` (30–300s) for high-security devices
- **Multi-port support:** `"ports": [80, 443, 554, ...]` in agent – device online if any port responds
- **Dashboard/family fixes:** Correct device counts (filter by user, exclude soft-deleted), timeouts for API calls, fix duplicate IDs causing "Loading…" stuck

**Why:** False "offline" status and wrong device counts undermined trust. The changes improved correctness and security posture.

---

### Phase 8: Network Watchdog & CIA Alignment
**What was built:**
- **Network watchdog** (`agent/network_watchdog.py`):
  - DNS server change detection – compare system DNS to EXPECTED_DNS, alert if changed
  - Unknown device detection – ping sweep + ARP, compare to known devices, alert on new IPs
- **Platform endpoint:** `POST /api/agent/security-report` – receives reports from agent, creates security alerts
- **Integrations:** Watchdog runs alongside device agent (every 60s by default)
- **Documentation:** `docs/SECURITY_AND_AVAILABILITY.md` – CIA alignment, port coverage, practical next steps

**Why:** Users wanted detection of DNS tampering and unauthorized devices on the network. The cloud app cannot scan private LANs, so this logic runs in the agent on the user's network.

---

### Phase 9: Modern UI & Run Automatically
**What was built:**
- **UI refresh:** Inter font, shorter transitions (150–250ms), updated cards/buttons/inputs, cleaner typography
- **Agent auto-run:** Documentation for Task Scheduler (Windows), systemd (Linux), NSSM, Docker – so the agent runs at boot without manual start

**Why:** To make the app feel modern and ensure the agent runs reliably without user intervention.

---

## 3. Architecture Overview

### Backend
- FastAPI with async MongoDB (Motor)
- JWT auth, bcrypt, rate limiting (slowapi)
- Background tasks: heartbeat sweep, retention cleanup, device status monitor, network monitor (optional)

### Frontend
- Vanilla JS (no framework) – landing, login, signup, dashboard, settings, pricing, family, etc.
- Socket.IO client for real-time updates
- Chart.js for analytics

### Agent (On-User LAN)
- `device_agent.py` – heartbeats + port checks
- `network_watchdog.py` – DNS + unknown device detection
- `discover.py` – network scan, send discovered devices to platform

### Deployment
- Railway, Render, Docker
- MongoDB Atlas
- SMTP (Gmail), Twilio (SMS/WhatsApp/Voice), Stripe (payments)

---

## 4. Key Changes & Why

| Change | Why |
|--------|-----|
| Stripe integration | Enable subscriptions and revenue |
| Plan limits | Enforce Free/Pro/Business tiers |
| Device agent | Connect real IoT devices without native APIs |
| Multi-port & check:none | Reduce false "offline" for doorbells/cameras |
| Shorter offline threshold | Faster detection of WiFi/DNS compromise |
| Network watchdog | Detect DNS changes and unknown devices on LAN |
| Family sharing | Support households and shared devices |
| Password reset (background task) | Avoid cold-start timeout on serverless |
| Forgot-password uses fetch() | Work when app.js doesn't load |
| Device count filter (userId, isDeleted) | Correct "Your devices: X" and family counts |
| Modern UI (Inter, transitions) | Improved look and perceived responsiveness |

---

## 5. Current State

### Production-Ready
- Auth (signup, login, MFA, password reset, email verification)
- Device management, heartbeats, alerts
- Multi-channel notifications (Email, SMS, WhatsApp, Voice)
- Stripe subscriptions and plan limits
- Family sharing, device groups
- Device agent + network watchdog
- Deployable to Railway/Docker

### Optional / Tiered
- Alert exports (Pro+)
- Audit logs (Business)
- Incident timeline (Pro/Business)
- Network monitoring (ENABLE_NETWORK_MONITORING)

### Mobile
- React Native / mobile app exists in repo (separate build/deploy path)

---

## 6. Documentation Map

- `README.md` – overview, quick start
- `docs/SECURITY_AND_AVAILABILITY.md` – CIA, offline thresholds, port guidance, practical next steps
- `docs/HOW_DEVICES_CONNECT.md` – how devices are added and connected
- `agent/README.md` – device agent setup, watchdog, run as service
- `STRIPE_SETUP_GUIDE.md` – payment configuration
- `docs/TAKE_SITE_OFFLINE.md` – how to take the site offline
- `docs/DEPLOYMENT_RUNBOOK.md` – deployment procedures

---

## 7. Summary

**Pro-Alert** started as an IoT monitoring MVP with devices, alerts, and email. It evolved into a full SaaS platform with subscriptions, multi-channel notifications, a device agent for real hardware, family sharing, security monitoring, and a network watchdog for DNS and unknown-device detection. Recent work focused on accuracy (offline detection, device counts), security posture (shorter thresholds, DNS/unknown-device alerts), and UX (modern UI, agent auto-run). The app is deployable to Railway and ready for production use.
