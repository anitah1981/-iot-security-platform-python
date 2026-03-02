# Your operational steps – exact walkthrough

Do these four things in order. Replace `<your-live-url>` with your real Railway (or Render) URL, e.g. `https://your-app.up.railway.app`.

---

## Task 1: Run the release gate before each deploy, then check health on live URL

### When to do it
Every time **before** you deploy (e.g. before you push to main if Railway auto-deploys, or before you click Deploy).

### Step 1.1 – Run the release gate on your PC

1. Open **PowerShell**.
2. Go to the project folder:
   ```powershell
   cd c:\IoT-security-app-python
   ```
3. Run the gate (this runs security check, lint, and tests):
   ```powershell
   python scripts/release_gate.py
   ```
4. Wait until it finishes. You must see at the end:
   ```text
   [RELEASE GATE PASSED] Safe to deploy. Then verify health/ready/startup on the deployed app.
   ```
5. If you see `[RELEASE GATE FAILED]`, fix what it reports (e.g. lint or test failures) and run the command again until it passes.

### Step 1.2 – Deploy

- If you use **Railway**: push to `main` (or trigger a deploy from the Railway dashboard).
- Wait until the deploy is **finished** (green/success in Railway).

### Step 1.3 – Check health on the live URL

1. In the browser, open (replace `<your-live-url>` with your real URL):
   - `https://<your-live-url>/api/health`
   - You should see something like: `{"ok":true,"service":"pro-alert","status":"alive",...}` and the page should load (no error).
2. Then open:
   - `https://<your-live-url>/api/ready`
   - You should see something like: `{"ok":true,"database":"connected",...}`.
3. Then open:
   - `https://<your-live-url>/api/startup`
   - You should see `{"ok":true,"tasks":[...]}`.

If any of these three URLs returns an error or doesn’t load, the deploy isn’t healthy – fix the issue (e.g. env vars, MongoDB) and redeploy, then check again.

**Done for Task 1:** You’ve run the release gate before deploy and confirmed health/ready/startup on the live URL.

---

## Task 2: Complete the manual verification list against the live app and note date/URL

### When to do it
Once before go-live, and again after any big security or auth change. You need the app **live** and reachable in the browser.

### Step 2.1 – Open the checklist

- Open the file: **`docs/LIVE_VERIFICATION_CHECKLIST.md`** in your project (or in a browser if you have it on GitHub).

### Step 2.2 – Fill in the header

At the top, write:

- **Env URL:** your full live URL, e.g. `https://your-app.up.railway.app`
- **Verified on (date):** today’s date, e.g. `2026-02-28`

### Step 2.3 – Go through each item on the live app

Use `<your-live-url>` in the steps below (e.g. `your-app.up.railway.app`).

1. **HTTPS**  
   - In the browser, go to: `http://<your-live-url>` (with `http`, not `https`).  
   - You should be redirected to `https://...`.  
   - If you have `curl`, you can run: `curl -I http://<your-live-url>` and check that you get a 307 redirect to `https://`.

2. **Security headers**  
   - Run in PowerShell (replace the URL):  
     `curl -I https://<your-live-url>`  
   - In the output, check that you see headers like: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy`.

3. **API docs protection**  
   - In the browser, open: `https://<your-live-url>/docs`  
   - You should get **401 Unauthorized** (or be redirected to login), **not** the full Swagger UI.  
   - Same for: `https://<your-live-url>/redoc`.

4. **Rate limiting**  
   - Send 6 login requests in a row with a **wrong** password.  
   - Easiest: use the login page on the live site and submit wrong credentials 6 times quickly.  
   - The **6th** attempt should return an error like “Too many requests” or **429**.  
   - (If you have curl, you can do 6× `POST` to `https://<your-live-url>/api/auth/login` with wrong JSON body.)

5. **Account lockout**  
   - Use one test account.  
   - Enter the **wrong** password 5 times (so the account locks).  
   - Try to log in again – you should see a message that the account is locked.  
   - Wait **15 minutes** (or whatever your app’s lockout duration is).  
   - Log in with the **correct** password – it should work again.

6. **MFA flow**  
   - Log in to the live app.  
   - Go to Settings (or wherever MFA is set up).  
   - **Enable MFA**: follow the steps (e.g. scan QR, enter code).  
   - Log out, then log in again – you should be asked for the MFA code; enter it and confirm you get in.  
   - Use a **backup code** once (if you have them) and confirm it works.  
   - **Disable MFA** (with your password or code) and confirm you can log in without MFA again.

