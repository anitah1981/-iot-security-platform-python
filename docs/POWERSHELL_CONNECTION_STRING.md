# PowerShell - Setting MongoDB Connection String

## The Problem

PowerShell treats `&` as a special character (command separator), so when your MongoDB connection string has `retryWrites=true&w=majority`, PowerShell tries to interpret it as a command.

**Error you see:**
```
ParserError: The ampersand (&) character is not allowed.
```

---

## Solution: Use Quotes and `$env:`

In PowerShell, you **must** wrap the connection string in quotes and use `$env:MONGO_URI=`:

### Method 1: Double Quotes

```powershell
$env:MONGO_URI="mongodb+srv://IoTAppPython:YourPassword@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority"
python scripts\test_mongodb_connection.py
```

### Method 2: Single Quotes (also works)

```powershell
$env:MONGO_URI='mongodb+srv://IoTAppPython:YourPassword@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority'
python scripts\test_mongodb_connection.py
```

### Method 3: Use the Helper Script

```powershell
.\scripts\test_mongodb_simple.ps1
```

This script will prompt you to paste your connection string and handle the quoting automatically.

---

## Your Connection String Format

Your connection string should look like this (replace with your actual values):

```
mongodb+srv://IoTAppPython:YourPassword@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority
```

Where:
- `IoTAppPython` = your database username
- `YourPassword` = your database password
- `cluster0.xxxxx` = your cluster name (from MongoDB Atlas)
- `/iot_security` = the database name (required)
- `?retryWrites=true&w=majority` = connection options (required)

---

## Test It

```powershell
cd c:\IoT-security-app-python
$env:MONGO_URI="mongodb+srv://IoTAppPython:YourPassword@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority"
python scripts\test_mongodb_connection.py
```

Should print: `✓ Connection successful!`

---

## For Railway Deployment

When you add `MONGO_URI` in Railway Variables, paste the connection string **without quotes** - Railway handles it automatically:

```
mongodb+srv://IoTAppPython:YourPassword@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority
```
