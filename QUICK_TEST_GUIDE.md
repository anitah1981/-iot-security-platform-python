# 🧪 Quick Testing Guide - Step by Step

**Purpose:** Test all features after digest removal  
**Time Required:** 30-45 minutes

---

## 🚀 **Before You Start**

1. **Make sure your server is running:**
   ```bash
   # In your terminal, you should see:
   # Uvicorn running on http://127.0.0.1:8000
   ```

2. **Open your browser:**
   - Go to: `http://localhost:8000`
   - Make sure you're logged in

3. **Open Browser Developer Tools:**
   - Press `F12` or `Ctrl+Shift+I`
   - Go to "Console" tab
   - Watch for any errors (red messages)

---

## ✅ **Test 1: Quiet Hours (5 minutes)**

### Step 1: Navigate to Settings
1. Click **Settings** in the sidebar (or go to `/settings`)
2. Scroll down to **"🔔 Notification Preferences"** section

### Step 2: Enable Quiet Hours
1. Find **"🌙 Quiet Hours"** section
2. Toggle **"Quiet Hours Enabled"** to ON
3. Time pickers should appear:
   - **Start Time:** Should default to `22:00`
   - **End Time:** Should default to `07:00`
4. Change times if needed (e.g., `23:00` to `06:00`)
5. Click **"Save Notification Preferences"** button
6. Wait for success message

### Step 3: Verify Settings Persist
1. Refresh the page (`F5` or `Ctrl+R`)
2. Scroll back to Quiet Hours section
3. ✅ **Check:** Toggle should still be ON
4. ✅ **Check:** Times should match what you set

### Step 4: Test Quiet Hours Logic
**Note:** This requires creating an alert. You can:
- Use the API to create a test alert, OR
- Wait until a real alert is generated

**To test via API:**
```bash
# Create a non-critical alert (should be suppressed during quiet hours)
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "YOUR_DEVICE_ID",
    "message": "Test alert - should be suppressed",
    "severity": "medium",
    "type": "system"
  }'
```

**Expected:**
- If current time is within quiet hours → Alert suppressed (no notification sent)
- If current time is outside quiet hours → Alert sent normally
- Critical alerts → Always sent (bypass quiet hours)

### ✅ **Test 1 Checklist:**
- [ ] Quiet Hours section visible
- [ ] Toggle works
- [ ] Time pickers appear when enabled
- [ ] Settings save successfully
- [ ] Settings persist after refresh
- [ ] No digest section visible (removed)

---

## ✅ **Test 2: Device Grouping (10 minutes)**

### Step 1: Open Group Management
1. Go to **Dashboard** (`/dashboard`)
2. Make sure you're on **"Devices & Alerts"** tab
3. Click **"📁 Manage Groups"** button (top right of device table)

### Step 2: Create a Group
1. Modal should open
2. Click **"+ Create New Group"** button
3. Fill in the form:
   - **Group Name:** "Test Group" (or any name)
   - **Description:** "Testing device grouping"
   - **Color:** Pick any color
4. Click **"Create Group"**
5. ✅ **Check:** Group appears in the list below

### Step 3: Assign Device to Group

**Option A: From Group Management Modal (Easiest)**
1. In the group management modal, find your test group
2. Look for the **"Devices in Group"** section
3. You'll see a dropdown that says **"Add device..."**
4. Click the dropdown and select a device
5. ✅ **Check:** Device appears in the group's device list as a badge
6. ✅ **Check:** You can remove a device by clicking the "×" button on the badge

**Option B: From Device Detail Panel**
1. Close the group management modal
2. Click on any device row in the device table to open device details
3. Scroll down to the **"Groups"** section
4. You'll see a dropdown that says **"Add to group..."**
5. Select a group from the dropdown
6. ✅ **Check:** Device is added to the group
7. ✅ **Check:** Group badge appears in the Groups section
8. ✅ **Check:** You can remove a device from a group by clicking "×" on the badge

### Step 4: Filter by Group
1. Look for **"Filter by Group"** dropdown (above device table)
2. Select your test group
3. ✅ **Check:** Only devices in that group should show
4. Select **"All Groups"**
5. ✅ **Check:** All devices should show again

### Step 5: Check Groups Column
1. Look at the device table
2. ✅ **Check:** There should be a **"Groups"** column
3. ✅ **Check:** Devices with groups show colored badges
4. ✅ **Check:** Devices without groups show "No groups"

### Step 6: Delete Group
1. Click **"📁 Manage Groups"** again
2. Find your test group
3. Click **"Delete"** button
4. Confirm deletion
5. ✅ **Check:** Group removed from list
6. ✅ **Check:** Devices still exist (just ungrouped)

