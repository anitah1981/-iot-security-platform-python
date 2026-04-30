# How to Take Your App Offline on Railway

## Option 1: Pause the Service (Easiest)

1. **Go to Railway Dashboard**
   - Visit https://railway.app
   - Sign in to your account

2. **Open Your Project**
   - Click on your project (`iot-security-platform-python`)

3. **Pause the Service**
   - Click on your service (the one running your app)
   - In the service panel, look for a **"Pause"** or **"Stop"** button
   - Click it to pause the service
   - The service will stop running and the URL will return an error

4. **To Bring It Back Online**
   - Click **"Resume"** or **"Start"** when ready
   - Railway will redeploy automatically

---

## Option 2: Remove Public Domain (Alternative)

1. **Go to Railway Dashboard**
   - Open your project → Service

2. **Remove Domain**
   - Go to **Settings** → **Networking** → **Public Networking**
   - Find your domain (e.g., `iot-security-platform-python-production-e18f.up.railway.app`)
   - Click the **trash/delete icon** next to the domain
   - Confirm deletion

3. **To Bring It Back Online**
   - Go back to **Settings** → **Networking**
   - Click **"Generate Domain"** again
   - Update `APP_BASE_URL` and `CORS_ORIGINS` in Variables if needed

---

## Option 3: Maintenance mode (503, keep Railway deployable)

Set in **Railway → Variables**:

```env
MAINTENANCE_MODE=true
```

Redeploy (or restart). The public site and API return **503** with JSON `{"detail":"Service temporarily unavailable","maintenance":true}`. **GET `/api/health`** and **GET `/api/ready`** still work so Railway health checks can pass.

Unset `MAINTENANCE_MODE` or set to `false` when you go live again.

**Local:** leave `MAINTENANCE_MODE` unset and run as usual (`APP_ENV=local`, `uvicorn`, etc.).

---

## Recommended: Option 1 (Pause Service)

**Why?**
- ✅ Easiest and fastest
- ✅ No configuration changes needed
- ✅ Can resume instantly when ready
- ✅ Saves resources (no charges while paused on free tier)

**Steps:**
1. Railway Dashboard → Your Project → Your Service
2. Click **"Pause"** or **"Stop"** button
3. Done! App is offline.

**To resume:**
- Click **"Resume"** or **"Start"** button

---

**Note:** If you're on Railway's free trial, pausing the service will stop any charges. The service can be resumed at any time.
