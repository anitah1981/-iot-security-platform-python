# What's left to do now

Use this list after the recent security, migration, and go-live prep work. Everything that could be done in code and docs is done; the rest is for you to run or configure.

---

## Done (in code and docs)

- **Pytest:** Datetime warnings fixed; CI runs clean with `python -m pytest tests/ -v -W default`.
- **Authz:** Sensitive routes use shared `get_current_user` / `require_admin` from `routes.auth`; documented in the runbook.
- **Migration script:** Loads `.env` from project root; project root added to path so `database` imports work when run as a script.
- **Docs:** GO_LIVE_STEPS (migration + five security steps), DEPLOYMENT_RUNBOOK (immediate actions, password-change checklist), SECURITY_CHECKLIST, runbook link to GO_LIVE_STEPS.
- **Security gate:** Rejects default JWT secrets; run before each release.

---

## Your actions (in order)

### 1. Run the migration (after backups)

For **each** deployed environment (e.g. production on Render):

- Confirm backups for that MongoDB.
- From project root, set `MONGO_URI` and run the migration.

**PowerShell (use single quotes for the URI so `&` and `!` are safe):**

```powershell
cd c:\IoT-security-app-python
$env:MONGO_URI = 'your-full-connection-string-here'
$env:PYTHONPATH = "c:\IoT-security-app-python"
python scripts/migrate_userid_to_user_id.py
```

Or if your `.env` already has `MONGO_URI` for that environment:

```powershell
$env:PYTHONPATH = "c:\IoT-security-app-python"
python scripts/migrate_userid_to_user_id.py
```

### 2. Before go-live: five production security steps

1. **JWT + env:** Run `python scripts/generate_secrets.py`, copy `JWT_SECRET`, and set it (and other production vars) in **Render** (and local `.env` if you run the app locally). See GO_LIVE_STEPS.md Step 1.
2. **HTTPS + CORS:** On Render, HTTPS is automatic. Set `ALLOWED_HOSTS` and `CORS_ORIGINS` to your live domain(s) in Render Environment.
3. **MongoDB:** Already using Atlas with auth and TLS; ensure backups are on and you’ve tested a restore once.
4. **Security gate:** Before each deploy, run `python scripts/security_gate.py` with production env (or ensure CI runs it). It must print "Security gate passed."
5. **Checklist:** After deploy, work through `docs/SECURITY_CHECKLIST.md` against your **live** site and fix anything that fails.

### 3. GitHub

- **Do not** commit or push `.env` or any file containing passwords or secrets. `.env` is in `.gitignore`.
- You **can** commit and push code and doc changes (runbook, GO_LIVE_STEPS, migration script, etc.) so the repo is up to date.

---

## Quick reference

| Item | Where |
|------|--------|
| Migration commands | docs/GO_LIVE_STEPS.md (Part 1) |
| Five security steps | docs/GO_LIVE_STEPS.md (Part 2) |
| Full security checklist | docs/SECURITY_CHECKLIST.md |
| When you change MongoDB password | docs/DEPLOYMENT_RUNBOOK.md (section "When you change the MongoDB password") |
