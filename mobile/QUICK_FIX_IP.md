# ⚡ Quick Fix - Wrong IP Address

**Problem:** Terminal shows `exp://127.0.0.1:8081` (won't work with iPhone)

**Fix:** Use your network IP instead

---

## 🚀 **Fix in 3 Steps**

### **1. Stop Expo**
Press `Ctrl+C` in terminal

### **2. Start with Correct IP**
```bash
npm run start:iphone
```

### **3. Connect iPhone**
- **Camera app** → Scan QR code (should now show correct IP)
- **Or Safari** → Type: `exp://192.168.0.235:8081`

---

## ✅ **That's It!**

The terminal should now show: `exp://192.168.0.235:8081` instead of `127.0.0.1`

**This will work!** ✅
