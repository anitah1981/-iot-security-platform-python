# 🚀 Deployment Guide - Quick Reference

**Get your IoT Security Platform live in minutes!**

---

## ⚡ **Fastest: Railway (10 minutes)**

1. **Sign up:** https://railway.app (GitHub login)
2. **New Project** → **Deploy from GitHub**
3. **Select your repo**
4. **Add environment variables** (see below)
5. **Done!** Your app is live at `https://your-app.railway.app`

### **Required Environment Variables:**
```
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/iot_security
JWT_SECRET=your-32-character-secret-key-here
PORT=8000
CORS_ORIGINS=https://your-app.railway.app
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
FROM_EMAIL=your-email@gmail.com
```

---

## 🐳 **Docker (5 minutes)**

```bash
# 1. Configure
cp .env.example .env
# Edit .env

# 2. Deploy
docker compose up -d

# 3. Access
# http://localhost:8000
```

---

## 📱 **Mobile App**

### **Update API URL:**
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

### **Build:**
```bash
cd mobile
npm install
npm start  # For testing
eas build --platform ios  # For production
eas build --platform android  # For production
```

---

## ✅ **Quick Test**

### **Web:**
```bash
python -m uvicorn main:app --reload --port 8000
# Open: http://localhost:8000
```

### **Mobile:**
```bash
cd mobile
npm start
# Scan QR code with Expo Go
```

---

## 📚 **Full Guides**

- `DEPLOY_NOW.md` - Step-by-step Railway deployment
- `TEST_AND_DEPLOY.md` - Complete testing & deployment
- `DEPLOYMENT_QUICK_START.md` - All deployment options
- `FINAL_DEPLOYMENT_CHECKLIST.md` - Pre-launch checklist

---

**Ready to deploy!** 🚀
