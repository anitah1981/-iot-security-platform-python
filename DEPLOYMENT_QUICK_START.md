# 🚀 Quick Deployment Guide

**Fastest way to get your IoT Security Platform live**

---

## ⚡ **Option 1: Railway (Fastest - 10 minutes)**

### **Steps:**

1. **Create Railway Account**
   - Go to: https://railway.app
   - Sign up with GitHub

2. **Deploy from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway auto-detects Python

3. **Add Environment Variables**
   In Railway dashboard, add:
   ```
   MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/iot_security
   JWT_SECRET=your-super-secret-key-32-chars-minimum
   PORT=8000
   CORS_ORIGINS=https://your-app.railway.app
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-gmail-app-password
   FROM_EMAIL=your-email@gmail.com
   ```

4. **Deploy**
   - Railway automatically builds and deploys
   - Get your app URL: `https://your-app.railway.app`

5. **Update Mobile App**
   Edit `mobile/app.json`:
   ```json
   {
     "expo": {
       "extra": {
         "apiUrl": "https://your-app.railway.app"
       }
     }
   }
   ```

**Done!** Your app is live! 🎉

---

## 🐳 **Option 2: Docker (5 minutes)**

### **Steps:**

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. **Deploy**
   ```bash
   docker compose up -d
   ```

3. **Access**
   - Web: http://localhost:8000
   - API: http://localhost:8000/api

**Done!** Running locally with Docker! 🐳

---

## ☁️ **Option 3: VPS (DigitalOcean/AWS - 30 minutes)**

### **Steps:**

1. **Create VPS**
   - DigitalOcean Droplet (Ubuntu 22.04)
   - Or AWS EC2 instance
   - Minimum: 1GB RAM, 1 CPU

2. **SSH into Server**
   ```bash
   ssh root@your-server-ip
   ```

3. **Install Dependencies**
   ```bash
   apt update
   apt install -y python3 python3-pip python3-venv nginx git
   ```

4. **Clone & Setup**
   ```bash
   git clone your-repo-url
   cd iot-security-app-python
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your values
   ```

6. **Set Up Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/iot-security.service
   ```
   ```ini
   [Unit]
   Description=IoT Security Platform
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/root/iot-security-app-python
   Environment="PATH=/root/iot-security-app-python/venv/bin"
   ExecStart=/root/iot-security-app-python/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start iot-security
   sudo systemctl enable iot-security
   ```

8. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/iot-security
   ```
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   ```bash
   sudo ln -s /etc/nginx/sites-available/iot-security /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

9. **Set Up SSL (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

**Done!** Your app is live with HTTPS! 🔒

---

## 📱 **Mobile App Deployment**

### **Build Production Apps:**

```bash
cd mobile

# Install EAS CLI
npm install -g eas-cli

# Login
eas login

# Configure
eas build:configure

# Build iOS
eas build --platform ios

# Build Android
eas build --platform android
```

### **Submit to Stores:**

**iOS:**
1. Create App Store Connect account ($99/year)
2. Create app listing
3. Upload build via EAS
4. Submit for review

**Android:**
1. Create Google Play Console account ($25 one-time)
2. Create app listing
3. Upload APK/AAB
4. Submit for review

---

## ✅ **Post-Deployment Checklist**

- [ ] Test web app in production
- [ ] Test mobile app with production API
- [ ] Verify email notifications work
- [ ] Check database connection
- [ ] Monitor server logs
- [ ] Set up error tracking (optional)
- [ ] Set up monitoring (optional)

---

## 🎯 **Recommended: Railway**

**Why Railway?**
- ✅ Fastest deployment (5-10 minutes)
- ✅ Automatic HTTPS
- ✅ Easy environment variables
- ✅ Auto-deploy from GitHub
- ✅ Free tier available
- ✅ Scales automatically

**Cost:** $5-20/month for production

---

## 🚀 **You're Ready!**

Choose your deployment method and get your app live!

**Recommended order:**
1. Deploy web app (Railway - 10 min)
2. Test web app
3. Build mobile apps (EAS - 30 min)
4. Test mobile apps
5. Submit to stores (1-2 weeks review)

---

**Good luck with your launch!** 🎊
