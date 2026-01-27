# 📱 IoT Security Platform - Mobile App

React Native mobile application for iOS and Android using Expo.

---

## 🚀 Quick Start

### **Prerequisites**
- Node.js 18+ installed
- Expo CLI: `npm install -g expo-cli` (or use npx)
- For iOS: Xcode (Mac only)
- For Android: Android Studio

### **Installation**

```bash
cd mobile
npm install
```

### **Configure API URL**

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

### **Run**

```bash
npm start
```

Then:
- Press `i` for iOS simulator
- Press `a` for Android emulator
- Scan QR code with Expo Go app

---

## 📁 Project Structure

```
mobile/
├── App.js                    # Main entry point
├── app.json                 # Expo configuration
├── package.json             # Dependencies
├── src/
│   ├── config/
│   │   └── api.js          # API client
│   ├── context/
│   │   ├── AuthContext.js  # Authentication state
│   │   └── NetworkContext.js # Network status
│   ├── navigation/
│   │   └── MainTabs.js     # Bottom tab navigation
│   ├── screens/
│   │   ├── LoginScreen.js
│   │   ├── SignupScreen.js
│   │   ├── DashboardScreen.js
│   │   ├── DevicesScreen.js
│   │   ├── AlertsScreen.js
│   │   └── SettingsScreen.js
│   └── components/
│       ├── DeviceCard.js
│       ├── AlertCard.js
│       └── StatsCard.js
└── assets/                  # Images, icons
```

---

## ✅ **Current Status**

### **Completed:**
- ✅ Project setup with Expo
- ✅ Authentication screens (Login, Signup, Forgot Password, Reset Password)
- ✅ Navigation structure
- ✅ Dashboard screen
- ✅ Device list screen
- ✅ Alert list screen
- ✅ Settings screen
- ✅ Network status detection
- ✅ Offline mode handling

### **In Progress:**
- ⏳ Device detail screen
- ⏳ Alert detail screen
- ⏳ Push notifications
- ⏳ Charts/analytics
- ⏳ Notification preferences

---

## 🔧 **Features**

### **Authentication**
- Login with email/password
- Signup with validation
- Forgot password flow
- Reset password
- Secure token storage

### **Dashboard**
- Device overview
- Alert summary
- Quick stats
- Pull to refresh

### **Devices**
- List all devices
- Device status (online/offline)
- Filter and search
- Device details

### **Alerts**
- List all alerts
- Filter by severity
- Filter by status
- Alert details

### **Settings**
- Account information
- Plan details
- Logout

---

## 📦 **Building for Production**

### **iOS**
```bash
eas build --platform ios
```

### **Android**
```bash
eas build --platform android
```

---

## 🐛 **Troubleshooting**

### **Metro bundler issues**
```bash
npm start -- --reset-cache
```

### **iOS simulator not opening**
- Install Xcode Command Line Tools: `xcode-select --install`
- Open Xcode and accept license

### **Android emulator issues**
- Make sure Android Studio is installed
- Create an AVD (Android Virtual Device)
- Start emulator before running `npm start`

---

## 📝 **Next Steps**

1. Add device detail screen
2. Add alert detail screen
3. Implement push notifications
4. Add charts/analytics
5. Add notification preferences
6. Test on physical devices
7. Submit to App Store / Play Store

---

**Happy coding!** 🚀
