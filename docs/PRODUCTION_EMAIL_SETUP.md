# Production email (password reset, verification, alerts)

For password reset, signup verification, and alert emails to work in production, the app must have SMTP configured. You set these once in your host (e.g. Railway), not per user.

## What you need to do (Railway)

1. Open Railway -> your project -> your service (the app).
2. Go to Variables.
3. Add these three variables:

   SMTP_USER    = Your Gmail address (e.g. you@gmail.com)
   SMTP_PASSWORD = Gmail App Password (from Google App Passwords)
   FROM_EMAIL   = Same as SMTP_USER

4. Save. Railway will redeploy.
5. After deploy open: https://your-app.up.railway.app/api/health
   You should see "email_configured": true. If false, one of the three is missing or wrong.

## Gmail App Password

1. Turn on 2-Step Verification for your Google account.
2. Go to App passwords (myaccount.google.com/apppasswords).
3. Create app password for Mail / Other (e.g. Alert-Pro).
4. Use that 16-character password as SMTP_PASSWORD.

## Check

GET /api/health -> email_configured: true means password reset and verification emails can be sent.
