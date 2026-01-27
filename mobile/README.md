# 📱 IoT Security Mobile App

**React Native mobile app for IoT Security Platform**

---

## 🚀 **Quick Start**

### **Build Standalone Apps (Recommended)**

Skip Expo Go - build real apps:

```bash
cd mobile
.\build-apps.ps1
```

**Or manually:**
```bash
npm install -g eas-cli
eas login
eas build:configure
eas build --platform ios --profile preview
eas build --platform android --profile preview
```

---

## 📋 **Before Building**

1. **Update API URL** in `app.json`:
   ```json
   "apiUrl": "https://your-backend-url.com"
   ```
   *(See UPDATE_API_URL.md for options)*

2. **Create Expo account** at https://expo.dev (free)

3. **Run pre-build check:**
   ```bash
   .\pre-build-check.ps1
   ```

---

## 🛠️ **Development**

### **Install Dependencies**
```bash
npm install
```

### **Start Development Server**
```bash
npm start
```

### **Run on Device (Expo Go)**
```bash
npm run start:lan
```
*(Then scan QR code with Expo Go app)*

---

## 📚 **Documentation**

- **QUICK_BUILD.md** - Fastest way to build
- **START_BUILDING.md** - Complete build guide
- **UPDATE_API_URL.md** - Backend URL configuration
- **READY_TO_BUILD.md** - Build readiness checklist

---

## 📁 **Project Structure**

```
mobile/
├── src/
│   ├── screens/       # App screens
│   ├── components/    # Reusable components
│   ├── navigation/   # Navigation setup
│   ├── context/      # React contexts
│   ├── config/       # API configuration
│   ├── services/     # API services
│   └── utils/        # Utilities
├── assets/            # Images, icons
├── App.js            # Root component
├── app.json          # Expo configuration
├── eas.json          # EAS build configuration
└── package.json      # Dependencies
```

---

## ✅ **Features**

- ✅ Device monitoring dashboard
- ✅ Real-time alerts
- ✅ Offline support
- ✅ Push notifications
- ✅ Authentication
- ✅ Dark theme

---

## 🔧 **Configuration**

### **API URL**
Set in `app.json`:
```json
"extra": {
  "apiUrl": "https://your-backend.com"
}
```

### **Build Profiles**
Configured in `eas.json`:
- `preview` - Internal testing
- `production` - App store builds

---

## 📱 **Building**

### **iOS**
```bash
eas build --platform ios --profile preview
```

### **Android**
```bash
eas build --platform android --profile preview
```

---

## 🐛 **Troubleshooting**

### **Build Fails**
- Check API URL is correct
- Verify backend is accessible
- Run `pre-build-check.ps1`

### **Can't Install on iPhone**
- Trust developer certificate in Settings
- Use HTTPS download link

### **API Connection Issues**
- Verify backend URL is correct
- Check backend is running
- Ensure CORS is configured

---

## 📝 **Notes**

- **First build:** Takes 10-15 minutes
- **Free tier:** Limited builds per month
- **No Mac needed:** EAS builds iOS in cloud
- **Assets:** Default icons used if custom icons not provided

---

## 🎯 **Ready to Build?**

Run the build script:
```bash
.\build-apps.ps1
```

**Or see QUICK_BUILD.md for step-by-step guide**
