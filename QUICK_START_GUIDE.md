# 🚀 Quick Start Guide - Get Live in 45 Minutes!

This guide will get your IoT Security Platform running with real notifications.

## ✅ Checklist

- [ ] **Step 1**: Gmail SMTP Setup (5 min)
- [ ] **Step 2**: Update .env file (2 min)
- [ ] **Step 3**: Start server (1 min)
- [ ] **Step 4**: Test notifications (5 min)
- [ ] **Step 5**: Deploy to production (20-30 min)

---

## 📧 Step 1: Gmail SMTP Setup (5 minutes)

### A. Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Find **"2-Step Verification"**
3. Click **"Get Started"** and follow the steps
4. Complete the setup (they'll text you a code)

### B. Create App Password
1. Go to: https://myaccount.google.com/apppasswords
2. **Select app**: Choose "Mail"
3. **Select device**: Choose "Other (Custom name)"
4. Type: **"IoT Security Platform"**
5. Click **"Generate"**
6. **COPY THE 16-CHARACTER PASSWORD**
   - Example format: `abcd efgh ijkl mnop`
   - **You won't see it again!**

---

## 🔧 Step 2: Update .env File (2 minutes)

Open your `.env` file and update these lines:

```env
# Gmail SMTP (REQUIRED for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com          # ⬅️ Your Gmail address
SMTP_PASSWORD=abcd efgh ijkl mnop       # ⬅️ App password from Step 1B
FROM_EMAIL=your.email@gmail.com         # ⬅️ Your Gmail address

# MongoDB (Should already be set)
MONGO_URI=mongodb+srv://...your-atlas-connection-string...

# JWT Secret (Should already be set)
JWT_SECRET=your-secret-key-here

# Port
PORT=8000

# CORS
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

**Optional - Twilio** (for SMS/WhatsApp/Voice):
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 🎯 Step 3: Start Server (1 minute)

Open terminal and run:

```bash
# Activate virtual environment (if not already active)
# Windows:
.\venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Start the server
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Starting IoT Security Backend...
INFO:     Heartbeat sweep started
INFO:     Backend ready
```

✅ **Server is running!**

---

## 🧪 Step 4: Test Notifications (5 minutes)

### Option A: Use Test Script (Recommended)

1. **Edit the test script**:
   ```bash
   # Open test_notifications.py
   # Change line 10: TEST_USER_EMAIL = "your@email.com"
   ```

2. **Run the test**:
   ```bash
   python test_notifications.py
   ```

3. **Check your email!**
   - Should receive HTML email with colored badge
   - Check spam folder if not in inbox

### Option B: Manual Testing via Dashboard

1. **Open browser**: http://localhost:8000

2. **Sign up**: 
   - Email: your@email.com
   - Password: Test123!
   - Full Name: Your Name

3. **Create a device**:
   - Device ID: camera-001
   - Name: Front Door Camera
   - Type: Camera
   - IP: 192.168.1.100

4. **Create an alert** (via API or device going offline):
   ```bash
   # Get your token from browser (localStorage)
   curl -X POST http://localhost:8000/api/alerts \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "device_id": "YOUR_DEVICE_ID",
       "type": "security",
       "severity": "high",
       "message": "Test alert - suspicious activity"
     }'
   ```

5. **Check your email!** 📧

---

## 🚀 Step 5: Deploy to Production (20-30 minutes)

### Option A: Railway (Easiest - $5/month)

1. **Create account**: https://railway.app
2. **Connect GitHub**: Link your repository
3. **Create new project**: 
   - New Project → Deploy from GitHub
   - Select your repo
4. **Add environment variables**:
   - Copy ALL variables from your local `.env`
   - Make sure MONGO_URI points to MongoDB Atlas
   - Update CORS_ORIGINS to your Railway URL
5. **Deploy**: Automatic on push to main branch
6. **Test**: Visit your Railway URL

**Cost**: ~$5-20/month depending on usage

### Option B: Render (Free tier available)

1. **Create account**: https://render.com
2. **New Web Service**:
   - Connect your GitHub repo
   - Branch: main
3. **Configure**:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. **Environment Variables**:
   - Add all from your `.env`
   - Set PORT=10000
5. **Create Web Service**: Click deploy
6. **Test**: Visit your Render URL

**Cost**: Free tier available, $7/month for production

---

## 🎉 Success Checklist

After completing all steps:

- [ ] ✅ Server runs locally without errors
- [ ] ✅ Can sign up and login
- [ ] ✅ Can create devices
- [ ] ✅ Can create alerts
- [ ] ✅ Email notifications arrive (with HTML formatting)
- [ ] ✅ Dashboard shows devices and alerts
- [ ] ✅ Deployed to production (Railway/Render)
- [ ] ✅ Production URL works

---

## 🆘 Troubleshooting

### Email not arriving?

1. **Check server logs** for error messages:
   ```
   ❌ Email error: [535] Username and Password not accepted
   ```
   → Wrong Gmail password, regenerate app password

2. **Check spam folder**

3. **Verify .env file**:
   - No quotes around values
   - Correct Gmail address
   - Correct app password (16 chars with spaces removed)

4. **Test Gmail credentials manually**:
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your@gmail.com', 'your-app-password')
   print("✅ Login successful!")
   ```

### Server won't start?

1. **Check MongoDB connection**:
   - Make sure MONGO_URI is correct
   - Test connection in MongoDB Compass

2. **Check Python version**: Must be 3.10+
   ```bash
   python --version
   ```

3. **Reinstall dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Other issues?

- Check `docs/API_KEYS_SETUP.md` for detailed troubleshooting
- Check `docs/DEPLOYMENT.md` for deployment issues
- Check server console output for error messages

---

## 📊 What You'll Have

After completing this guide:

✅ **Fully functional IoT security platform**
- Web dashboard at real URL
- Email notifications working
- Device monitoring active
- Alert system operational

✅ **Production ready**
- HTTPS enabled
- Cloud database
- Automatic deployments
- Professional email notifications

✅ **Ready to use**
- Add real devices
- Monitor your IoT devices
- Receive alerts
- Resolve issues

---

## 🎯 Next Steps

Once live, you can:

1. **Add more devices**: Register your actual IoT devices
2. **Configure alerts**: Set up custom alert rules
3. **Enable SMS/WhatsApp**: Add Twilio for multi-channel notifications
4. **Custom domain**: Point your domain to the app
5. **Monitor usage**: Track alerts and device health
6. **Scale up**: Add more features from Path 2 or Path 3

---

## 💰 Cost Summary

### Minimal Setup (Email only):
- MongoDB Atlas: **FREE** (512MB tier)
- Gmail SMTP: **FREE**
- Railway/Render: **$0-7/month**
- **Total: $0-7/month**

### Full Setup (Email + SMS + WhatsApp):
- MongoDB Atlas: **FREE**
- Gmail SMTP: **FREE**
- Twilio: **~$1-5/month** (pay per use)
- Railway/Render: **$5-7/month**
- **Total: $6-12/month**

---

## 🎓 Learning Resources

- **API Docs**: http://localhost:8000/docs
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas
- **FastAPI**: https://fastapi.tiangolo.com
- **Twilio**: https://www.twilio.com/docs

---

**Questions?** Check the main `README.md` or detailed docs in the `docs/` folder.

**Ready to go live?** Start with Step 1! 🚀
