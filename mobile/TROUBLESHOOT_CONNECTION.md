# 🔧 Troubleshoot iPhone Connection

**If Safari method doesn't work, try these:**

---

## ✅ **Step 1: Check Windows Firewall**

### **Allow Node.js through Firewall:**
1. Open **Windows Defender Firewall**
2. Click **"Allow an app through firewall"**
3. Find **"Node.js"** in the list
4. Check both **"Private"** and **"Public"**
5. If Node.js isn't listed:
   - Click **"Allow another app"**
   - Browse to: `C:\Program Files\nodejs\node.exe`
   - Add it and check both boxes
6. Click **OK**

### **Or Temporarily Disable Firewall (for testing):**
1. Open **Windows Defender Firewall**
2. Click **"Turn Windows Defender Firewall on or off"**
3. Turn off for **Private networks** (temporarily)
4. Try connecting again
5. **Re-enable after testing!**

---

## ✅ **Step 2: Verify Same Network**

### **Check Computer IP:**
```cmd
ipconfig
```
Note your IPv4 address (e.g., `192.168.0.235`)

### **Check iPhone IP:**
1. iPhone: **Settings** → **WiFi**
2. Tap the ⓘ icon next to your network
3. Check **IP Address**
4. Should be same network (e.g., `192.168.0.x`)

**If different networks:** Connect both to same WiFi

---

## ✅ **Step 3: Test Server Accessibility**

### **On iPhone, try in Safari:**
```
http://192.168.0.235:8081
```

**If this doesn't load:** Server isn't accessible (firewall/network issue)

**If this loads:** Server is accessible, try `exp://` URL again

---

## ✅ **Step 4: Try Different Port**

### **Stop Expo, then:**
```bash
expo start --lan --port 19000
```

### **Then in Safari:**
```
exp://192.168.0.235:19000
```

---

## ✅ **Step 5: Use Expo Go's Recent Projects**

1. **Open Expo Go app**
2. **Check "Recent" or "History"** tab
3. **If your project appears**, tap it
4. **Might reconnect automatically**

---

## ✅ **Step 6: Check Expo is Actually Running**

### **In terminal, you should see:**
- `Metro waiting on...`
- QR code displayed
- No error messages

**If errors:** Check terminal output

---

## ✅ **Step 7: Restart Everything**

1. **Stop Expo:** `Ctrl+C`
2. **Close Expo Go app** on iPhone
3. **Restart Expo:**
   ```bash
   npm run start:lan
   ```
4. **Wait 30 seconds** for full startup
5. **Try Safari again:** `exp://192.168.0.235:8081`

---

## 🔍 **Common Issues**

### **"Can't connect"**
- ✅ Check Windows Firewall
- ✅ Verify same WiFi network
- ✅ Try `http://` instead of `exp://`

### **"Network request failed"**
- ✅ Server might not be listening on network IP
- ✅ Try different port
- ✅ Check firewall settings

### **"Expo Go can't find project"**
- ✅ Make sure Expo is running
- ✅ Check IP address is correct
- ✅ Try restarting Expo

---

## 🎯 **Most Likely Fix**

**Windows Firewall is blocking the connection.**

**Try this:**
1. Temporarily disable Windows Firewall
2. Try connecting again
3. If it works, re-enable firewall and add Node.js exception

---

**Let me know what error you see and we'll fix it!** 🔧
