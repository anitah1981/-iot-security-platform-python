# 🚀 Build Mobile Apps NOW - Simple Guide

**Skip Expo Go - Build real apps you can install!**

---

## ⚡ **Quick Start (3 Steps)**

### **Step 1: Install EAS CLI**
```bash
cd mobile
npm install -g eas-cli
```

### **Step 2: Login to Expo**
```bash
eas login
```
*(Create free account at https://expo.dev if needed)*

### **Step 3: Build Apps**
```bash
# Build iOS (for iPhone)
eas build --platform ios --profile preview

# Build Android (for Android phones)
eas build --platform android --profile preview
```

**That's it!** EAS will build your apps in the cloud and give you download links.

---

## 📱 **After Building**

### **iOS (iPhone):**
1. Get download link from EAS output
2. Open link on iPhone
3. Install app
4. Trust developer in Settings > General > Device Management (if needed)

### **Android:**
1. Get APK download link from EAS output
2. Download APK on Android phone
3. Enable "Install from Unknown Sources" if needed
4. Install APK

---

## ⚙️ **Update API URL**

**Before building, update your backend URL:**

Edit `mobile/app.json` - change this line:
```json
"apiUrl": "http://localhost:8000"
```

To your actual backend URL:
```json
"apiUrl": "https://your-backend-domain.com"
```

**For local testing:** Use ngrok or deploy backend first.

---

## 🎯 **What You Get**

✅ Real iOS app (installs like normal app)  
✅ Real Android app (APK file)  
✅ No Expo Go needed  
✅ Direct backend connection  
✅ Works offline  

---

## 📝 **Notes**

- **First build:** Takes 10-15 minutes
- **Free tier:** Limited builds per month (usually enough for testing)
- **Credentials:** Expo handles iOS/Android certificates automatically
- **No Mac needed:** EAS builds iOS apps in the cloud!

---

**Ready? Run the commands above!** 🚀
