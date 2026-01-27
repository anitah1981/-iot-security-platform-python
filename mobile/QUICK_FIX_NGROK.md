# ⚡ Quick Fix - Ngrok Error

**Error with tunnel mode? Use LAN mode instead!**

---

## 🚀 **Quick Fix (30 seconds)**

### **1. Stop Expo** (if running):
Press `Ctrl+C`

### **2. Start with LAN mode:**
```bash
npm run start:lan
```

**Or:**
```bash
npm start -- --lan
```

### **3. Get your IP address:**
Open new terminal and run:
```cmd
ipconfig
```

Look for **IPv4 Address** (e.g., `192.168.1.100`)

### **4. In Expo Go:**
1. Open Expo Go app
2. Tap **"Enter URL manually"** (at bottom)
3. Type: `exp://YOUR_IP:8081`
   - Example: `exp://192.168.1.100:8081`
4. Tap **"Connect"**

**Done!** ✅

---

## ✅ **Why This Works**

**LAN mode:**
- ✅ Uses your local network
- ✅ No ngrok needed
- ✅ Works if phone/computer on same WiFi
- ✅ Simpler than tunnel mode

---

## ⚠️ **Requirements**

- iPhone and computer must be on **same WiFi network**
- Windows Firewall may need to allow Node.js (or temporarily disable)

---

## 🔧 **If Still Doesn't Work**

### **Check Same Network:**
- iPhone: Settings → WiFi → Check network name
- Computer: Should be on same network

### **Check Firewall:**
- Windows Defender → Allow app through firewall
- Add Node.js or allow port 8081

### **Try Different IP:**
- Some networks use different IP ranges
- Try `192.168.0.x` or `192.168.1.x` or `10.0.0.x`

---

## ✅ **You're Ready!**

1. Run: `npm run start:lan`
2. Get IP: `ipconfig`
3. Enter URL in Expo Go: `exp://YOUR_IP:8081`
4. Test your app!

---

**LAN mode = No ngrok needed!** 📱✅