7. **Password reset**  
   - Use “Forgot password” on the live login page.  
   - Enter an email that receives the reset email.  
   - Open the email, click the reset link.  
   - Set a new password and submit.  
   - Log in with the **new** password and confirm it works.

8. **Admin: unlock account**  
   - You need a user with **admin** role.  
   - Lock a different account (wrong password 5 times).  
   - Log in as the **admin** user.  
   - Use the admin “Unlock account” feature for the locked user.  
   - Confirm the locked user can log in again.

9. **Admin: network monitoring**  
   - Log in as a **non-admin** user.  
   - Try to open the network monitoring page (or the API that enables/disables it). You should get **403** or “access denied”.  
   - Log in as an **admin** user.  
   - Open network monitoring – it should load and work.

10. **Audit (Business plan)**  
    - Log in as a user on **Free** or **Pro** (not Business).  
    - Try to open Audit logs (or the audit API). You should get **403** or “Business plan” message.  
    - Log in as a **Business** plan user (or upgrade a test user to Business).  
    - Open Audit logs – they should load.

11. **Health/ready/startup**  
    - You already did this in Task 1:  
      `https://<your-live-url>/api/health`, `/api/ready`, `/api/startup` all return 200 and sensible JSON.

### Step 2.4 – Mark the checklist and save

- In **LIVE_VERIFICATION_CHECKLIST.md**, tick each item you verified (e.g. change `- [ ]` to `- [x]`).
- Save the file. Optionally add a line at the bottom, e.g.:  
  `Signed off: Verified on 2026-02-28 for https://your-app.up.railway.app`

**Done for Task 2:** Manual verification list completed against the live app, with date and URL recorded.

---

## Task 3: Schedule backups, run a restore drill once, set retention

### Step 3.1 – Run a backup (first time)

1. Open **PowerShell**.
2. Go to the project:
   ```powershell
   cd c:\IoT-security-app-python
   ```
3. Set the project root so the script can load your app’s `database` module:
   ```powershell
   $env:PYTHONPATH = "c:\IoT-security-app-python"
   ```
4. Run the backup script (it uses `MONGO_URI` from your `.env`):
   ```powershell
   python scripts/backup_manual.py
   ```
5. You should see lines like `[OK] users: 5 documents -> users.json` and finally `[DONE] Backup in C:\backups\mongodb_YYYYMMDD_HHMM`.
6. Open **File Explorer**, go to **C:\backups**. You should see a folder like **mongodb_20260228_1430** with JSON files inside. That’s your backup.

### Step 3.2 – Schedule backups (e.g. weekly)

- **Option A – Windows Task Scheduler**  
  1. Open **Task Scheduler** (search “Task Scheduler” in the Start menu).  
  2. Create a new task: **Action** → **Create Basic Task**.  
  3. Name it e.g. “MongoDB backup IoT app”.  
  4. Trigger: **Weekly**, pick a day and time (e.g. Sunday 2:00 AM).  
  5. Action: **Start a program**.  
  6. Program: `powershell.exe`  
  7. Arguments (adjust path if needed):  
     `-NoProfile -Command "cd c:\IoT-security-app-python; $env:PYTHONPATH='c:\IoT-security-app-python'; python scripts/backup_manual.py"`  
  8. Finish and save.  
  9. Run the task once manually (right‑click → Run) to confirm a new folder appears under `C:\backups`.

- **Option B – Reminder**  
  If you prefer not to use Task Scheduler, put a recurring reminder (e.g. every Sunday) to run the same two commands from Step 3.1 (PYTHONPATH then `python scripts/backup_manual.py`).

### Step 3.3 – Restore drill (once)

Goal: prove you can restore from a backup. Do this when you can afford a short test.

1. **Pick a backup folder**  
   Use one of the folders under `C:\backups\mongodb_*` (e.g. the one you just created).

2. **Option A – Restore into a test MongoDB**  
   - Create a **new** database (e.g. a new Atlas cluster or a new database name) that is **not** your live DB.  
   - Use a small script or tool to load the JSON files from the backup folder into that test DB (e.g. a script that reads each `.json` and inserts into the test DB).  
   - Point your app at the test DB (e.g. change `MONGO_URI` in `.env` to the test DB), start the app, and check login, devices, alerts.  
   - When done, switch `.env` back to your real DB.

3. **Option B – Document “restore” steps**  
   If you don’t have a test DB yet, at least document what you would do:  
   - “Restore = copy backup folder to safe place; if we lose the DB, we would create a new cluster and load these JSON files (or use mongorestore if we install the tools).”  
   - Keep that note in your runbook or next to `docs/MONGODB_MANUAL_BACKUP.md`.

