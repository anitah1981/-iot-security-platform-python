# ✅ FINAL BUILD STEPS - Almost There!

**Your app.json is configured correctly! Just need to complete login and build.**

---

## ✅ **What's Already Done**

- ✅ EAS CLI installed
- ✅ Project configured (`eas.json` ready)
- ✅ Dependencies installed
- ✅ **app.json updated** with ngrok URL: `https://nonspectrally-unindignant-alivia.ngrok-free.dev`
- ✅ Backend running on port 8000

---

## 🚀 **Final 2 Steps (Interactive)**

### **Step 1: Login to Expo** (30 seconds)

**In Cursor terminal, run:**

```powershell
cd c:\IoT-security-app-python\mobile
eas login
```

**Enter your Expo credentials** when prompted.

**Verify login worked:**
```powershell
eas whoami
```
(Should show your username)

---

### **Step 2: Build Apps** (10-15 minutes)

**After logging in, run:**

```powershell
.\complete-build.ps1
```

**Or manually:**

```powershell
# Build Android
eas build --platform android --profile preview

# Build iOS  
eas build --platform ios --profile preview
```

---

## 📱 **After Build**

You'll get download links in the terminal:
- **Android:** APK download link
- **iOS:** TestFlight or direct install link

---

## ⚠️ **Important Notes**

1. **Make sure ngrok is running** with port 8000:
   ```powershell
   ngrok http 8000
   ```

2. **Make sure backend is running**:
   ```powershell
   python -m uvicorn main:app --reload --port 8000
   ```

3. **If ngrok URL changes**, update `app.json` with the new URL

---

## 🎯 **Quick Commands**

```powershell
# 1. Login
cd c:\IoT-security-app-python\mobile
eas login

# 2. Build
.\complete-build.ps1
```

---

**You're 99% done! Just login and build!** 🚀
