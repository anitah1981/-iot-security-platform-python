# 📱 Mobile App Installation Guide

## Prerequisites

1. **Node.js** (v18 or later)
   - Download from: https://nodejs.org/

2. **Expo CLI** (optional - can use npx)
   ```bash
   npm install -g expo-cli
   ```

3. **For iOS Development:**
   - Mac computer required
   - Xcode (from App Store)
   - iOS Simulator (comes with Xcode)

4. **For Android Development:**
   - Android Studio
   - Android SDK
   - Android Emulator

5. **For Testing on Physical Device:**
   - Expo Go app (iOS App Store / Google Play Store)

---

## Installation Steps

### **1. Navigate to Mobile Directory**

```bash
cd mobile
```

### **2. Install Dependencies**

```bash
npm install
```

This will install all required packages:
- React Native
- Expo
- Navigation libraries
- API client (axios)
- Storage utilities
- Push notification libraries

### **3. Configure API URL**

Edit `app.json`:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://your-api-domain.com"
    }
  }
}
```

Or for local development:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "http://localhost:8000"
    }
  }
}
```

### **4. Start Development Server**

```bash
npm start
```

This will:
- Start Metro bundler
- Open Expo DevTools in browser
- Show QR code in terminal

---

## 🧪 Testing

### **Option 1: iOS Simulator (Mac only)**

1. Make sure Xcode is installed
2. Run: `npm start`
3. Press `i` in terminal
4. iOS Simulator will open automatically

### **Option 2: Android Emulator**

1. Make sure Android Studio is installed
2. Create an AVD (Android Virtual Device)
3. Start the emulator
4. Run: `npm start`
5. Press `a` in terminal

### **Option 3: Physical Device**

1. Install **Expo Go** app on your phone:
   - iOS: App Store
   - Android: Google Play Store

2. Run: `npm start`

3. Scan QR code:
   - iOS: Use Camera app
   - Android: Use Expo Go app to scan

4. App will load on your device

---

## 🐛 Troubleshooting

### **Metro bundler won't start**
```bash
npm start -- --reset-cache
```

### **iOS simulator not opening**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Open Xcode and accept license
sudo xcodebuild -license accept
```

### **Android emulator issues**
- Make sure Android Studio is installed
- Create an AVD in Android Studio
- Start emulator before running `npm start`

### **"Module not found" errors**
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install
```

### **Port already in use**
```bash
# Kill process on port 8081 (Metro bundler)
# Windows:
netstat -ano | findstr :8081
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8081 | xargs kill
```

---

## 📦 Building for Production

### **Using EAS Build (Recommended)**

1. **Install EAS CLI:**
   ```bash
   npm install -g eas-cli
   ```

2. **Login:**
   ```bash
   eas login
   ```

3. **Configure:**
   ```bash
   eas build:configure
   ```

4. **Build iOS:**
   ```bash
   eas build --platform ios
   ```

5. **Build Android:**
   ```bash
   eas build --platform android
   ```

### **Local Build (Advanced)**

For iOS (Mac only):
```bash
expo build:ios
```

For Android:
```bash
expo build:android
```

---

## ✅ **Verification**

After installation, verify everything works:

1. ✅ Server starts without errors
2. ✅ QR code appears in terminal
3. ✅ Can open in simulator/emulator
4. ✅ Can scan QR code with Expo Go
5. ✅ App loads on device
6. ✅ Can login with test account
7. ✅ Dashboard loads
8. ✅ Devices list loads
9. ✅ Alerts list loads

---

## 📝 **Next Steps**

1. Test all screens
2. Test authentication flow
3. Test offline mode
4. Configure push notifications
5. Build production version
6. Submit to App Store / Play Store

---

**Happy coding!** 🚀📱
