# API Keys Setup Guide

Complete this guide to enable full notification capabilities in your IoT Security Platform.

## 🔑 Required API Keys

### 1. **Twilio** (SMS, WhatsApp, Voice Calls)
### 2. **SendGrid** (Email Notifications)

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

### Test It
```bash
# Test SMS
curl -X POST http://localhost:8000/api/test/sms \
  -H "Content-Type: application/json" \
  -d '{"to":"+447712345678","message":"Test from IoT Security"}'
```

---

## 📧 SendGrid Setup (Email)

### Step 1: Create SendGrid Account
1. Go to https://signup.sendgrid.com/
2. Sign up (free tier: 100 emails/day)
3. Verify your email address

### Step 2: Create API Key
1. Go to [Settings → API Keys](https://app.sendgrid.com/settings/api_keys)
2. Click **Create API Key**
3. Name it: "IoT Security Platform"
4. Choose **Full Access** or **Restricted Access** (Mail Send only)
5. Click **Create & View**
6. **IMPORTANT**: Copy the API key NOW (you can't see it again!)

### Step 3: Verify Sender Identity
1. Go to **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender**
3. Fill in your details:
   - From Name: IoT Security Platform
   - From Email: alerts@yourdomain.com (or your email)
   - Reply To: (same as above)
4. Click **Create**
5. Check your email and verify

### Step 4: Add to `.env` File
```env
SENDGRID_API_KEY=SG.your_api_key_here
FROM_EMAIL=alerts@yourdomain.com
```

### Test It
```bash
# Test email
curl -X POST http://localhost:8000/api/test/email \
  -H "Content-Type: application/json" \
  -d '{"to":"your@email.com","subject":"Test","body":"Test from IoT Security"}'
```

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
