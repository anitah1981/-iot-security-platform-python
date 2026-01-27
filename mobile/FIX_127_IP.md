# 🔧 Fix 127.0.0.1 IP Address Issue

**Problem:** Expo is showing `exp://127.0.0.1:8081` instead of your network IP.

**Why this fails:**
- `127.0.0.1` is localhost (your computer only)
- iPhone can't reach `127.0.0.1` on your Windows computer
- iPhone thinks it's trying to connect to itself
- Results in "internet connection appears to be offline"

---

## ✅ **Solution 1: Restart with Correct IP**

### **Step 1: Stop Expo**
Press `Ctrl+C` in the terminal

### **Step 2: Start with Your Network IP**
```bash
npm run start:iphone
```

This uses your actual IP: `192.168.0.235`

### **Step 3: Connect**
- Use iPhone Camera to scan QR code
- Or in Safari, type: `exp://192.168.0.235:8081`

---

## ✅ **Solution 2: Force LAN Mode**

### **Stop Expo, then run:**
```bash
expo start --lan --host lan
```

This forces Expo to detect your network IP.

---

## ✅ **Solution 3: Manual IP (If Above Don't Work)**

### **Stop Expo, then:**
```bash
expo start --lan --host 192.168.0.235
```

Replace `192.168.0.235` with your actual IP from `ipconfig`.

---

## 🔍 **Why This Happens**

Expo's `--lan` mode sometimes fails to detect your network IP and defaults to `127.0.0.1`. This happens when:
- Network adapter isn't properly detected
- Multiple network adapters confuse Expo
- VPN or virtual adapters interfere

---

## ✅ **Quick Fix Right Now**

1. **Stop Expo:** `Ctrl+C`

2. **Run:**
   ```bash
   npm run start:iphone
   ```

3. **Check terminal** - should now show: `exp://192.168.0.235:8081`

4. **Connect iPhone:**
   - Camera app → Scan QR code
   - Or Safari → `exp://192.168.0.235:8081`

---

**This should fix the connection!** ✅
