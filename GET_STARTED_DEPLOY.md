# 🚀 Get Started - Deploy Your App Live (5-10 minutes)

**Everything is ready. Follow these steps:**

---

## Quick Start (3 commands)

```bash
# 1. Get your MongoDB connection string (see Step 1 below)
# 2. Generate Railway env vars
python scripts\prepare_for_railway.py

# 3. Test MongoDB connection (optional)
MONGO_URI=your-connection-string python scripts\test_mongodb_connection.py
```

Then follow **DEPLOY_NOW_STEPS.md** for the complete Railway deployment.

---

## What's Already Done ✅

- ✅ **Procfile** - Railway/Render can start the app
- ✅ **railway.json** - Railway-specific config
- ✅ **.env.example** - All production variables documented
- ✅ **Helper scripts** - Generate secrets, test connections, prepare env vars
- ✅ **Deployment docs** - Step-by-step guides

---

## Step 1: MongoDB Atlas (You Do This)

Since you're logged into MongoDB Atlas:

1. **Create cluster** → Free tier (M0) → Create
2. **Database Access** → Add user → Copy password
3. **Network Access** → Allow 0.0.0.0/0
4. **Database → Connect → Drivers → Python** → Copy connection string
5. **Replace `<password>`** with your password
6. **Add `/iot_security`** at the end

**Test it:**
```bash
MONGO_URI=your-connection-string python scripts\test_mongodb_connection.py
```

---

## Step 2: Railway Deployment

1. **Go to**: https://railway.app → Sign in with GitHub
2. **New Project** → Deploy from GitHub → Select your repo
3. **Settings → Networking** → Generate domain (copy the URL)
4. **Variables** → Add these (run `python scripts\prepare_for_railway.py` first to get JWT_SECRET):

   - `MONGO_URI` = your Atlas connection string
   - `JWT_SECRET` = from the script output
   - `PORT` = `8000`
   - `APP_ENV` = `production`
   - `APP_BASE_URL` = your Railway URL
   - `CORS_ORIGINS` = your Railway URL

5. **Wait for deploy** → Open your Railway URL → Test signup/login

---

## Full Details

- **Complete steps**: `DEPLOY_NOW_STEPS.md`
- **Deployment options**: `docs/DEPLOYMENT.md`
- **Security checklist**: `docs/SECURITY_CHECKLIST.md`

---

## Your App is Ready! 🎉

Once deployed, users can:
- Sign up and log in
- Add devices (manually or via discovery)
- See devices online/offline (with device agent)
- Get security alerts
- Use mobile apps (update `mobile/app.json` with Railway URL)
