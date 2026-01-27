# 🔧 Fix iPhone Connection - Windows

**Quick fix for QR code not working with iPhone on Windows**

---

## ⚡ **Quick Fix (30 seconds)**

### **Stop current Expo** (if running):
Press `Ctrl+C` in your terminal

### **Start with tunnel mode:**
```bash
npm run start:tunnel
```

**Or:**
```bash
npm start -- --tunnel
```

### **Scan QR code:**
1. Open **iPhone Camera app**
2. Point at QR code in terminal
3. Tap notification
4. Opens in Expo Go!

---

## ✅ **Why This Works**

**Tunnel mode:**
- ✅ Creates a public URL through Expo servers
- ✅ Bypasses Windows Firewall
- ✅ Works even if phone/computer on different networks
- ✅ Most reliable for Windows + iPhone

---

## 📱 **If QR Code Still Doesn't Work**

### **Manual URL Entry:**

1. **Get URL from terminal:**
   - Look for: `exp://xxx-xxx.anonymous.exp.direct:80`
   - Or similar tunnel URL

2. **In Expo Go app:**
   - Open Expo Go
   - Tap "Enter URL manually" (at bottom)
   - Paste the URL
   - Tap "Connect"

---

## 🎯 **Always Use Tunnel Mode on Windows**

**For iPhone testing on Windows, always use:**
```bash
npm run start:tunnel
```

This solves 99% of connection issues!

---

## ✅ **You're Ready!**

1. Run: `npm run start:tunnel`
2. Scan QR code with iPhone Camera
3. Test your app!

---

**Tunnel mode = No more connection problems!** 📱✅
