# 🔧 Fix Ngrok Tunnel Error on Windows

**Error: `TypeError [ERR_INVALID_ARG_TYPE]: The "file" argument must be of type string. Received null`**

This is a common ngrok installation issue on Windows.

---

## ✅ **Solution 1: Install Ngrok Manually (Recommended)**

### **Step 1: Download Ngrok**
1. Go to: https://ngrok.com/download
2. Download Windows version
3. Extract to a folder (e.g., `C:\ngrok`)

### **Step 2: Add to PATH**
1. **Open System Properties:**
   - Press `Win + R`
   - Type: `sysdm.cpl`
   - Press Enter

2. **Environment Variables:**
   - Click "Environment Variables"
   - Under "System variables", find "Path"
   - Click "Edit"
   - Click "New"
   - Add: `C:\ngrok` (or wherever you extracted it)
   - Click "OK" on all dialogs

3. **Restart Terminal:**
   - Close and reopen your terminal/PowerShell

### **Step 3: Verify Installation**
```bash
ngrok version
```

Should show version number.

### **Step 4: Try Tunnel Again**
```bash
cd mobile
npm run start:tunnel
```

---

## ✅ **Solution 2: Use LAN Mode Instead**

**If ngrok is too complicated, use LAN mode:**

```bash
cd mobile
npm start -- --lan
```

**Then:**
1. Get your computer's IP address:
   ```cmd
   ipconfig
   ```
   Look for IPv4 Address (e.g., `192.168.1.100`)

2. In Expo Go:
   - Tap "Enter URL manually"
   - Type: `exp://192.168.1.100:8081` (use your IP)
   - Connect

**Note:** Make sure iPhone and computer are on same WiFi network.

---

## ✅ **Solution 3: Use Expo Development Build (Alternative)**

If tunnel doesn't work, you can use Expo's development build:

```bash
cd mobile
npx expo start --dev-client
```

This uses Expo's cloud service instead of ngrok.

---

## ✅ **Solution 4: Fix Ngrok Installation**

### **Uninstall and Reinstall:**
```bash
npm uninstall -g @expo/ngrok
npm install -g @expo/ngrok@^4.1.0
```

### **Or use npx (no global install):**
```bash
cd mobile
npx expo start --tunnel
```

This uses ngrok without global installation.

---

## 🎯 **Recommended: Use LAN Mode**

**For Windows + iPhone, LAN mode is often easier:**

```bash
cd mobile
npm start -- --lan
```

**Then manually enter URL in Expo Go:**
- Get IP: `ipconfig` (look for IPv4)
- In Expo Go: `exp://YOUR_IP:8081`

---

## ✅ **Quick Fix Right Now**

**Try LAN mode first (easiest):**

1. **Stop Expo** (if running): `Ctrl+C`

2. **Start with LAN:**
   ```bash
   npm start -- --lan
   ```

3. **Get your IP:**
   ```cmd
   ipconfig
   ```
   Copy IPv4 address (e.g., `192.168.1.100`)

4. **In Expo Go:**
   - Tap "Enter URL manually"
   - Type: `exp://YOUR_IP:8081`
   - Connect

**This should work!** ✅

---

## 📝 **If LAN Mode Doesn't Work**

1. **Check same WiFi:**
   - iPhone and computer must be on same network

2. **Check Windows Firewall:**
   - Allow Node.js through firewall
   - Or temporarily disable for testing

3. **Try manual IP:**
   - Make sure IP address is correct
   - Try both `exp://` and `http://` protocols

---

**LAN mode is usually easier than fixing ngrok!** 📱✅
