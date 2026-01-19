# API Keys Setup Guide

Complete this guide to enable full notification capabilities in your IoT Security Platform.

## 🔑 Required Setup

### 1. **Twilio** (SMS, WhatsApp, Voice Calls)
### 2. **Gmail SMTP** (Email Notifications - FREE & Easy!)

---

## 📱 Twilio Setup (SMS/WhatsApp/Voice)

### Step 1: Create Twilio Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up for a free account
3. Verify your email and phone number

### Step 2: Get Your Credentials
1. Go to your [Twilio Console Dashboard](https://console.twilio.com/)
2. Find your **Account SID** and **Auth Token**
3. Copy both values

### Step 3: Get a Phone Number
1. In Twilio Console, go to **Phone Numbers** → **Buy a Number**
2. Choose a number (free trial includes $15 credit)
3. Select capabilities: Voice, SMS, MMS
4. Purchase the number
5. Copy your new phone number (format: +1234567890)

### Step 4: Enable WhatsApp (Optional)
1. Go to **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Follow instructions to activate WhatsApp sandbox
3. Your WhatsApp number will be: `whatsapp:+14155238886` (Twilio sandbox)
4. For production, apply for WhatsApp Business API

### Step 5: Add to `.env` File
```env
TWILIO_ACCOUNT_SID=AC...your_account_sid
TWILIO_AUTH_TOKEN=...your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Trial & UK Regulatory Notes
- Trial Twilio accounts can only send SMS to verified recipient numbers.
- UK SMS may require a UK Regulatory Bundle for UK numbers.
- If you see error code **21612**, enable UK in Twilio Geo Permissions.

### Test It
```bash
# Test SMS (requires login + saved preferences)
# 1) Login and capture token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"your_password"}' | jq -r '.token')

# 2) Ensure sms_enabled=true and phone_number set in /api/notification-preferences

# 3) Send test SMS
curl -X POST http://localhost:8000/api/notification-preferences/test/sms \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📧 Gmail SMTP Setup (Email) - FREE & Easy!

### Step 1: Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Find **"2-Step Verification"**
3. Click **"Get Started"**
4. Follow the steps (they'll text you a code)
5. Complete the setup

### Step 2: Create App Password
1. Go to: https://myaccount.google.com/apppasswords
2. In "Select app" dropdown: Choose **"Mail"**
3. In "Select device" dropdown: Choose **"Other"**
4. Type: "IoT Security Platform"
5. Click **"Generate"**
6. **COPY THE 16-CHARACTER PASSWORD** (looks like: `abcd efgh ijkl mnop`)
   - You won't be able to see it again!

### Step 3: Add to `.env` File
```env
# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
FROM_EMAIL=your.email@gmail.com
```

**Replace:**
- `your.email@gmail.com` with YOUR Gmail address
- `abcd efgh ijkl mnop` with your app password from Step 2

### Why Gmail Instead of SendGrid?
✅ **FREE** - No daily limits for personal use  
✅ **No verification needed** - Just enable 2FA and get app password  
✅ **5 minutes setup** - vs 20+ minutes for SendGrid  
✅ **Familiar** - You already have Gmail  
✅ **Reliable** - Google's infrastructure

---

## ✅ Verify Your Setup

### Method 1: Use the Dashboard
1. Go to http://localhost:8000/dashboard
2. Create a test alert
3. Check your email/SMS

### Method 2: Direct API Test
```python
# test_notifications.py
import requests

API_BASE = "http://localhost:8000"

# Login first
login = requests.post(f"{API_BASE}/api/auth/login", json={
    "email": "your@email.com",
    "password": "your_password"
})
token = login.json()["token"]

headers = {"Authorization": f"Bearer {token}"}

# Update notification preferences
prefs = {
    "email_enabled": True,
    "sms_enabled": True,
    "whatsapp_enabled": True,
    "voice_enabled": False,
    "phone_number": "+447712345678",  # Your number
    "whatsapp_number": "+447712345678",
    "email_severities": ["low", "medium", "high", "critical"],
    "sms_severities": ["high", "critical"]
}

requests.put(
    f"{API_BASE}/api/notification-preferences",
    json=prefs,
    headers=headers
)

# Create a test device
device = requests.post(
    f"{API_BASE}/api/devices",
    json={
        "device_id": "test-001",
        "name": "Test Camera",
        "type": "Camera",
        "ip_address": "192.168.1.100"
    },
    headers=headers
)
device_id = device.json()["id"]

# Create a test alert (will trigger notifications!)
requests.post(
    f"{API_BASE}/api/alerts",
    json={
        "device_id": device_id,
        "type": "connectivity",
        "severity": "high",
        "message": "Test alert - please ignore"
    },
    headers=headers
)

print("✓ Test alert created! Check your email/SMS")
```

Run it:
```bash
python test_notifications.py
```

---

## 🚨 Troubleshooting

### Twilio Issues

**"Unverified numbers" error:**
- Free trial accounts can only send to verified numbers
- Go to Console → Phone Numbers → Verified Caller IDs
- Add your test phone number

**SMS not received:**
- Check Twilio logs in Console
- Verify number format: +[country code][number] (e.g., +447712345678)
- Check if message is in spam

**WhatsApp not working:**
- Make sure you followed sandbox setup
- Send "join [your-code]" to the sandbox number first
- For production, apply for WhatsApp Business API approval

### SendGrid Issues

**"Forbidden" error:**
- Verify your sender identity (check email for verification link)
- Make sure API key has "Mail Send" permission

**Emails not received:**
- Check spam/junk folder
- Verify sender email is verified in SendGrid
- Check SendGrid Activity logs

**Daily limit reached:**
- Free tier: 100 emails/day
- Upgrade to paid plan for more

### General Issues

**Notifications not sending:**
```bash
# Check server logs
tail -f logs/app.log

# Or check console output
```

**Environment variables not loading:**
```bash
# Restart server
# Make sure .env file exists in project root
# Check .env syntax (no quotes needed usually)
```

---

## 💰 Cost Estimates

### Twilio (Pay-as-you-go after free trial)
- SMS: ~£0.04 per message (UK)
- WhatsApp: ~£0.005 per message
- Voice: ~£0.02 per minute (UK)
- Free trial: $15 credit

### SendGrid
- Free: 100 emails/day forever
- Essentials: £15/month for 50,000 emails
- Pro: £90/month for 100,000 emails

### Monthly Estimate (100 devices, 50 alerts/month)
- SendGrid Free: £0
- Twilio SMS (if 10 critical alerts): ~£0.40
- **Total: < £1/month** (with mostly email)

---

## 🎯 Next Steps

Once you have your API keys:

1. ✅ Add them to your `.env` file
2. ✅ Restart your server
3. ✅ Test notifications with the scripts above
4. ✅ Configure your user preferences in the dashboard
5. ✅ Deploy to production (see DEPLOYMENT.md)

---

## 📚 Additional Resources

- [Twilio Documentation](https://www.twilio.com/docs)
- [SendGrid Documentation](https://docs.sendgrid.com)
- [Twilio Pricing](https://www.twilio.com/pricing)
- [SendGrid Pricing](https://sendgrid.com/pricing)

---

**Need help?** Check the server logs or create an issue on GitHub.
