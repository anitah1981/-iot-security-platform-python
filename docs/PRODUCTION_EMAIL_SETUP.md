# Production email (password reset, verification, alerts)

For password reset, signup verification, and alert emails to work in production, the app must have SMTP configured. You set these once in your host (e.g. Railway), not per user.

## What you need to do (Railway)

1. Open Railway -> your project -> your service (the app).
2. Go to Variables.
3. Add these variables (required for email):

   SMTP_USER     = Your Gmail address (e.g. you@gmail.com)
   SMTP_PASSWORD = Gmail App Password (from Google App Passwords)
   FROM_EMAIL    = Same as SMTP_USER

4. Set the reset link domain (required so the link in the email goes to your live site):

   APP_BASE_URL  = https://iot-security-platform-python-production.up.railway.app

   (Use your exact Railway URL with https, no trailing slash.)

5. Save. Railway will redeploy.
6. After deploy open: https://your-app.up.railway.app/api/health
   You should see "email_configured": true. If false, one of the three is missing or wrong.

## Gmail App Password

1. Turn on 2-Step Verification for your Google account.
2. Go to App passwords (myaccount.google.com/apppasswords).
3. Create app password for Mail / Other (e.g. Alert-Pro).
4. Use that 16-character password as SMTP_PASSWORD.

## Check

GET /api/health -> email_configured: true means password reset and verification emails can be sent.

## Still no reset email?

1. **Check Railway logs** – In Railway, open your service -> Deployments -> click the latest deployment -> **View Logs**. Trigger "Forgot password" again, then look for:
   - `[INFO] Attempting to send password reset email to ...` – request reached the server
   - `[OK] Password reset email sent to ...` – email was sent
   - `[WARNING] Gmail SMTP not configured` or `FROM_EMAIL not set` – add or fix variables
   - `[ERROR] Email error: ...` – the message after this is the real reason (e.g. wrong app password, Gmail blocking)

2. **Check spam/junk** – Look in Spam and "All Mail" for the sender (your Gmail address).

3. **Confirm the email exists** – Use the exact address the account was created with. If it’s wrong, the app still says "link sent" but does not send an email.

4. **Verify variables** – In Railway Variables, names must be exactly: SMTP_USER, SMTP_PASSWORD, FROM_EMAIL (no typos). Redeploy after changing.
