# 📱 iPhone Testing on Windows - Quick Guide

**How to test your mobile app on iPhone when developing on Windows**

---

## ⚡ **Quick Start (Recommended)**

### **Use Tunnel Mode:**
```bash
cd mobile
npm start -- --tunnel
```

**Why tunnel mode?**
- ✅ Works across different networks
- ✅ Bypasses Windows Firewall
- ✅ Most reliable for Windows + iPhone
- ✅ QR code works perfectly

---

## 📱 **Steps:**

1. **Install Expo Go on iPhone:**
   - App Store: https://apps.apple.com/app/expo-go/id982107779

2. **Start Expo with tunnel:**
   ```bash
   cd mobile
   npm start -- --tunnel
   ```

3. **Scan QR code:**
   - Open **iPhone Camera app**
   - Point at QR code in terminal
   - Tap notification that appears
   - Opens in Expo Go

4. **If QR code doesn't work:**
   - Open **Expo Go app**
   - Tap "Enter URL manually"
   - Copy URL from terminal (looks like: `exp://xxx-xxx.anonymous.exp.direct:80`)
   - Paste and connect

---

## 🔧 **Alternative: Manual URL**

If QR code still doesn't work:

1. **Get URL from terminal:**
   - Look for line like: `exp://192.168.1.100:8081`
   - Or tunnel URL: `exp://xxx-xxx.anonymous.exp.direct:80`

2. **In Expo Go:**
   - Open app
   - Tap "Enter URL manually"
   - Type the URL
   - Connect

---

## ⚠️ **Common Issues**

### **"Can't connect"**
- **Solution:** Use tunnel mode (`--tunnel` flag)
- **Why:** Windows Firewall often blocks local network connections

### **"Network request failed"**
- **Solution:** Make sure you're using tunnel mode
- **Check:** Internet connection is working

### **"Expo Go can't find project"**
- **Solution:** Copy URL manually from terminal
- **Check:** Metro bundler is still running

---

## 🎯 **Best Practice**

**Always use tunnel mode on Windows:**
```bash
npm start -- --tunnel
```

This is the most reliable method for Windows + iPhone!

---

## ✅ **You're Ready!**

1. Run: `npm start -- --tunnel`
2. Scan QR code with iPhone Camera
3. Test your app!

---

**Tunnel mode = No more connection issues!** 📱✅
