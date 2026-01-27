# 🧪 Test & Deploy Guide

**Complete testing and deployment checklist for IoT Security Platform**

---

## 🧪 **Phase 1: Testing**

### **1. Web Application Testing**

#### **Start Server:**
```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Start server
python -m uvicorn main:app --reload --port 8000
```

#### **Test Checklist:**

**Authentication:**
- [ ] Can create account
- [ ] Can login
- [ ] Can logout
- [ ] Forgot password works
- [ ] Reset password works
- [ ] Password validation works

**Dashboard:**
- [ ] Dashboard loads
- [ ] Devices display correctly
- [ ] Alerts display correctly
- [ ] Charts load and display
- [ ] Charts resize on window resize
- [ ] Device detail panel opens
- [ ] Can add devices to groups from detail panel

**Device Management:**
- [ ] Can create device
- [ ] Can update device
- [ ] Can delete device
- [ ] Device status updates
- [ ] Groups column shows in table

**Device Grouping:**
- [ ] "Manage Groups" button works
- [ ] Can create group
- [ ] Can update group
- [ ] Can delete group
- [ ] Can add device to group (from modal)
- [ ] Can add device to group (from detail panel)
- [ ] Can remove device from group
- [ ] Group filter works
- [ ] Groups display in device table

**Alerts:**
- [ ] Alerts display correctly
- [ ] Can resolve alerts
- [ ] Alert severity colors correct
- [ ] Alert filtering works

**Notification Preferences:**
- [ ] Quiet hours toggle works
- [ ] Time pickers appear when enabled
- [ ] Settings save correctly
- [ ] Settings persist after refresh
- [ ] Test email works
- [ ] No digest section (removed)

**Audit Logs (Business Plan):**
- [ ] Page loads (shows upgrade message for non-Business users)
- [ ] Filters work
- [ ] Statistics display
- [ ] Export works (CSV/JSON)
- [ ] Pagination works

**Incident Timeline (Pro/Business Plan):**
- [ ] Page loads (shows upgrade message for non-Pro/Business users)
- [ ] Can create incident
- [ ] Can view incident details
- [ ] Timeline displays correctly
- [ ] Can add notes
- [ ] Can resolve incidents
- [ ] Correlation suggestions work

**Settings:**
- [ ] Account info displays
- [ ] Plan info displays
- [ ] Can change password
- [ ] Logout works

---

### **2. Mobile Application Testing**

#### **Setup:**
```bash
cd mobile
npm install
```

#### **Configure API:**
Edit `mobile/app.json`:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "http://localhost:8000"  // For local testing
      // Or: "apiUrl": "https://your-api-domain.com"  // For production
    }
  }
}
```

#### **Start Mobile App:**
```bash
npm start
```

#### **Test Checklist:**

**Authentication:**
- [ ] Login screen loads
- [ ] Can login with credentials
- [ ] Signup screen works
- [ ] Forgot password works
- [ ] Auto-login on app restart

**Navigation:**
- [ ] Bottom tabs work
- [ ] Can navigate between screens
- [ ] Detail screens open correctly

**Dashboard:**
- [ ] Dashboard loads
- [ ] Stats cards display
- [ ] Recent devices show
- [ ] Active alerts show
- [ ] Pull to refresh works

**Devices:**
- [ ] Device list loads
- [ ] Device details open
- [ ] Status indicators work
- [ ] Offline mode works (disconnect internet)

**Alerts:**
- [ ] Alert list loads
- [ ] Filters work
- [ ] Alert details open
- [ ] Can resolve alerts
- [ ] Offline mode works

**Settings:**
- [ ] Settings screen loads
- [ ] Account info displays
- [ ] Logout works

**Offline Mode:**
- [ ] Disconnect internet
- [ ] App shows offline indicator
- [ ] Cached data displays
- [ ] Reconnect - data refreshes

---

## 🚀 **Phase 2: Deployment**

### **Option A: Quick Deploy (Railway - Recommended)**

#### **1. Create Railway Account**
- Go to: https://railway.app
- Sign up with GitHub

#### **2. Deploy Backend**
```bash
# Connect GitHub repo
# Railway will auto-detect Python project

# Add environment variables:
MONGO_URI=mongodb+srv://...
JWT_SECRET=your-secret-key
PORT=8000
CORS_ORIGINS=https://your-domain.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

#### **3. Deploy Frontend**
- Railway serves static files automatically
- Or use Netlify/Vercel for frontend

#### **4. Update Mobile App API URL**
Edit `mobile/app.json`:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://your-railway-app.railway.app"
    }
  }
}
```

---

### **Option B: Docker Deployment**

#### **1. Build Docker Image**
```bash
docker build -t iot-security-platform .
```

#### **2. Run Container**
```bash
docker compose up -d
```

#### **3. Configure Environment**
Edit `.env` file with production values

---

### **Option C: Traditional VPS (DigitalOcean, AWS, etc.)**

#### **1. Server Setup**
```bash
# SSH into server
ssh user@your-server

# Install dependencies
sudo apt update
sudo apt install python3 python3-pip nginx

# Clone repository
git clone your-repo-url
cd iot-security-app-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### **2. Configure Environment**
```bash
# Create .env file
nano .env

# Add all environment variables
```

#### **3. Set Up Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### **4. Set Up Systemd Service**
```ini
[Unit]
Description=IoT Security Platform
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/iot-security-app-python
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

#### **5. Start Service**
```bash
sudo systemctl start iot-security
sudo systemctl enable iot-security
```

---

## 📱 **Mobile App Deployment**

### **1. Build Production Apps**

#### **iOS:**
```bash
cd mobile
eas build --platform ios
```

#### **Android:**
```bash
eas build --platform android
```

### **2. Test Production Builds**
- Download builds from EAS
- Install on test devices
- Test all features

### **3. Submit to Stores**

#### **App Store (iOS):**
1. Create App Store Connect account
2. Create app listing
3. Upload build via EAS
4. Submit for review

#### **Play Store (Android):**
1. Create Google Play Console account
2. Create app listing
3. Upload APK/AAB
4. Submit for review

---

## ✅ **Pre-Deployment Checklist**

### **Backend:**
- [ ] All environment variables set
- [ ] MongoDB connection working
- [ ] JWT_SECRET changed from default
- [ ] CORS origins configured
- [ ] Email notifications tested
- [ ] SSL/HTTPS configured
- [ ] Database backups set up

### **Frontend:**
- [ ] All pages load correctly
- [ ] API URLs point to production
- [ ] No console errors
- [ ] Responsive design works
- [ ] All features tested

### **Mobile:**
- [ ] API URL configured
- [ ] App icons added
- [ ] Push notifications configured (optional)
- [ ] Tested on physical devices
- [ ] Production builds created

---

## 🎯 **Quick Deploy Commands**

### **Local Testing:**
```bash
# Web
python -m uvicorn main:app --reload --port 8000

# Mobile
cd mobile
npm start
```

### **Production Deploy:**
```bash
# Using Docker
docker compose up -d

# Or direct
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📝 **Post-Deployment**

1. **Monitor:**
   - Check server logs
   - Monitor error rates
   - Check database performance

2. **Test:**
   - Test all features in production
   - Test on mobile devices
   - Test notifications

3. **Optimize:**
   - Monitor performance
   - Optimize database queries
   - Add caching if needed

---

**Ready to deploy!** 🚀
