# 🔥 Critical Fix - Windows Firewall

**Expo Go can't see your server because Windows Firewall is blocking it.**

---

## ✅ **Step-by-Step Firewall Fix**

### **1. Allow Node.js Through Firewall**

1. Press **Win + R**
2. Type: `firewall.cpl`
3. Press **Enter**
4. Click **"Allow an app through firewall"**
5. Click **"Change settings"** (if needed)
6. Find **"Node.js JavaScript Runtime"** in the list
7. Check **both boxes**: ✅ **Private** and ✅ **Public**
8. If Node.js is NOT in the list:
   - Click **"Allow another app..."**
   - Click **"Browse"**
   - Go to: `C:\Program Files\nodejs\`
   - Select **`node.exe`**
   - Click **"Add"**
   - Check **both boxes**: ✅ **Private** and ✅ **Public**
9. Click **OK**

---

### **2. Allow Port 8081**

1. In Windows Firewall, click **"Advanced settings"** (left side)
2. Click **"Inbound Rules"** (left side)
3. Click **"New Rule..."** (right side)
4. Select **"Port"** → Click **Next**
5. Select **"TCP"**
6. Select **"Specific local ports"** and type: `8081`
7. Click **Next**
8. Select **"Allow the connection"** → Click **Next**
9. Check **all three boxes**: ✅ Domain, ✅ Private, ✅ Public
10. Click **Next**
11. Name it: **"Expo Dev Server"**
12. Click **Finish**

---

### **3. Restart Expo**

1. **Stop Expo** (if running): `Ctrl+C`
2. **Start again:**
   ```bash
   npm run start:lan
   ```
3. **Wait 60 seconds** for full startup
4. **In Expo Go**, pull down to refresh the server list
5. **Your server should appear!**

---

## ✅ **Quick Test**

**After firewall fix:**
1. Restart Expo
2. Wait 60 seconds
3. In Expo Go, **pull down** on "Development servers" to refresh
4. Server should appear in the list!

---

## 🎯 **If Still Doesn't Work**

**Temporarily disable firewall to test:**
1. In Windows Firewall, click **"Turn Windows Defender Firewall on or off"**
2. Turn off for **Private networks** (temporarily)
3. Try connecting
4. **Re-enable after testing!**

---

**Firewall is blocking network discovery - fix this first!** 🔥
