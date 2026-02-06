# 🚀 Deploy the App Now - Complete Step-by-Step

Follow these steps **in order** to get your IoT Security app live on Railway.

---

## ✅ Step 1: Get Your MongoDB Atlas Connection String

**You're already logged into MongoDB Atlas, so:**

1. **Create or use a cluster**:
   
   **If you see "The limit for free tier clusters in this project has been reached":**
   - **Option A (Recommended)**: Use your existing free cluster:
     - Go to **"Database"** → Click on your existing cluster
     - Skip to Step 2 (Create database user) below
   - **Option B**: Delete an old unused cluster, then create a new free one:
     - Go to **"Database"** → Click the **"..."** menu on an old cluster → **"Terminate"**
     - Then create a new free cluster
   - **Option C**: Use **Flex** ($0.011/hour ≈ $8/month) for this project:
     - Select **"Flex"** → Choose provider/region → **"Create Deployment"**
   
   **If you don't have a cluster yet:**
   - Click **"Create"** or **"Build a Database"**
   - Choose **FREE** tier (M0) if available
   - Select provider/region (AWS, closest to you)
   - Click **"Create"** (takes 1-3 minutes)

2. **Create database user**:
   - Go to **"Database Access"** → **"Add New Database User"**
   - Username: `iotapp` (or your choice)
   - Password: Click **"Autogenerate Secure Password"** → **Copy** (save it!)
   - Privileges: **"Atlas admin"**
   - Click **"Add User"**

3. **Allow network access**:
   - Go to **"Network Access"** → **"Add IP Address"**
   - Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - Click **"Confirm"**

4. **Get connection string**:
   - Go to **"Database"** → **"Connect"** → **"Drivers"**
   - Choose **"Python"** → Version **"3.12 or later"**
   - Copy the connection string (looks like `mongodb+srv://iotapp:<password>@cluster0.xxxxx.mongodb.net/`)
   - **Replace `<password>`** with the password you copied in step 2
   - **Add database name**: Change `/` at the end to `/iot_security?retryWrites=true&w=majority`
   - Final example: `mongodb+srv://iotapp:YourPassword123@cluster0.abc123.mongodb.net/iot_security?retryWrites=true&w=majority`

5. **Test the connection** (optional but recommended):
   ```bash
   cd c:\IoT-security-app-python
   MONGO_URI=your-connection-string-here python scripts\test_mongodb_connection.py
   ```
   Should print: `✓ Connection successful!`

---

## ✅ Step 2: Push Code to GitHub

**If your code isn't on GitHub yet:**

```bash
cd c:\IoT-security-app-python
git init
git add .
git commit -m "IoT Security Platform - ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

(Replace `YOUR-USERNAME` and `YOUR-REPO` with your actual GitHub username and repo name)

---

## ✅ Step 3: Deploy to Railway

1. **Go to Railway**: https://railway.app
2. **Sign in** with GitHub
3. **New Project** → **"Deploy from GitHub repo"**
4. **Select your repo** (`IoT-security-app-python` or whatever you named it)
5. **Wait for first build** (Railway auto-detects Python and builds)

---

## ✅ Step 4: Get Your Railway URL

1. In Railway, click on your **service** (the one that just deployed)
2. Go to **"Settings"** tab → **"Networking"**
3. Click **"Generate Domain"**
4. Copy the URL (e.g., `https://your-app-production.up.railway.app`)

---

## ✅ Step 5: Add Environment Variables

1. In Railway, go to your service → **"Variables"** tab
2. Click **"New Variable"** and add these **one by one**:

   | Variable | Value |
   |----------|-------|
   | `MONGO_URI` | Your MongoDB Atlas connection string from Step 1 |
   | `JWT_SECRET` | Run `python scripts\prepare_for_railway.py` and copy the JWT_SECRET it prints |
   | `PORT` | `8000` |
   | `APP_ENV` | `production` |
   | `APP_BASE_URL` | Your Railway URL from Step 4 (e.g., `https://your-app-production.up.railway.app`) |
   | `CORS_ORIGINS` | Same as APP_BASE_URL (e.g., `https://your-app-production.up.railway.app`) |

3. **Save** (Railway auto-redeploys when you add variables)

---

## ✅ Step 6: Test Your Live App

1. **Wait for deployment** to finish (check Railway logs)
2. **Open your Railway URL** in a browser
3. **You should see**: Landing page or login page
4. **Test signup**: Create an account
5. **Test login**: Sign in
6. **Go to Dashboard**: Should see "IoT Device Management"
7. **Go to Settings**: Should see all sections including "Device agent key"

---

## ✅ Step 7: Optional - Email Notifications

If you want email (signup verification, password reset, alerts):

1. **Gmail**: Enable 2FA → Create App Password (https://myaccount.google.com/apppasswords)
2. **In Railway Variables**, add:
   - `SMTP_HOST=smtp.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USER=your@gmail.com`
   - `SMTP_PASSWORD=<your Gmail App Password>`
   - `FROM_EMAIL=your@gmail.com`
3. **Redeploy** (Railway auto-redeploys when you add variables)

---

## 🎉 Done!

Your app is now live! Share the Railway URL with users or add a custom domain in Railway Settings.

**Next steps:**
- Update mobile app `mobile/app.json` → set `apiUrl` to your Railway URL
- Update device agent `.env` → set `API_BASE_URL` to your Railway URL
