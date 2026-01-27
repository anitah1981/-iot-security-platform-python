# 🚀 Build Mobile Apps - Complete Guide

**Skip Expo Go - Build real apps you can install directly!**

---

## ✅ **What We're Doing**

Building **real iOS and Android apps** that:
- ✅ Install like normal apps (no Expo Go needed)
- ✅ Connect directly to your backend
- ✅ Work offline
- ✅ Can be submitted to App Store / Play Store

---

## 🚀 **Step 1: Install EAS CLI**

```bash
cd mobile
npm install -g eas-cli
```

---

## 🚀 **Step 2: Login to Expo**

```bash
eas login
```

**If you don't have an account:**
- Go to: https://expo.dev
- Sign up (free)
- Then run `eas login`

---

## 🚀 **Step 3: Configure Project**

```bash
eas build:configure
```

**Accept defaults** when prompted.

---

## 🚀 **Step 4: Update API URL**

**Before building, update your backend URL:**

Edit `mobile/app.json`:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://your-backend-url.com"
    }
  }
}
```

**For local testing:** Use ngrok or deploy backend first.

---

## 🚀 **Step 5: Build iOS App**

```bash
eas build --platform ios --profile preview
```

**This will:**
- Upload your code to Expo servers
- Build in the cloud (takes 10-15 minutes)
- Give you a download link

**When prompted:**
- Choose **"Expo managed workflow"**
- Choose **"Let Expo handle credentials"** (easiest)

---

## 🚀 **Step 6: Build Android App**

```bash
eas build --platform android --profile preview
```

**Same process** - builds in cloud, gives download link.

---

## 📱 **Step 7: Install on Your iPhone**

### **Option A: Direct Install**
1. **Get download link** from EAS build output
2. **Open link on iPhone**
3. **Install** (may need to trust developer in Settings)

### **Option B: TestFlight**
1. **EAS will guide you** through TestFlight setup
2. **Install TestFlight** app
3. **Install your app** from TestFlight

---

## ✅ **What You Get**

- ✅ **Real iOS app** installed on iPhone
- ✅ **Real Android app** (APK file)
- ✅ **No Expo Go needed**
- ✅ **Direct backend connection**
- ✅ **Ready for App Store submission**

---

## 🎯 **Quick Commands**

```bash
# Install EAS
npm install -g eas-cli

# Login
eas login

# Configure
eas build:configure

# Build iOS
eas build --platform ios --profile preview

# Build Android
eas build --platform android --profile preview
```

---

## 📝 **Important Notes**

1. **Backend URL:** Make sure `apiUrl` in `app.json` points to your deployed backend
2. **First build:** Takes 10-15 minutes (subsequent builds are faster)
3. **Free tier:** Expo gives free builds (limited per month)
4. **Credentials:** Expo can manage iOS/Android credentials for you

---

## 🎊 **You're Ready!**

**Run the commands above and you'll have real mobile apps!**

**No more Expo Go connection issues!** 🚀📱
