# 📱 Mobile App Setup Guide

**React Native with Expo** - iOS & Android

---

## 🚀 Quick Start

### **1. Prerequisites**

```bash
# Install Node.js (v18 or later)
# Install Expo CLI globally
npm install -g expo-cli

# Or use npx (recommended)
npx expo-cli --version
```

### **2. Install Dependencies**

```bash
cd mobile
npm install
```

### **3. Configure API URL**

Edit `mobile/app.json`:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://your-api-domain.com"
    }
  }
}
```

Or create `mobile/.env`:
```
API_URL=https://your-api-domain.com
```

### **4. Start Development Server**

```bash
cd mobile
npm start
```

Then:
- Press `i` for iOS simulator
- Press `a` for Android emulator
- Scan QR code with Expo Go app on your phone

---

## 📁 Project Structure

```
mobile/
├── App.js                 # Main app entry
├── app.json              # Expo configuration
├── package.json          # Dependencies
├── babel.config.js       # Babel config
├── src/
│   ├── config/
│   │   └── api.js        # API client
│   ├── context/
│   │   ├── AuthContext.js
│   │   └── NetworkContext.js
│   ├── navigation/
│   │   └── MainTabs.js
│   ├── screens/
│   │   ├── LoginScreen.js
│   │   ├── SignupScreen.js
│   │   ├── DashboardScreen.js
│   │   ├── DevicesScreen.js
│   │   ├── AlertsScreen.js
│   │   └── SettingsScreen.js
│   ├── components/
│   │   ├── DeviceCard.js
│   │   ├── AlertCard.js
│   │   └── Chart.js
│   └── utils/
│       └── storage.js
└── assets/
    ├── icon.png
    ├── splash.png
    └── adaptive-icon.png
```

---

## 🔧 Configuration

### **API Configuration**

Update `src/config/api.js` with your API URL:
```javascript
const API_URL = 'https://your-api-domain.com';
```

### **Push Notifications**

1. Set up Firebase Cloud Messaging
2. Add Firebase config to `app.json`
3. Configure notification permissions

### **App Icons & Splash**

Replace files in `assets/`:
- `icon.png` (1024x1024)
- `splash.png` (1242x2436)
- `adaptive-icon.png` (1024x1024)

---

## 📦 Building for Production

### **iOS**

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure build
eas build:configure

# Build for iOS
eas build --platform ios
```

### **Android**

```bash
# Build for Android
eas build --platform android
```

---

## 🧪 Testing

### **Development**

```bash
npm start
```

### **On Physical Device**

1. Install Expo Go app
2. Scan QR code from terminal
3. App loads on device

### **Production Build**

```bash
# Test production build locally
eas build --platform ios --profile preview
```

---

## 📝 Next Steps

1. ✅ Authentication screens (Done)
2. ⏳ Dashboard screen
3. ⏳ Device list/details
4. ⏳ Alert list/details
5. ⏳ Settings screen
6. ⏳ Push notifications
7. ⏳ Offline mode

---

## 🐛 Troubleshooting

### **Metro bundler issues**
```bash
npm start -- --reset-cache
```

### **iOS simulator not opening**
```bash
# Install Xcode Command Line Tools
xcode-select --install
```

### **Android emulator issues**
- Make sure Android Studio is installed
- Create an AVD (Android Virtual Device)
- Start emulator before running `npm start`

---

**Happy coding!** 🚀
