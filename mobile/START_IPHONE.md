# 📱 Start Mobile App for iPhone - Quick Guide

**Easiest way to get your app running on iPhone**

---

## ⚡ **Option 1: Use Helper Script (Easiest)**

### **In PowerShell:**
```powershell
.\get-ip.ps1
```

This will:
- ✅ Get your IP address automatically
- ✅ Show you the exact URL to enter
- ✅ Start Expo in LAN mode

### **Then in Expo Go:**
1. Open Expo Go app
2. Tap "Enter URL manually"
3. Copy the URL shown in terminal (e.g., `exp://192.168.1.100:8081`)
4. Paste and connect

---

## ⚡ **Option 2: Manual Start**

### **Step 1: Start Expo**
```bash
npm run start:lan
```

### **Step 2: Get IP**
Open new terminal:
```cmd
ipconfig
```
Look for **IPv4 Address** (e.g., `192.168.1.100`)

### **Step 3: Connect**
In Expo Go:
- Tap "Enter URL manually"
- Type: `exp://YOUR_IP:8081`
- Connect

---

## ✅ **Requirements**

- iPhone and computer on **same WiFi network**
- Windows Firewall may need to allow Node.js

---

## 🔧 **If Connection Fails**

1. **Check same WiFi:**
   - iPhone: Settings → WiFi
   - Computer: Should be on same network

2. **Check Firewall:**
   - Windows Defender → Allow Node.js through firewall

3. **Try different IP:**
   - Some networks use `192.168.0.x` or `10.0.0.x`
   - Check all IPv4 addresses from `ipconfig`

---

## 🚀 **Quick Start**

**Just run:**
```powershell
.\get-ip.ps1
```

**Then follow the instructions shown!** ✅

---

**That's it!** 📱
