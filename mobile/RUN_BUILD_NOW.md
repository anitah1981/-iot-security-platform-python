# 🚀 RUN BUILD NOW - Step by Step

**Complete guide to build your mobile apps right now!**

---

## ✅ **Current Status**

- ✅ EAS CLI installed
- ✅ Project configured (`eas.json` exists)
- ✅ Dependencies installed
- ⚠️ Need to login to Expo
- ⚠️ Need to update API URL

---

## 🎯 **Quick Steps (5 minutes)**

### **Step 1: Login to Expo** (2 minutes)

Open PowerShell/Terminal and run:

```bash
cd mobile
eas login
```

**If you don't have an Expo account:**
1. Go to: https://expo.dev
2. Click "Sign Up" (free)
3. Create account with email or GitHub
4. Then run `eas login`

---

### **Step 2: Update API URL** (1 minute)

**Option A: Using ngrok (for local testing)**

1. **Install ngrok** (if not installed):
   ```bash
   choco install ngrok
   ```

2. **Start your backend** (in another terminal):
   ```bash
   cd ..
   python -m uvicorn main:app --reload --port 8000
   ```

3. **Start ngrok** (in another terminal):
   ```bash
   ngrok http 8000
   ```

4. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

5. **Update app.json:**
   Edit `mobile/app.json` and change:
   ```json
   "apiUrl": "http://localhost:8000"
   ```
   To:
   ```json
   "apiUrl": "https://abc123.ngrok.io"
   ```
   (Use your actual ngrok URL)

**Option B: Using deployed backend**

If your backend is deployed (Railway, Heroku, etc.):
Edit `mobile/app.json` and change to your backend URL:
```json
"apiUrl": "https://your-backend.railway.app"
```

---

### **Step 3: Build Apps** (10-15 minutes)

**Option 1: Use build script**
```bash
cd mobile
.\build-apps.ps1
```

**Option 2: Manual commands**
```bash
cd mobile

# Build iOS
eas build --platform ios --profile preview

# Build Android
eas build --platform android --profile preview
```

---

## 📱 **After Building**

### **iOS:**
1. Get download link from EAS output
2. Open link on iPhone
3. Install app
4. Trust developer: Settings > General > Device Management

### **Android:**
1. Get APK download link from EAS output
2. Download on Android phone
3. Enable "Install from Unknown Sources"
4. Install APK

---

## ⚡ **One-Command Option**

Run the complete setup script:
```bash
cd mobile
.\setup-and-build.ps1
```

This will guide you through everything!

---

## ✅ **Checklist**

- [ ] Logged into Expo (`eas login`)
- [ ] API URL updated in `app.json`
- [ ] Backend is running (if using localhost)
- [ ] ngrok running (if using localhost)
- [ ] Ready to wait 10-15 minutes for build

---

## 🎊 **Ready!**

**Run these commands:**
```bash
cd mobile
eas login                    # Login to Expo
# Update app.json API URL
.\build-apps.ps1            # Build apps
```

**Or use the complete script:**
```bash
cd mobile
.\setup-and-build.ps1
```

---

**You'll have real mobile apps in 15 minutes!** 🚀📱
