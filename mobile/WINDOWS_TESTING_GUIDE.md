# 📱 Mobile App Testing on Windows

**Since you're on Windows, you can't use iOS Simulator. Here are your options:**

---

## ✅ **Option 1: Android Emulator (Recommended for Windows)**

### **Prerequisites:**
1. Install **Android Studio**: https://developer.android.com/studio
2. Install Android SDK and create an emulator

### **Steps:**
1. **Open Android Studio**
2. **Tools** → **Device Manager**
3. **Create Device** → Choose a phone (e.g., Pixel 5)
4. **Download a system image** (e.g., Android 13)
5. **Start the emulator**

### **Run Expo:**
```bash
cd mobile
npm start
# Press 'a' to open Android emulator
```

---

## ✅ **Option 2: Physical Android Device**

### **Steps:**
1. **Install Expo Go** on your Android phone:
   - Google Play Store: https://play.google.com/store/apps/details?id=host.exp.exponent

2. **Connect to same WiFi** as your computer

3. **Start Expo:**
   ```bash
   cd mobile
   npm start
   ```

4. **Scan QR code** with:
   - **Android:** Open Expo Go app → Scan QR code
   - Or use the Expo Go app's built-in scanner

---

## ✅ **Option 3: Web Version (Quick Test)**

### **Steps:**
```bash
cd mobile
npm start
# Press 'w' to open web version
```

This opens the app in your browser (limited functionality, but good for quick testing).

---

## ✅ **Option 4: Physical iOS Device (If You Have One)**

### **Steps:**
1. **Install Expo Go** on your iPhone:
   - App Store: https://apps.apple.com/app/expo-go/id982107779

2. **Connect to same WiFi** as your computer

3. **Start Expo:**
   ```bash
   cd mobile
   npm start
   ```

4. **Scan QR code** with:
   - **iOS:** Open Camera app → Point at QR code → Tap notification

---

## 🎯 **Recommended: Android Emulator**

**Best for development on Windows:**
- Full emulator experience
- Easy to test
- No physical device needed

**Setup time:** ~15 minutes (one-time setup)

---

## 🚀 **Quick Start (Android Emulator)**

1. **Install Android Studio** (if not installed)
2. **Create an emulator** in Android Studio
3. **Start the emulator**
4. **Run:**
   ```bash
   cd mobile
   npm start
   # Press 'a' when emulator is running
   ```

---

## 📝 **Troubleshooting**

### **"Android emulator not found"**
- Make sure emulator is running before pressing 'a'
- Check that Android SDK is installed
- Try: `adb devices` to see if emulator is detected

### **"Can't connect to Metro bundler"**
- Make sure you're on the same network
- Check firewall settings
- Try: `npm start -- --reset-cache`

### **"Expo Go not working"**
- Make sure Expo Go app is up to date
- Clear Expo Go cache
- Restart Metro bundler

---

## ✅ **You're Ready!**

Choose your preferred option and start testing your mobile app!

**Recommended:** Start with Android Emulator for the best development experience on Windows.
