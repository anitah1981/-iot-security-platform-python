# ✅ Final Deployment Checklist

**Complete checklist before going live**

---

## 🔧 **Pre-Deployment Setup**

### **1. Environment Variables**
- [ ] `MONGO_URI` - MongoDB connection string
- [ ] `JWT_SECRET` - Changed from default (32+ characters)
- [ ] `PORT` - Set to 8000 (or your port)
- [ ] `CORS_ORIGINS` - Your production domain(s)
- [ ] `SMTP_USER` - Gmail address
- [ ] `SMTP_PASSWORD` - Gmail app password
- [ ] `FROM_EMAIL` - Sender email
- [ ] `APP_BASE_URL` - Your production URL

### **2. Database**
- [ ] MongoDB Atlas cluster created
- [ ] Connection string configured
- [ ] Network access allowed (IP whitelist or 0.0.0.0/0)
- [ ] Database user created
- [ ] Indexes created (automatic on first run)

### **3. Security**
- [ ] JWT_SECRET is strong and unique
- [ ] CORS origins restricted to your domain
- [ ] HTTPS/SSL configured
- [ ] Security headers enabled (already in code)

---

## 🧪 **Testing Checklist**

### **Web Application:**
- [ ] Server starts without errors
- [ ] Can create user account
- [ ] Can login
- [ ] Dashboard loads
- [ ] Devices display
- [ ] Alerts display
- [ ] Charts load
- [ ] Device grouping works
- [ ] Notification preferences save
- [ ] Email notifications work
- [ ] Audit logs accessible (Business plan)
- [ ] Incident timeline accessible (Pro/Business plan)

### **Mobile Application:**
- [ ] App builds without errors
- [ ] Can login
- [ ] Dashboard loads
- [ ] Devices list loads
- [ ] Alerts list loads
- [ ] Offline mode works
- [ ] Push notifications register

---

## 🚀 **Deployment Steps**

### **Backend Deployment:**

**Option A: Railway (Recommended)**
1. [ ] Create Railway account
2. [ ] Connect GitHub repository
3. [ ] Add environment variables
4. [ ] Deploy
5. [ ] Test production URL

**Option B: Docker**
1. [ ] Build Docker image
2. [ ] Run container
3. [ ] Configure reverse proxy (nginx)
4. [ ] Set up SSL

**Option C: VPS**
1. [ ] Set up server
2. [ ] Install dependencies
3. [ ] Clone repository
4. [ ] Configure environment
5. [ ] Set up systemd service
6. [ ] Configure nginx
7. [ ] Set up SSL

### **Mobile App Deployment:**
1. [ ] Update API URL in `mobile/app.json`
2. [ ] Build iOS app (EAS)
3. [ ] Build Android app (EAS)
4. [ ] Test production builds
5. [ ] Submit to App Store
6. [ ] Submit to Play Store

---

## ✅ **Post-Deployment Verification**

### **Web App:**
- [ ] Homepage loads
- [ ] Can sign up
- [ ] Can login
- [ ] Dashboard works
- [ ] All features accessible
- [ ] HTTPS working
- [ ] No console errors

### **Mobile App:**
- [ ] Can connect to production API
- [ ] Login works
- [ ] All screens load
- [ ] Data syncs correctly
- [ ] Push notifications work (if configured)

### **Notifications:**
- [ ] Email notifications send
- [ ] Test email arrives
- [ ] Alert emails work
- [ ] SMS/WhatsApp/Voice (if configured)

---

## 📊 **Monitoring Setup (Optional but Recommended)**

- [ ] Error tracking (Sentry, Rollbar, etc.)
- [ ] Uptime monitoring (UptimeRobot, Pingdom)
- [ ] Log aggregation (Logtail, Papertrail)
- [ ] Performance monitoring (New Relic, Datadog)

---

## 🎯 **Quick Deploy Commands**

### **Test Locally:**
```bash
# Web
python -m uvicorn main:app --reload --port 8000

# Mobile
cd mobile
npm start
```

### **Deploy Production:**
```bash
# Docker
docker compose up -d

# Or direct
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🎉 **You're Ready!**

Once all items are checked:
1. ✅ Deploy backend
2. ✅ Deploy frontend (or serve from backend)
3. ✅ Update mobile app API URL
4. ✅ Build mobile apps
5. ✅ Test everything
6. ✅ Go live! 🚀

---

**Good luck with your deployment!** 🎊
