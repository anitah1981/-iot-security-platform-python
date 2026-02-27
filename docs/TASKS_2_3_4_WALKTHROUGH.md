# Tasks 2, 3, 4 – What was done and what you do

One place for the exact steps. Env URL: https://iot-security-platform-python-production.up.railway.app

---

## Task 2: Live verification

### Done automatically (2026-02-27)

- Backup run: python scripts/backup_manual.py ran successfully; backup in C:\backups\mongodb_20260227_2303.
- Health: GET /api/health returns 200, ok true.
- API docs: Unauthenticated GET /docs returns 401 (Not authenticated).
- Rate limit: 6 rapid failed logins were tried; all returned 401. Verify 6th returns 429 in browser if your limit is 5.

### You still do (in the live app)

Use LIVE_VERIFICATION_CHECKLIST.md. Check off: HTTPS redirect, security headers, rate limiting, lockout, MFA, password reset, admin unlock, admin network monitoring, audit Business-only, health/ready/startup. Then set Verified on (date) on the checklist.

---

## Task 3: Backups

### Done

- Backup run: Manual backup completed; output in C:\backups\mongodb_20260227_2303.
- Scheduled task: Windows task "MongoDB backup IoT app" created (weekly Sunday 02:00, runs scripts/run_backup.ps1).
- Restore and retention: RESTORE_NOTES.md documents restore steps and suggested retention (e.g. keep last 4 weekly; prune older; copy latest to OneDrive monthly).

### You still do

1. Run the scheduled task once manually (Task Scheduler, right-click Run) and confirm a new folder under C:\backups.
2. Restore drill once: restore one backup into a test DB or document the steps in RESTORE_NOTES.md.
3. Write down your retention policy (e.g. in RESTORE_NOTES.md or runbook).

---

## Task 4: Migration and post-migration

### Done

- Production migration already run for production DB.
- With only production, there is nothing else to run for migration.

### You still do

1. Post-migration validation on the live app: verify login, devices list, alerts list, settings load without 500s; if Business user, audit logs work. Then tick and date the Post-migration validation section in DEPLOYMENT_RUNBOOK.md.
2. If you add staging later: run migrate_userid_to_user_id.py with that env MONGO_URI, then same post-migration checks.