### ✅ **Test 2 Checklist:**
- [ ] "Manage Groups" button works
- [ ] Modal opens correctly
- [ ] Can create new group
- [ ] Group appears in list
- [ ] Can assign devices to groups
- [ ] Filter dropdown works
- [ ] Groups column shows in device table
- [ ] Can delete groups
- [ ] No console errors

---

## ✅ **Test 3: Dashboard Charts (5 minutes)**

### Step 1: Navigate to Analytics Tab
1. Go to **Dashboard** (`/dashboard`)
2. Click **"Analytics & Charts"** tab

### Step 2: Check Charts Load
1. Wait a few seconds for charts to load
2. ✅ **Check:** You should see:
   - **Device Status** pie chart (online/offline)
   - **Alert Trends** line chart
   - **Alert Severity** chart
   - **Device Type** breakdown (if applicable)

### Step 3: Test Date Range Filter
1. Look for **"Date Range"** dropdown at top
2. Select different ranges:
   - 7 days
   - 30 days
   - 90 days
   - 180 days
   - 365 days
3. ✅ **Check:** Charts update with new data
4. ✅ **Check:** Chart titles reflect selected range
5. ✅ **Check:** No errors in console

### Step 4: Test Responsiveness
1. Resize browser window
2. ✅ **Check:** Charts resize appropriately
3. ✅ **Check:** No layout breaks

### ✅ **Test 3 Checklist:**
- [ ] Analytics tab accessible
- [ ] All charts load without errors
- [ ] Date range filter works
- [ ] Charts update when range changes
- [ ] Charts are responsive
- [ ] No JavaScript errors

---

## ✅ **Test 4: Notification Channels (5 minutes)**

### Step 1: Go to Settings
1. Navigate to **Settings** (`/settings`)
2. Scroll to **"🔔 Notification Preferences"**

### Step 2: Test Email
1. Find **"Test Your Notifications"** section
2. Click **"Test Email"** button
3. ✅ **Check:** Success message appears
4. ✅ **Check:** Check your email inbox (may take 10-30 seconds)
5. ✅ **Check:** Email has nice HTML formatting

### Step 3: Test Other Channels (if enabled)
- **SMS:** Click "Test SMS" (requires phone number configured)
- **WhatsApp:** Click "Test WhatsApp" (requires WhatsApp number)
- **Voice:** Click "Test Voice Call" (requires phone number)

**Note:** If channels are disabled, you should see appropriate error messages.

### ✅ **Test 4 Checklist:**
- [ ] Test buttons visible
- [ ] Email test works
- [ ] Other channels work (if enabled)
- [ ] Error messages clear (if disabled)
- [ ] Notifications received

---

## ✅ **Test 5: General UI/UX (5 minutes)**

### Step 1: Navigation
1. Click through all sidebar links:
   - Dashboard
   - Settings
   - (Any other pages)
2. ✅ **Check:** All links work
3. ✅ **Check:** Pages load correctly

### Step 2: Responsive Design
1. Resize browser window to mobile size (narrow)
2. ✅ **Check:** Sidebar collapses or adapts
3. ✅ **Check:** Content is readable
4. ✅ **Check:** Buttons are clickable

### Step 3: Error Handling
1. Try to trigger errors (e.g., invalid form submission)
2. ✅ **Check:** Error messages are clear
3. ✅ **Check:** User knows what went wrong

### Step 4: Console Check
1. Open Developer Tools (`F12`)
2. Go to **Console** tab
3. ✅ **Check:** No red errors
4. ✅ **Check:** No warnings (yellow) that indicate problems

### ✅ **Test 5 Checklist:**
- [ ] All navigation works
- [ ] Responsive design works
- [ ] Error messages helpful
- [ ] No console errors
- [ ] UI looks polished

---

## 🐛 **If You Find Issues**

### Document the Issue:
1. **What you were doing:** (e.g., "Creating a device group")
2. **What happened:** (e.g., "Modal didn't open")
3. **What you expected:** (e.g., "Modal should open")
4. **Screenshot:** (if possible)
5. **Console errors:** (copy any red error messages)

### Report Format:
```
**Issue #1: [Brief Description]**
- **Location:** Settings page / Quiet Hours
- **Steps to Reproduce:**
  1. Go to Settings
  2. Enable quiet hours
  3. [What happens]
- **Expected:** [What should happen]
- **Actual:** [What actually happened]
- **Console Errors:** [Any errors]
```

---

## ✅ **Testing Complete!**

Once you've completed all tests:
1. Review the checklist
2. Document any issues found
3. Note any improvements needed
4. Decide if ready to move to next feature

---

## 🚀 **Next Steps After Testing**

If everything works:
- ✅ Move to **Option B.1: Audit Logs** (3-4 days)

If issues found:
- 🔧 Fix critical issues first
- 🔧 Fix medium issues
- 🔧 Polish minor issues
- ✅ Then move to next feature

---

**Happy Testing! 🎉**
