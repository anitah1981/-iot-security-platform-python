# 🧪 Test if Server is Accessible

**Quick test to see if the issue is network or Expo:**

---

## ✅ **Test 1: Check if Port is Open**

### **On iPhone Safari, try:**
```
http://192.168.0.235:8081
```

**Expected:**
- ✅ **If it loads:** Server is accessible, issue is with `exp://` protocol
- ❌ **If it doesn't load:** Server not accessible (firewall/network issue)

---

## ✅ **Test 2: Check Windows Firewall**

### **Quick Test:**
1. **Temporarily disable Windows Firewall**
2. **Try connecting again**
3. **If it works:** Firewall was blocking
4. **Re-enable firewall** and add Node.js exception

---

## ✅ **Test 3: Try Different URL Format**

### **In Safari, try these:**
```
exp://192.168.0.235:8081
http://192.168.0.235:8081
```

**See which one works (if any)**

---

## ✅ **Test 4: Check Network**

### **On iPhone:**
1. **Settings** → **WiFi**
2. **Tap ⓘ next to your network**
3. **Check IP Address**
4. **Should be:** `192.168.0.x` (same network as computer)

**If different:** Connect to same WiFi network

---

## 🎯 **What to Report Back**

1. **Does `http://192.168.0.235:8081` load in Safari?**
2. **What error message do you see?**
3. **Are both devices on same WiFi?**
4. **Have you tried disabling firewall?**

---

**This will help identify the exact issue!** 🔍
