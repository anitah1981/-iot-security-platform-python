# ⚡ Quick Firewall Fix - Run This!

**I've created a script to automatically fix the firewall!**

---

## 🚀 **Step 1: Run the Firewall Fix Script**

### **Option A: Use the Batch File (Easiest)**
1. **Right-click** on `RUN_FIREWALL_FIX.bat`
2. Select **"Run as Administrator"**
3. Click **"Yes"** when Windows asks for permission
4. Wait for it to complete

### **Option B: Use PowerShell**
1. **Right-click** on **PowerShell** (Start menu)
2. Select **"Run as Administrator"**
3. Navigate to mobile folder:
   ```powershell
   cd C:\IoT-security-app-python\mobile
   ```
4. Run the script:
   ```powershell
   .\fix-firewall.ps1
   ```

---

## ✅ **Step 2: Restart Expo**

After the firewall fix completes:

1. **Stop Expo** (if running): `Ctrl+C`
2. **Start again:**
   ```bash
   npm run start:lan
   ```
3. **Wait 60 seconds** for full startup

---

## ✅ **Step 3: Check Expo Go**

1. **Open Expo Go** on iPhone
2. **Pull down** on the "Development servers" section to refresh
3. **Your server should appear!**

---

## 🎯 **What the Script Does**

- ✅ Allows Node.js through firewall (Private & Public)
- ✅ Allows port 8081 through firewall
- ✅ Enables network discovery

---

## ⚠️ **If Script Doesn't Work**

**Manually configure firewall:**
- See `FIREWALL_FIX.md` for step-by-step instructions

---

**Run the script as Administrator, then restart Expo!** 🔥