### Step 3.4 – Set retention

- Decide how many backups to keep (e.g. **last 4 weekly** = about one month).  
- Decide where they live (e.g. **C:\backups** plus a copy to OneDrive or an external drive).  
- Periodically (e.g. once a month) delete or archive backups older than that (e.g. delete folders in `C:\backups` older than 4 weeks).  
- Write this down in one sentence, e.g. “We keep the last 4 weekly backups in C:\backups and a copy in OneDrive; we delete backups older than 4 weeks.”

**Done for Task 3:** Backups are scheduled, you’ve done one restore drill (or documented restore steps), and retention is decided and written down.

---

## Task 4: Run the migration in each environment and complete post-migration validation

You run the migration **once per environment** (e.g. once for staging, once for production). Each environment has its own MongoDB (or its own database/cluster).

### Step 4.1 – Migration for one environment (e.g. production)

1. **Confirm backup**  
   Make sure you have a recent backup of that environment’s MongoDB (Task 3). If not, run `python scripts/backup_manual.py` with that environment’s `MONGO_URI` (or run it with `.env` set to that env).

2. Open **PowerShell** and go to the project:
   ```powershell
   cd c:\IoT-security-app-python
   ```

3. **Set MONGO_URI for this environment**  
   - If this is the **same** DB as in your `.env` (e.g. production is already in `.env`), you don’t need to set it – the script loads `.env`.  
   - If you’re migrating a **different** env (e.g. staging), set its connection string (use single quotes so `&` and `!` are safe):
     ```powershell
     $env:MONGO_URI = 'mongodb+srv://USER:PASSWORD@cluster.mongodb.net/iot_security?retryWrites=true&w=majority'
     ```
     Replace `USER`, `PASSWORD`, and `cluster` with that environment’s values.

4. Set PYTHONPATH and run the migration:
   ```powershell
   $env:PYTHONPATH = "c:\IoT-security-app-python"
   python scripts/migrate_userid_to_user_id.py
   ```

5. Check the output. You should see lines like:
   - `[MIGRATION] Connected to DB: iot_security`
   - `[devices] backfilled user_id from userId on N documents`
   - `[MIGRATION] Completed userId/user_id backfill.`
   If you see an error (e.g. `bad auth`), fix `MONGO_URI` and run again.

### Step 4.2 – Repeat for every other environment

- For **staging** (or any other env): point `MONGO_URI` at that env’s MongoDB, run the same two commands again (`PYTHONPATH` then `python scripts/migrate_userid_to_user_id.py`).  
- Do **not** run the migration twice against the same DB in the same day unless you’re re-running on purpose (it’s safe but redundant).

### Step 4.3 – Post-migration validation (per environment)

After migrating **each** environment:

1. **Migration completed**  
   You already confirmed this: no errors and “Completed userId/user_id backfill” in the script output.

2. **App flows**  
   Open the **app for that environment** (staging URL or production URL) and check:
   - Log in.
   - Devices list loads.
   - Alerts list loads.
   - Settings page loads.
   - If you have Business plan, open Audit logs and confirm they load.

3. **No regressions**  
   - Use the app normally (click around dashboard, devices, alerts).  
   - You should **not** see 500 errors or “missing field” type errors.  
   - If you do, note the page and error; we’d then check queries for `user_id`/`created_at`.

4. **Tick the runbook checklist**  
   In **docs/DEPLOYMENT_RUNBOOK.md**, under “Post-migration validation (per environment)”, tick the three bullets (migration completed, app flows verified, no query regressions) for that environment. You can add a short note, e.g. “Prod: 2026-02-28”.

**Done for Task 4:** Migration run in each environment (staging/prod), and post-migration validation checklist completed for each.

---

## Quick reference

| Task | What you do |
|------|-------------|
| **1** | Before each deploy: `python scripts/release_gate.py` → deploy → open `/api/health`, `/api/ready`, `/api/startup` on live URL. |
| **2** | Once (and after big changes): open `docs/LIVE_VERIFICATION_CHECKLIST.md`, fill Env URL and date, run through every bullet on the live app, tick and save. |
| **3** | Run `python scripts/backup_manual.py` (with PYTHONPATH set); schedule it weekly; do one restore drill; write down retention. |
| **4** | For each env: set that env’s MONGO_URI → run `python scripts/migrate_userid_to_user_id.py` → then verify app flows and no 500s; tick post-migration checklist. |

If you want, next we can turn this into a one-page printable checklist (same steps, shorter wording).
