# Testing Guide for Option 1 New Features

**Date:** January 26, 2026  
**Features to Test:** Dashboard Charts, Device Grouping, Enhanced Notifications

---

## 🚀 Quick Start

1. **Ensure server is running:**
   ```bash
   cd c:\IoT-security-app-python
   uvicorn main:app --reload --port 8000
   ```

2. **Open browser:** http://localhost:8000/dashboard

3. **Login** with your credentials

---

## 📊 Test 1: Dashboard Charts & Analytics

### Steps:
1. Navigate to **Dashboard** (http://localhost:8000/dashboard)
2. Click on the **"📊 Analytics & Charts"** tab
3. Verify the following:

#### ✅ What to Check:
- [ ] **Date Range Filter** appears at the top
  - Dropdown shows: 7, 30, 90, 180, 365 days
  - Default is 30 days
  
- [ ] **Health Metrics Cards** display:
  - System Health Score (percentage)
  - Device Uptime (percentage)
  - Alerts (24h count)
  
- [ ] **Top Alerting Devices** table shows:
  - Device names
  - Device types
  - Alert counts
  
- [ ] **Charts Render:**
  - Device Status Chart (pie/doughnut) - shows online/offline/error
  - Device Type Chart (pie/doughnut) - shows breakdown by type
  - Alert Trends Chart (line) - shows alerts over time
  - Alert Severity Chart (bar) - shows low/medium/high/critical
  
- [ ] **Date Range Works:**
  - Change dropdown to "Last 7 days"
  - Charts should update
  - Change to "Last 90 days"
  - Charts should update again
  
- [ ] **Refresh Button:**
  - Click "🔄 Refresh" button
  - Charts should reload

### Expected Results:
- All charts should render without errors
- Data should be accurate based on your devices/alerts
- Charts should be responsive and look good
- No console errors in browser (F12 → Console)

---

## 📁 Test 2: Device Grouping

### Steps:
1. On the **Dashboard**, go to **"📱 Devices & Alerts"** tab
2. Look for the **"Filter by Group"** dropdown above the device table
3. Click **"📁 Manage Groups"** button

#### ✅ What to Check:

**Group Management Modal:**
- [ ] Modal opens when clicking "Manage Groups"
- [ ] Shows existing groups (if any)
- [ ] "Create New Group" button is visible

**Create Group:**
- [ ] Click "Create New Group"
- [ ] Form appears with:
  - Group Name field
  - Description field
  - Color picker
- [ ] Fill in:
  - Name: "Living Room"
  - Description: "Devices in living room"
  - Color: Pick a color
- [ ] Click "Create"
- [ ] Group appears in list
- [ ] Success message shows

**Group Filter:**
- [ ] Close modal
- [ ] Check "Filter by Group" dropdown
- [ ] Your new group should appear
- [ ] Select the group
- [ ] Device table should filter (if devices are in group)

**Device Table:**
- [ ] Check device table has "Groups" column
- [ ] Groups should show as colored badges
- [ ] Devices without groups show "No groups"

**Add Device to Group:**
- [ ] Open a device detail panel (click device row)
- [ ] Look for group assignment options
- [ ] Or use API to add device to group

**Delete Group:**
- [ ] Open "Manage Groups" again
- [ ] Click "Delete" on test group
- [ ] Confirm deletion
- [ ] Group should disappear

### Expected Results:
- Groups can be created, viewed, and deleted
- Group filter works on device table
- Groups display as badges in device table
- No errors in console

---

## 🔔 Test 3: Enhanced Notifications

### Steps:
1. Navigate to **Settings** (http://localhost:8000/settings)
2. Scroll to **"🔔 Notification Preferences"** section
3. Look for new sections

#### ✅ What to Check:

**Quiet Hours:**
- [ ] "🌙 Quiet Hours" section is visible
- [ ] Toggle switch for "Quiet Hours Enabled"
- [ ] When enabled, time pickers appear:
  - Start Time (default: 22:00)
  - End Time (default: 07:00)
- [ ] Change times and save
- [ ] Settings persist after page reload

**Notification Digest:**
- [ ] "📬 Notification Digest" section is visible
- [ ] Toggle switch for "Digest Enabled"
- [ ] When enabled, settings appear:
  - Frequency dropdown (Daily/Weekly)
  - Send Time picker (default: 09:00)
- [ ] Change settings and save
- [ ] Settings persist after page reload

**Save Preferences:**
- [ ] Enable quiet hours
- [ ] Set times: 22:00 - 07:00
- [ ] Enable digest
- [ ] Set frequency: Daily
- [ ] Set time: 09:00
- [ ] Click "Save Notification Preferences"
- [ ] Success message appears
- [ ] Reload page
- [ ] Settings should be preserved

**Test Quiet Hours Logic:**
- [ ] Create a test alert (non-critical)
- [ ] If current time is within quiet hours (22:00-07:00)
- [ ] Alert should be queued for digest (not sent immediately)
- [ ] Critical alerts should still be sent

### Expected Results:
- All UI elements render correctly
- Settings save and load properly
- Quiet hours logic works (check notification service logs)
- No console errors

---

## 🧪 API Testing (Optional)

If you want to test the APIs directly:

### Analytics Endpoints:
```bash
# Get device stats
curl http://localhost:8000/api/analytics/devices/stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get alert trends (30 days)
curl http://localhost:8000/api/analytics/alerts/trends?days=30 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get health metrics
curl http://localhost:8000/api/analytics/health/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Groups Endpoints:
```bash
# List groups
curl http://localhost:8000/api/groups \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create group
curl -X POST http://localhost:8000/api/groups \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Group", "color": "#3b82f6"}'
```

### Notification Preferences:
```bash
# Get preferences
curl http://localhost:8000/api/notification-preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update preferences
curl -X PUT http://localhost:8000/api/notification-preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email_enabled": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00",
    "digest_enabled": true,
    "digest_frequency": "daily",
    "digest_time": "09:00"
  }'
```

---

## 🐛 Troubleshooting

### Charts Not Showing:
1. **Hard refresh browser:** `Ctrl + Shift + R`
2. **Check browser console (F12):**
   - Look for JavaScript errors
   - Check if Chart.js loaded: `typeof Chart !== 'undefined'`
3. **Verify API responses:**
   - Open Network tab (F12)
   - Check `/api/analytics/*` requests
   - Should return 200 status
4. **Check data:**
   - You need devices/alerts for charts to show data
   - Create some test devices if needed

### Groups Not Working:
1. **Check API endpoint:**
   - Verify `/api/groups` returns 200
   - Check browser console for errors
2. **Database:**
   - Ensure MongoDB is connected
   - Check `device_groups` collection exists
3. **Permissions:**
   - Make sure you're logged in
   - Token should be valid

### Notification Settings Not Saving:
1. **Check form validation:**
   - All required fields filled?
   - Phone numbers in E.164 format if SMS enabled
2. **Check API response:**
   - Network tab should show 200 status
   - Response should include updated preferences
3. **Database:**
   - Check `notification_preferences` collection
   - Verify document was updated

---

## ✅ Success Criteria

All features are working correctly if:

1. **Charts:**
   - ✅ All 4 charts render
   - ✅ Date range filter works
   - ✅ Data is accurate
   - ✅ No console errors

2. **Groups:**
   - ✅ Can create groups
   - ✅ Groups appear in filter
   - ✅ Groups show in device table
   - ✅ Can delete groups

3. **Notifications:**
   - ✅ Quiet hours toggle works
   - ✅ Time pickers appear when enabled
   - ✅ Digest settings work
   - ✅ Settings save and persist

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________

Dashboard Charts:
[ ] Date range filter works
[ ] All charts render
[ ] Data is accurate
[ ] No errors

Device Grouping:
[ ] Can create groups
[ ] Groups filter works
[ ] Groups display correctly
[ ] Can delete groups

Enhanced Notifications:
[ ] Quiet hours UI works
[ ] Digest settings work
[ ] Settings save correctly
[ ] Settings persist

Overall: [ ] PASS [ ] FAIL
Notes: ________________________________
```

---

**Happy Testing! 🚀**
