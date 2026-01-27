# ⚡ QUICK BUILD GUIDE - Mobile Apps

**Build iOS and Android apps in 5 minutes - No Expo Go needed!**

---

## 🚀 **Step-by-Step**

### **1. Open Terminal/PowerShell**
```bash
cd mobile
```

### **2. Install EAS CLI** (one-time)
```bash
npm install -g eas-cli
```

### **3. Login to Expo** (one-time)
```bash
eas login
```
*(Create free account at https://expo.dev if needed)*

### **4. Configure Project** (one-time)
```bash
eas build:configure
```
*(Press Enter to accept all defaults)*

### **5. Update API URL**
**IMPORTANT:** Edit `mobile/app.json` and change:
```json
"apiUrl": "http://localhost:8000"
```
To your actual backend URL:
- **If deployed:** `"https://your-backend.com"`
- **If local:** Use ngrok (see UPDATE_API_URL.md)

### **6. Build iOS App**
```bash
eas build --platform ios --profile preview
```

### **7. Build Android App**
```bash
eas build --platform android --profile preview
```

---

## ⏱️ **What Happens**

1. **EAS uploads your code** to cloud
2. **Builds in cloud** (10-15 minutes)
3. **Gives you download link** when done
4. **Install on your phone** from the link!

---

## 📱 **Installing**

### **iPhone:**
1. Open download link on iPhone
2. Tap "Install"
3. Go to Settings > General > Device Management
4. Trust developer certificate
5. Done!

### **Android:**
1. Download APK from link
2. Enable "Install from Unknown Sources"
3. Tap APK to install
4. Done!

---

## 🎯 **Or Use Build Script**

**Windows:**
```bash
cd mobile
.\build-apps.ps1
```

**Or:**
```bash
cd mobile
build-apps.bat
```

---

## ✅ **That's It!**

**No Expo Go needed - you'll have real apps!** 🚀

**See START_BUILDING.md for detailed guide**
