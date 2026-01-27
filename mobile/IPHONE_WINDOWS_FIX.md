# 📱 iPhone + Windows - Expo Go Connection Fix

**Common issue: QR code doesn't work when connecting iPhone to Expo on Windows**

---

## 🔍 **Why QR Code Might Not Work**

1. **Network connectivity** - Phone and computer not on same network
2. **Firewall blocking** - Windows Firewall blocking Metro bundler
3. **Wrong URL** - Expo trying to use localhost (not accessible from phone)
4. **Network type** - Some networks block device-to-device communication

---

## ✅ **Solution 1: Use Tunnel Mode (Recommended)**

**This creates a public URL that works from anywhere:**

```bash
cd mobile
npm start -- --tunnel
```

**Or:**
```bash
npx expo start --tunnel
```

**What this does:**
- Creates a public URL via Expo's servers
- Works even if phone and computer are on different networks
- Bypasses firewall issues
- More reliable for Windows + iPhone

**Then:**
1. Scan QR code with iPhone Camera app
2. Tap the notification
3. Opens in Expo Go

---

## ✅ **Solution 2: Manual URL Entry**

**If QR code still doesn't work:**

1. **Get the URL from terminal:**
   - Look for: `exp://192.168.x.x:8081` or similar
   - Or use tunnel URL: `exp://xxx-xxx.anonymous.exp.direct:80`

2. **In Expo Go app:**
   - Open Expo Go
   - Tap "Enter URL manually"
   - Type the URL from terminal
   - Press "Connect"

---

## ✅ **Solution 3: Fix Network Connection**

### **Check Same Network:**
1. **On Windows:** Open Command Prompt
   ```cmd
   ipconfig
   ```
   - Note your IP address (e.g., `192.168.1.100`)

2. **On iPhone:** Settings → WiFi → Tap your network
   - Check IP address matches same network (e.g., `192.168.1.x`)

### **Fix Windows Firewall:**
1. **Open Windows Defender Firewall**
2. **Allow an app through firewall**
3. **Add Node.js** (or allow port 8081)
4. **Or temporarily disable firewall** (for testing only)

---

## ✅ **Solution 4: Use LAN Mode Explicitly**

```bash
cd mobile
npx expo start --lan
```

This forces Expo to use your local network IP address.

---

## 🎯 **Best Solution: Tunnel Mode**

**For Windows + iPhone, tunnel mode is most reliable:**

```bash
cd mobile
npm start -- --tunnel
```

**Advantages:**
- ✅ Works across different networks
- ✅ Bypasses firewall
- ✅ More reliable
- ✅ Works from anywhere

**Disadvantages:**
- ⚠️ Slightly slower (goes through Expo servers)
- ⚠️ Requires internet connection

---

## 📝 **Step-by-Step: Tunnel Mode**

1. **Start Expo with tunnel:**
   ```bash
   cd mobile
   npm start -- --tunnel
   ```

2. **Wait for QR code** to appear in terminal

3. **On iPhone:**
   - Open **Camera app**
   - Point at QR code
   - Tap notification that appears
   - Opens in Expo Go

4. **If that doesn't work:**
   - Open **Expo Go app**
   - Tap "Enter URL manually"
   - Copy URL from terminal (starts with `exp://`)
   - Paste and connect

---

## 🔧 **Troubleshooting**

### **"Can't connect to Metro bundler"**
- Use tunnel mode: `npm start -- --tunnel`
- Or check firewall settings

### **"Network request failed"**
- Make sure you're using tunnel mode
- Check internet connection
- Try restarting Expo

### **"Expo Go can't find the project"**
- Make sure URL is correct
- Try tunnel mode
- Check that Metro bundler is running

---

## ✅ **Recommended: Always Use Tunnel on Windows**

**For Windows + iPhone, always use:**
```bash
npm start -- --tunnel
```

This is the most reliable method!

---

## 🚀 **Quick Fix Right Now**

1. **Stop current Expo** (Ctrl+C)

2. **Restart with tunnel:**
   ```bash
   cd mobile
   npm start -- --tunnel
   ```

3. **Scan QR code** with iPhone Camera

4. **Done!** ✅

---

**Tunnel mode solves 99% of Windows + iPhone connection issues!** 📱
