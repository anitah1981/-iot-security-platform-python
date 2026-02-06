# MongoDB Atlas Setup - Step by Step

## Important: You Don't Create a Database Manually

In MongoDB Atlas, **the database is created automatically** when your app first connects. You just need to:
1. Create a **database user** (so your app can connect)
2. Allow **network access** (so Railway can reach it)
3. Get the **connection string** (with the database name in it)

---

## Step 1: Create Database User

1. **In MongoDB Atlas**, look at the left sidebar
2. Click **"Database Access"** (under "Security" section)
3. Click **"Add New Database User"** button (green button, top right)
4. Fill in:
   - **Username**: `iotapp` (or any name you want)
   - **Password**: Click **"Autogenerate Secure Password"** → **Copy** the password (save it!)
   - **Database User Privileges**: Select **"Atlas admin"** (or "Read and write to any database")
5. Click **"Add User"**

**Done!** You now have a user that can access your databases.

---

## Step 2: Allow Network Access

1. In the left sidebar, click **"Network Access"** (under "Security")
2. Click **"Add IP Address"** button (green button, top right)
3. Click **"Allow Access from Anywhere"** (this adds `0.0.0.0/0`)
   - This allows Railway/Render to connect
4. Click **"Confirm"**

**Done!** Your cluster can now accept connections from anywhere.

---

## Step 3: Get Connection String

1. In the left sidebar, click **"Database"** (top of the list)
2. Click **"Connect"** button on your cluster
3. Choose **"Drivers"** (not "MongoDB Compass" or "MongoDB Shell")
4. Select:
   - **Driver**: `Python`
   - **Version**: `3.12 or later`
5. **Copy the connection string** (looks like: `mongodb+srv://iotapp:<password>@cluster0.xxxxx.mongodb.net/`)
6. **Edit it**:
   - Replace `<password>` with the password you copied in Step 1
   - Change the ending from `/` to `/iot_security?retryWrites=true&w=majority`
   - Final example: `mongodb+srv://iotapp:YourPassword123@cluster0.abc123.mongodb.net/iot_security?retryWrites=true&w=majority`

**Done!** This is your `MONGO_URI` - use it in Railway.

---

## Step 4: Test Connection (Optional)

```bash
cd c:\IoT-security-app-python
MONGO_URI=your-connection-string python scripts\test_mongodb_connection.py
```

Should print: `✓ Connection successful!`

---

## What Happens Next?

When your app connects to MongoDB Atlas using this connection string:
- MongoDB **automatically creates** the `iot_security` database
- It **automatically creates** collections (`users`, `devices`, `alerts`, etc.) as your app uses them
- You don't need to create anything manually!

---

## Summary

**You don't create a database** - MongoDB creates it automatically when your app connects.

**What you DO create:**
1. ✅ Database **user** (Database Access)
2. ✅ Network **access** (Network Access)
3. ✅ Get connection **string** (Database → Connect → Drivers)

Then use that connection string in Railway!
