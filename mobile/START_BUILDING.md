# 🚀 START BUILDING MOBILE APPS NOW

**Complete guide to build iOS and Android apps without Expo Go**

---

## ⚡ **Quick Start (5 Minutes)**

### **1. Install EAS CLI**
```bash
cd mobile
npm install -g eas-cli
```

### **2. Login to Expo**
```bash
eas login
```
*(Sign up at https://expo.dev if needed - it's free!)*

### **3. Configure Project**
```bash
eas build:configure
```
*(Accept all defaults)*

### **4. Update API URL**
Edit `mobile/app.json` - change:
```json
"apiUrl": "http://localhost:8000"
```
To your backend URL (see UPDATE_API_URL.md for options)

### **5. Build Apps**
```bash
# Build iOS
eas build --platform ios --profile preview

# Build Android  
eas build --platform android --profile preview
```

**Done!** You'll get download links in 10-15 minutes.

---

## 🎯 **What You Get**

✅ **Real iOS app** - installs like any iPhone app  
✅ **Real Android app** - APK file you can install  
✅ **No Expo Go needed** - works independently  
✅ **Direct backend connection** - connects to your API  
✅ **Offline support** - works without internet  

---

## 📱 **Installing Built Apps**

### **iOS (iPhone):**
1. Get download link from EAS build output
2. Open link on iPhone (Safari)
3. Tap "Install"
4. Go to Settings > General > Device Management
5. Trust the developer certificate
6. App installs!

### **Android:**
1. Get APK download link from EAS build output
2. Download APK on Android phone
3. Enable "Install from Unknown Sources" (Settings > Security)
4. Tap APK file to install
5. App installs!

---

## 🔧 **Using Build Scripts**

**Windows (PowerShell):**
```powershell
cd mobile
.\build-apps.ps1
```

**Windows (Command Prompt):**
```cmd
cd mobile
build-apps.bat
```

**Mac/Linux:**
```bash
cd mobile
npm install -g eas-cli
eas login
eas build:configure
eas build --platform ios --profile preview
eas build --platform android --profile preview
```

---

## ⚙️ **API URL Options**

### **Option 1: Deployed Backend**
If your backend is live:
```json
"apiUrl": "https://your-backend.com"
```

### **Option 2: ngrok (Local Testing)**
1. Install ngrok: `choco install ngrok` (Windows)
2. Start tunnel: `ngrok http 8000`
3. Copy HTTPS URL
4. Update app.json with that URL

### **Option 3: Production**
```json
"apiUrl": "https://api.iot-security-platform.com"
```

**See UPDATE_API_URL.md for detailed instructions**

---

## 📝 **Important Notes**

- ⏱️ **First build:** Takes 10-15 minutes (cloud build)
- 💰 **Free tier:** Limited builds per month (usually enough)
- 🔐 **Credentials:** Expo handles iOS/Android certificates automatically
- 🖥️ **No Mac needed:** EAS builds iOS apps in the cloud!
- 🌐 **Backend must be accessible:** Can't use localhost - use ngrok or deploy

---

## 🐛 **Troubleshooting**

### **"EAS CLI not found"**
```bash
npm install -g eas-cli
```

### **"Not logged in"**
```bash
eas login
```

### **"Build failed"**
- Check API URL is correct in app.json
- Make sure backend is accessible
- Check EAS dashboard for error details

### **"Can't install on iPhone"**
- Trust developer certificate: Settings > General > Device Management
- Make sure you downloaded from HTTPS link

---

## ✅ **Checklist Before Building**

- [ ] EAS CLI installed (`eas --version`)
- [ ] Logged into Expo (`eas whoami`)
- [ ] Project configured (`eas.json` exists)
- [ ] API URL updated in `app.json`
- [ ] Backend is accessible (test in browser)
- [ ] Ready to wait 10-15 minutes for build

---

## 🎊 **You're Ready!**

**Run these commands:**
```bash
cd mobile
npm install -g eas-cli
eas login
eas build:configure
# Update app.json API URL
eas build --platform ios --profile preview
eas build --platform android --profile preview
```

**Or use the build script:**
```bash
cd mobile
.\build-apps.ps1
```

---

**No more Expo Go issues - you'll have real apps!** 🚀📱
