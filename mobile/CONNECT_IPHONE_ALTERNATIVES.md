# 📱 Connect iPhone to Expo - Alternative Methods

**Expo Go UI has changed - here are other ways to connect:**

---

## ✅ **Method 1: Scan QR Code with iPhone Camera**

### **Steps:**
1. **Make sure Expo is running** (you should see a QR code in terminal)
2. **Open iPhone Camera app** (not Expo Go)
3. **Point camera at QR code** in your terminal/computer screen
4. **Tap the notification** that appears at top of screen
5. **Opens in Expo Go automatically**

**This is the easiest method!** ✅

---

## ✅ **Method 2: Use Expo Go's Built-in Scanner**

### **Steps:**
1. **Open Expo Go app**
2. **Look for "Scan QR Code" button** (usually on home screen)
3. **Tap it** to open scanner
4. **Point at QR code** in terminal
5. **App loads automatically**

---

## ✅ **Method 3: Share URL via Text/Email**

### **Steps:**
1. **Get the URL from terminal:**
   - Look for: `exp://192.168.0.235:8081`
   - Or similar URL shown in Expo output

2. **Send URL to yourself:**
   - Text it to your iPhone
   - Email it to yourself
   - Copy and paste in Notes app (if synced)

3. **In Expo Go:**
   - Long-press the URL
   - Select "Open in Expo Go"
   - Or copy URL and paste in Expo Go's search/URL field

---

## ✅ **Method 4: Use Expo Go's Recent Projects**

### **If you've connected before:**
1. **Open Expo Go**
2. **Check "Recent" or "History"** section
3. **Tap your project** if it appears
4. **Reconnects automatically**

---

## ✅ **Method 5: Direct URL in Safari**

### **Steps:**
1. **On iPhone, open Safari**
2. **Type in address bar:**
   ```
   exp://192.168.0.235:8081
   ```
   (Use your actual IP from terminal)

3. **Safari will ask to open in Expo Go**
4. **Tap "Open"**

---

## 🎯 **Recommended: Camera App Method**

**Easiest and most reliable:**

1. **Start Expo:**
   ```bash
   npm run start:lan
   ```

2. **Wait for QR code** to appear in terminal

3. **On iPhone:**
   - Open **Camera app** (not Expo Go)
   - Point at QR code on screen
   - Tap notification that appears
   - Opens in Expo Go!

---

## 🔧 **If QR Code Doesn't Work**

### **Check:**
- ✅ Both devices on same WiFi
- ✅ Expo is running (check terminal)
- ✅ QR code is visible in terminal
- ✅ Camera has permission to scan QR codes

### **Try:**
- Restart Expo
- Restart iPhone
- Try different network
- Check Windows Firewall

---

## 📝 **Quick Test**

**Right now:**
1. Make sure Expo is running (`npm run start:lan`)
2. Look for QR code in terminal
3. Open iPhone Camera app
4. Point at QR code
5. Tap notification

**This should work!** ✅

---

**Camera app method is usually the most reliable!** 📱
