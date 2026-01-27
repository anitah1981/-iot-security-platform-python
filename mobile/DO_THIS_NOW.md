# 🚀 DO THIS NOW - Exact Steps

**Follow these steps in order:**

---

## ✅ **Step 1: Open Terminal in Cursor**

1. Press **Ctrl+`** (Ctrl + backtick) to open terminal
2. You should see: `PS C:\IoT-security-app-python>`

---

## ✅ **Step 2: Login to Expo**

**Type exactly:**

```powershell
cd mobile
eas login
```

**Press Enter**

**What happens:**
- It asks: `Email or username:`
- Type your Expo email
- Press Enter
- It asks: `Password:`
- Type your password (won't show on screen - that's normal)
- Press Enter

**Success looks like:**
```
✓ Successfully logged in as your-email@example.com
```

---

## ✅ **Step 3: Verify Login**

**Type:**

```powershell
eas whoami
```

**Press Enter**

**Should show:** Your Expo username/email

---

## ✅ **Step 4: Build Android App**

**Type:**

```powershell
eas build --platform android --profile preview
```

**Press Enter**

**What happens:**
- Uploads your code (takes 1-2 minutes)
- Builds in cloud (takes 10-15 minutes)
- Shows progress
- Gives you download link when done

**You'll see something like:**
```
Build finished
Download: https://expo.dev/artifacts/...
```

---

## ✅ **Step 5: Build iOS App**

**After Android finishes, type:**

```powershell
eas build --platform ios --profile preview
```

**Press Enter**

**Same process** - takes 10-15 minutes

---

## ✅ **Step 6: Install on Your Phone**

### **Android:**
1. Copy the download link from terminal
2. Open on Android phone
3. Download APK
4. Install (allow unknown sources if asked)

### **iOS:**
1. Copy the download link from terminal
2. Open on iPhone
3. Follow TestFlight instructions
4. Trust developer in Settings if needed

---

## ⚠️ **Before Building - Make Sure:**

1. **Backend is running** (in another terminal):
   ```powershell
   python -m uvicorn main:app --reload --port 8000
   ```

2. **ngrok is running** (in another PowerShell window):
   ```powershell
   ngrok http 8000
   ```

3. **app.json has correct ngrok URL** ✅ (Already done!)

---

## 🎯 **Quick Copy-Paste Commands**

**Run these in order:**

```powershell
# 1. Go to mobile folder
cd c:\IoT-security-app-python\mobile

# 2. Login
eas login

# 3. Build Android
eas build --platform android --profile preview

# 4. Build iOS (after Android finishes)
eas build --platform ios --profile preview
```

---

## 📝 **What Each Step Does**

- **Step 1:** Opens terminal
- **Step 2:** Authenticates with Expo (required)
- **Step 3:** Confirms login worked
- **Step 4:** Builds Android app (10-15 min)
- **Step 5:** Builds iOS app (10-15 min)
- **Step 6:** Install apps on your phone

---

## ✅ **That's It!**

**Just run the commands above in order.**

**Total time:** ~30 minutes (mostly waiting for builds)

---

**Start with Step 1: Open terminal and run `cd mobile` then `eas login`**
