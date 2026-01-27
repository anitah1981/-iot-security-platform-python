# ⚡ EAS Build - Step by Step

**Build your mobile apps in 5 commands:**

---

## 🚀 **Commands to Run**

### **1. Install EAS CLI**
```bash
npm install -g eas-cli
```

### **2. Login**
```bash
eas login
```
(Create account at https://expo.dev if needed)

### **3. Configure**
```bash
eas build:configure
```
(Press Enter to accept defaults)

### **4. Build iOS**
```bash
eas build --platform ios --profile preview
```

### **5. Build Android**
```bash
eas build --platform android --profile preview
```

---

## ✅ **That's It!**

**EAS will:**
- Upload your code
- Build in the cloud
- Give you download links
- Guide you through installation

---

## 📱 **After Build**

**For iOS:**
- Get download link from EAS
- Open on iPhone
- Install (trust developer if needed)

**For Android:**
- Download APK file
- Install on Android device

---

## 🎯 **Update Backend URL**

**Before building, edit `app.json`:**
```json
"extra": {
  "apiUrl": "https://your-backend-url.com"
}
```

---

**Run these commands and you'll have real apps!** 🚀
