# 🚀 Installation Guide for New Features

## Quick Start (5 minutes)

### Step 1: Install New Dependencies

```bash
cd c:\IoT-security-app-python
.\venv\Scripts\activate
pip install reportlab pandas
```

### Step 2: Restart the Server

```bash
# Stop current server (Ctrl+C if running)
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Step 3: Test New Features

Visit these URLs:

1. **Dashboard with Charts:**  
   http://localhost:8000/dashboard
   - You'll see beautiful analytics charts at the top!
   - Scroll down to alerts section - notice the new "Export PDF" and "Export CSV" buttons

2. **Family Sharing:**  
   http://localhost:8000/family
   - Create your family
   - Invite members (use a second email to test)
   - Manage family members and permissions

3. **API Documentation:**  
   http://localhost:8000/docs
   - Check out the new API endpoints:
     - `/api/analytics/*` - Analytics endpoints
     - `/api/family/*` - Family management
     - `/api/alerts/export/*` - PDF/CSV exports
     - `/api/groups/*` - Device grouping
     - `/api/audit/*` - Audit logs

---

## Detailed Testing Guide

### 1. Test Dashboard Charts (1 minute)

```
1. Login: http://localhost:8000/login
   Email: anitah1981@gmail.com
   Password: Test123!!Test

2. Go to dashboard: http://localhost:8000/dashboard

3. You should see:
   ✅ System Health Score card
   ✅ Device Uptime percentage
   ✅ Recent alerts count
   ✅ Device Status pie chart
   ✅ Device Type pie chart
   ✅ Alert Trends line chart (30 days)
   ✅ Alert Severity bar chart
   ✅ Top Alerting Devices table
```

**If you don't see charts:**
- Hard refresh: Ctrl + Shift + R
- Check browser console for errors
- Verify Chart.js is loaded

---

### 2. Test Family Sharing (3 minutes)

#### Create a Family:
```
1. Go to: http://localhost:8000/family
2. Fill out the form:
   - Family Name: "Smith Family" or "My Home"
   - Description: "Our household IoT devices"
3. Click "Create Family"
4. You should see:
   ✅ Family info card
   ✅ Member count (should be 1 - you)
   ✅ Device count
   ✅ Invite form
```

#### Invite a Family Member:
```
1. In the "Invite Family Member" section:
   - Email: Use a different email (e.g., test@example.com)
   - Name: "Test User"
   - Role: "Member" or "Admin"
   - Check the permissions you want to grant
2. Click "Send Invitation"
3. Check the invitee's email for invitation link
```

#### Accept Invitation (if you have a second email):
```
1. Open the invitation email
2. Click the invitation link
3. If the email doesn't have an account:
   - You'll be prompted to create a password
   - Enter a secure password (12+ chars)
4. You're now part of the family!
5. Login with the new account and see shared devices
```

---

### 3. Test Alert Exports (2 minutes)

#### Export PDF:
```
1. Go to dashboard: http://localhost:8000/dashboard
2. Scroll to "Recent alerts" section
3. Click "📄 Export PDF" button
4. Wait for generation (2-3 seconds)
5. PDF should download automatically
6. Open the PDF:
   ✅ Should see report header with your name
   ✅ Statistics table
   ✅ Severity distribution pie chart
   ✅ Alert details table
   ✅ Professional formatting
```

#### Export CSV:
```
1. Click "📊 Export CSV" button
2. CSV should download immediately
3. Open in Excel/Google Sheets:
   ✅ All alert fields included
   ✅ Device names populated
   ✅ Timestamps formatted
   ✅ Ready for analysis
```

**Note:** If you get "Pro+ feature" error:
- You need to upgrade your account to Pro or Business
- Or temporarily modify the code to test (not recommended for production)

---

### 4. Test Device Grouping (2 minutes)

#### Via API (use Swagger UI):
```
1. Go to: http://localhost:8000/docs
2. Authorize with your JWT token:
   - Get token by logging in
   - Click "Authorize" button
   - Paste token
3. Test these endpoints:
   
   POST /api/groups/
   {
     "name": "Living Room",
     "description": "Devices in living room",
     "color": "#3b82f6"
   }
   
   GET /api/groups/
   - Should return your created groups
   
   POST /api/groups/{group_id}/devices/{device_id}
   - Assign a device to a group
```

---

### 5. Test Audit Logs (Business Plan Only)

#### Via API:
```
1. Upgrade account to Business plan (or skip)
2. Go to: http://localhost:8000/docs
3. Test:
   
   GET /api/audit/logs
   - Should return audit log entries
   
   GET /api/audit/logs/stats
   - Should return action breakdown
```

---

## Common Issues & Solutions

### Issue 1: Charts Not Showing
**Solution:**
```bash
# Hard refresh browser
Ctrl + Shift + R

# Check console for errors
# Verify Chart.js is loading
```

### Issue 2: Import Errors
**Solution:**
```bash
# Reinstall dependencies
pip uninstall reportlab pandas
pip install reportlab==4.2.5 pandas==2.2.0
```

### Issue 3: "Module not found" errors
**Solution:**
```bash
# Make sure you're in the right directory
cd c:\IoT-security-app-python

# Activate virtual environment
.\venv\Scripts\activate

# Check Python is using venv
where python
# Should show: c:\IoT-security-app-python\venv\Scripts\python.exe
```

### Issue 4: Family invitations not sending
**Solution:**
```bash
# Check email configuration in .env
# Make sure Gmail SMTP is configured:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your@gmail.com
```

### Issue 5: PDF Export fails
**Solution:**
```bash
# Check reportlab installed
pip show reportlab

# If missing:
pip install reportlab==4.2.5
```

---

## Verification Checklist

After installation, verify these work:

- [ ] Dashboard loads with charts visible
- [ ] Can create a family
- [ ] Can invite family members
- [ ] Export PDF button downloads a PDF file
- [ ] Export CSV button downloads a CSV file
- [ ] Charts show real data (create some devices/alerts to test)
- [ ] Family page shows member list
- [ ] No console errors in browser (F12)
- [ ] Server starts without errors
- [ ] All API endpoints return 200 (not 500)

---

## Performance Tips

### For Best Chart Performance:
```javascript
// Charts auto-load on dashboard
// To manually refresh charts:
await refreshCharts();
```

### For Large Exports:
```
PDF exports are limited to 50 alerts (performance)
CSV exports include ALL alerts (unlimited)

For large datasets, use CSV
```

---

## Database Indexes (Optional Performance Boost)

Add these indexes for better performance:

```javascript
// MongoDB shell or Compass
db.devices.createIndex({ "family_id": 1, "user_id": 1 })
db.devices.createIndex({ "user_id": 1, "groups": 1 })
db.alerts.createIndex({ "user_id": 1, "created_at": -1 })
db.alerts.createIndex({ "family_id": 1, "created_at": -1 })
db.audit_logs.createIndex({ "user_id": 1, "created_at": -1 })
db.family_members.createIndex({ "user_id": 1 })
db.family_members.createIndex({ "family_id": 1 })
```

---

## 🎉 You're Ready!

All new features are installed and ready to use!

**What you can do now:**
1. ✅ View beautiful analytics charts
2. ✅ Create and manage families
3. ✅ Export professional PDF reports
4. ✅ Export CSV data for analysis
5. ✅ Organize devices with groups
6. ✅ Track all actions with audit logs

**Ready to launch!** 🚀

---

## Need Help?

Check these files for more info:
- `FEATURES_ADDED_TODAY.md` - Complete feature documentation
- `TODO_AND_ROADMAP.md` - Future roadmap
- `README.md` - General project info
- `API_KEYS_SETUP.md` - Stripe/Twilio setup

**Happy building!** 💙
