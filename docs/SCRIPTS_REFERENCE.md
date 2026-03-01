# Scripts reference

All runnable scripts and what they do. **Update this table when you add or change scripts** so the info is always available.

**Giving a user full access (Pro + Business) without paying:** Run `python scripts/set_user_plan.py USER_EMAIL --plan business`. See `docs/ADMIN_AND_BETA_USERS.md` for admin role and beta testers.

---

## Quick reference table

| Script | What it does | When to use | Requires |
|--------|--------------|-------------|----------|
| **scripts/set_user_plan.py** | Set a user's plan (free/pro/business) or role (admin, etc.) or plan_override (full access without paying). Updates MongoDB `users` by email. | Give yourself or a consumer full access; make someone admin; give beta users free Business access. | `MONGO_URI` in .env |
| **scripts/security_gate.py** | Checks env before deploy: JWT_SECRET set and strong in production, MONGO_URI, CORS_ORIGINS, SMTP, Stripe. Exits with failure if something is wrong. | Before deploy or in CI. Run with production env to lock config. | `.env` (optional); CI sets JWT_SECRET, APP_ENV |
| **scripts/generate_secrets.py** | Prints a new JWT_SECRET (32+ chars) and suggested production env vars. Copy into .env or host. | When setting up production or rotating JWT. | None |
| **scripts/backup_manual.py** | Backs up MongoDB collections to JSON files in a timestamped folder (e.g. backups/mongodb_YYYYMMDD/). No mongodump needed. | Before major changes or on a schedule. | `MONGO_URI` in .env (not localhost) |
| **scripts/release_gate.py** | Runs security_gate, ruff lint, and pytest. Single command to pass same checks as CI before pushing. | Before git push or deploy. | Same as CI (Python, deps, .env for gate) |
| **scripts/run_critical_checklist.py** | Stub / placeholder. For pre-launch API checks use test_system.py or test_auth_flows.py; for plan/role use set_user_plan.py. | See docs/ADMIN_AND_BETA_USERS.md and LAUNCH_CHECKLIST.md. | — |
| **scripts/do_it_all_deploy.py** | Prints step-by-step instructions to go live (MongoDB Atlas, GitHub, Railway/Render) and generates a JWT_SECRET to paste. | First-time deployment. | None |
| **scripts/prepare_for_railway.py** | Prints env vars to paste into Railway (MONGO_URI, JWT_SECRET, PORT, APP_BASE_URL, CORS_ORIGINS, optional SMTP). | When deploying to Railway. | None |
| **scripts/test_mongodb_connection.py** | Tests MONGO_URI: pings MongoDB, lists DBs and collections. | After setting MONGO_URI to verify connectivity. | `MONGO_URI` |
| **scripts/migrate_userid_to_user_id.py** | One-time backfill: copies `userId` → `user_id` and `createdAt` → `created_at` where missing. Safe to run multiple times. | After deploying compatibility code that uses user_id/created_at. | `MONGO_URI` |
| **scripts/fix_dashboard_remove_block.py** | One-off: removes a specific block of lines from web/dashboard.html. | Only if that orphaned block reappears. | — |
| **change_password.py** (root) | Interactive: prompts for email, current password, new password; calls API to change password. App must be running. | When a user (or you) needs to change password via CLI. | Server on localhost:8000 (or set API_BASE) |
| **reset_password_direct.py** (root) | Resets a hardcoded user's password directly in MongoDB (no email flow). Edit script for email and new password. | Emergency reset when forgot-password email is not an option. | `MONGO_URI`, edit script for user |
| **add_test_data.py** (root) | Adds sample devices and alerts to the DB for the user in script (e.g. anitah1981@gmail.com). Uses async MongoDB. | Populate dashboard for testing. | `MONGO_URI`, user must exist |
| **create_test_data.py** (root) | Creates test devices and alerts via API (login with credentials in script, then POST devices/alerts). | Populate dashboard via API for testing. | Server running, user in script must exist |
| **upgrade_plan.py** (root) | Same kind of add-test-data script (adds devices/alerts for a user in DB). Name suggests plan upgrade but primarily adds test data. | Same as add_test_data when you want test data. | `MONGO_URI`, user must exist |
| **test_system.py** (root) | Full system test: health, login, devices, alerts, notifications, subscription, frontend pages. Set TEST_EMAIL and TEST_PASSWORD. | Pre-launch or after changes to verify app. | Server running, optional TEST_EMAIL/TEST_PASSWORD |
| **test_auth_flows.py** (root) | Auth flow tests: signup, verification, login, forgot password, token refresh, logout. | Verify auth and password reset flows. | Server running |
| **test_notifications.py** (root) | Tests notification preferences and send paths (email, etc.). | After configuring SMTP/Twilio. | Server running |
| **test_email_direct.py** (root) | Sends a test email using app's notification service / SMTP. | Verify SMTP delivery. | `MONGO_URI`, SMTP in .env, app context |

---

## Related docs

- **Admin and beta users (plan, role, full access):** `docs/ADMIN_AND_BETA_USERS.md`
- **Launch and pre-launch:** `LAUNCH_CHECKLIST.md`, `docs/LIVE_VERIFICATION_CHECKLIST.md`
- **Security:** `scripts/security_gate.py`, `docs/SECURITY_CHECKLIST.md`

---

*Last updated: when scripts or their behavior change. Keep this table in sync with the repo.*
