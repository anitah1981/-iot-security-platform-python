# 🔧 Fix Expo Go Not Detecting Server

**Problem:** Expo Go shows empty "Development servers" list - can't find your server.

**Solution:** Force Expo to broadcast properly and allow firewall access.

---

## ✅ **Solution 1: Fix Windows Firewall (Most Important)**

### **Step 1: Allow Node.js Through Firewall**
1. Open **Windows Defender Firewall**
2. Click **"Allow an app through firewall"**
3. Find **"Node.js JavaScript Runtime"**
4. Check both **"Private"** and **"Public"** boxes
5. If not listed:
   - Click **"Allow another app"**
   - Click **"Browse"**
   - Navigate to: `C:\Program Files\nodejs\node.exe`
   - Click **"Add"**
   - Check both **"Private"** and **"Public"**
6. Click **OK**

### **Step 2: Allow Port 8081**
1. In Windows Firewall, click **"Advanced settings"**
2. Click **"Inbound Rules"** → **"New Rule"**
3. Select **"Port"** → **Next**
4. Select **"TCP"** and enter **8081** → **Next**
5. Select **"Allow the connection"** → **Next**
6. Check all profiles → **Next**
7. Name it: **"Expo Dev Server"** → **Finish**

---

## ✅ **Solution 2: Restart Expo with Proper Settings**

### **Stop Expo** (Ctrl+C), then:

```bash
npm run start:lan
```

### **Wait 30-60 seconds** for full startup and network discovery

### **Then check Expo Go:**
- Pull down to refresh the "Development servers" list
- Your server should appear

---

## ✅ **Solution 3: Use Manual Connection (If Discovery Still Fails)**

### **In Expo Go:**
1. Tap **"Diagnostics"** tab (bottom)
2. Look for connection options
3. Or try tapping the **"HELP"** link next to "Development servers"

### **Alternative: Use QR Code Method**
1. Make sure Expo is running
2. In terminal, look for the QR code
3. Use iPhone **Camera app** (not Expo Go)
4. Scan the QR code
5. Tap notification to open in Expo Go

---

## ✅ **Solution 4: Check Network Discovery**

### **On Windows:**
1. Open **Network and Sharing Center**
2. Click **"Change advanced sharing settings"**
3. Under **"Private"** profile:
   - Turn on **"Network discovery"**
   - Turn on **"File and printer sharing"**
4. Click **"Save changes"**

---

## ✅ **Solution 5: Try Different Network**

### **If on WiFi:**
- Some networks block device-to-device communication
- Try a mobile hotspot or different WiFi network
- Or connect both devices to same mobile hotspot

---

## 🎯 **Most Likely Fix**

**Windows Firewall is blocking network discovery.**

**Do this:**
1. Allow Node.js through firewall (both Private and Public)
2. Allow port 8081 through firewall
3. Restart Expo: `npm run start:lan`
4. Wait 60 seconds
5. In Expo Go, pull down to refresh
6. Server should appear in list

---

## ✅ **Quick Test**

**After fixing firewall:**
1. Restart Expo: `npm run start:lan`
2. Wait 60 seconds
3. In Expo Go, **pull down** on the "Development servers" section to refresh
4. Your server should appear!

---

**Try the firewall fix first - that's usually the issue!** 🔧
