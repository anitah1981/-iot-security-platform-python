# 🚀 BUILD NOW - Final Instructions

**Your backend is running on port 8000. Here's how to build:**

---

## ⚡ **Quick Build (3 Steps)**

### **Step 1: Login to Expo**
```bash
cd mobile
eas login
```
*(Create account at https://expo.dev if needed - it's free!)*

### **Step 2: Set Up ngrok (for local backend)**

**In a NEW terminal window:**
```bash
# Install ngrok if needed
choco install ngrok

# Start ngrok tunnel
ngrok http 8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### **Step 3: Update API URL & Build**

**Back in the mobile directory:**
```bash
# Edit app.json - change "apiUrl" to your ngrok URL
# Then run:
.\build-apps.ps1
```

---

## 🎯 **Or Use This One Command:**

```bash
cd mobile
eas login
# Update app.json with ngrok URL
eas build --platform ios --profile preview
eas build --platform android --profile preview
```

---

## ✅ **What Happens:**

1. **EAS uploads your code** to cloud
2. **Builds in cloud** (10-15 minutes)
3. **Gives you download links**
4. **Install on your phone!**

---

## 📱 **After Build:**

- **iOS:** Open download link on iPhone → Install → Trust developer
- **Android:** Download APK → Enable unknown sources → Install

---

## 🎊 **Ready!**

**Run these commands:**
```bash
cd mobile
eas login
# Update app.json API URL (use ngrok URL)
.\build-apps.ps1
```

**You'll have real mobile apps in 15 minutes!** 🚀
