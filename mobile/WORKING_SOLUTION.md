# ✅ Working Solution - Connect iPhone

**The issue:** Expo's `--host` flag doesn't accept IP addresses directly.

**The fix:** Use `--lan` and manually enter your IP address.

---

## 🚀 **Step-by-Step**

### **1. Start Expo**
```bash
npm run start:lan
```

### **2. Get Your IP** (if you forgot)
```cmd
ipconfig
```
Look for IPv4 Address (should be `192.168.0.235`)

### **3. On iPhone - Use Safari**

**Option A: Safari (Easiest)**
1. Open **Safari** on iPhone
2. In address bar, type:
   ```
   exp://192.168.0.235:8081
   ```
3. Safari will show "Open in Expo Go"
4. Tap it
5. App loads!

**Option B: Camera App**
1. Open **Camera app**
2. Point at QR code (even if it shows wrong IP)
3. When notification appears, **don't tap it**
4. Instead, manually type the URL in Safari

---

## ✅ **Why This Works**

- Expo server is listening on your network IP (`192.168.0.235`)
- Even if QR code shows `127.0.0.1`, the server is accessible
- Manually entering the correct IP bypasses the detection issue
- Safari can open `exp://` URLs and redirect to Expo Go

---

## 🎯 **Quick Command**

**Just run:**
```bash
npm run start:lan
```

**Then on iPhone Safari:**
```
exp://192.168.0.235:8081
```

**That's it!** ✅

---

**This is the most reliable method!** 📱
