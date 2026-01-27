# 🔧 Update API URL Before Building

**Important:** Update your backend URL before building standalone apps!

---

## 📝 **Step 1: Edit `app.json`**

Open `mobile/app.json` and find this section:

```json
"extra": {
  "apiUrl": "http://localhost:8000"
}
```

---

## 🌐 **Step 2: Choose Your Backend URL**

### **Option A: Deployed Backend**
If your backend is deployed (e.g., on Heroku, AWS, etc.):
```json
"extra": {
  "apiUrl": "https://your-backend-domain.com"
}
```

### **Option B: Local Backend with ngrok**
If testing locally, use ngrok:

1. **Install ngrok:**
   ```bash
   # Download from https://ngrok.com/download
   # Or use chocolatey on Windows:
   choco install ngrok
   ```

2. **Start ngrok tunnel:**
   ```bash
   ngrok http 8000
   ```

3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

4. **Update app.json:**
   ```json
   "extra": {
     "apiUrl": "https://abc123.ngrok.io"
   }
   ```

### **Option C: Production URL**
For production apps:
```json
"extra": {
  "apiUrl": "https://api.iot-security-platform.com"
}
```

---

## ✅ **Step 3: Verify**

After updating, your `app.json` should look like:

```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://your-actual-backend-url.com"
    }
  }
}
```

---

## 🚀 **Step 4: Build**

Now you can build your apps:
```bash
eas build --platform ios --profile preview
eas build --platform android --profile preview
```

---

## ⚠️ **Important Notes**

- **localhost won't work** - mobile apps can't access `localhost` on your computer
- **Use HTTPS** - required for production apps
- **ngrok is temporary** - URL changes each time you restart ngrok (unless you have a paid plan)
- **Deploy backend first** - for production, deploy your backend before building apps

---

**Update the URL, then build!** 🚀
