# ✅ EXACT STEPS - Copy & Paste These Commands

**You're logged in as `anitah1981`. Follow these exact steps:**

---

## 🎯 **Step-by-Step (Copy Each Command)**

### **Step 1: Open Terminal**
- Press **Ctrl+`** in Cursor
- You should see: `PS C:\IoT-security-app-python>`

---

### **Step 2: Go to Mobile Folder**

**Type this:**

```powershell
cd mobile
```

**Press Enter**

---

### **Step 3: Configure EAS Project** (One-Time Setup)

**Type this:**

```powershell
eas build:configure
```

**Press Enter**

**What happens:**
- It asks: `Would you like to automatically create an EAS project for @anitah1981/iot-security-platform?`
- Type: **`y`**
- Press Enter

**It will:**
- Create the project
- Update app.json automatically
- Say "Project configured successfully"

---

### **Step 4: Build Android App**

**Type this:**

```powershell
eas build --platform android --profile preview
```

**Press Enter**

**What happens:**
- Uploads code (1-2 minutes)
- Builds in cloud (10-15 minutes)
- Shows progress
- Gives download link when done

**You'll see:**
```
✓ Build finished
Download: https://expo.dev/artifacts/...
```

---

### **Step 5: Build iOS App** (After Android Finishes)

**Type this:**

```powershell
eas build --platform ios --profile preview
```

**Press Enter**

**Same process** - 10-15 minutes

---

## 📋 **Complete Command List** (Copy All)

```powershell
cd mobile
eas build:configure
# (Type 'y' when asked)
eas build --platform android --profile preview
eas build --platform ios --profile preview
```

---

## ⚠️ **Before Starting - Make Sure:**

1. ✅ **Backend running:** `python -m uvicorn main:app --reload --port 8000`
2. ✅ **ngrok running:** `ngrok http 8000`
3. ✅ **Logged in:** You are (`anitah1981`)

---

## 🎯 **That's It!**

**Just run the 3 commands above in order.**

**Total time:** ~30 minutes (mostly waiting)

---

**Start now: Open terminal and run `cd mobile` then `eas build:configure`**
