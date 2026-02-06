# MongoDB Atlas Connection String - Exact Steps

## Step 4: Edit Your Connection String

When you copy the connection string from MongoDB Atlas, it looks like this:

```
mongodb+srv://IoTAppPython:<password>@cluster0.xxxxx.mongodb.net/
```

**You need to make TWO changes:**

---

## Change 1: Replace `<password>`

Replace `<password>` with the **actual password** you created for the user `IoTAppPython`.

**Example:**
- If your password is `MySecurePass123!`
- Change: `mongodb+srv://IoTAppPython:<password>@cluster0.xxxxx.mongodb.net/`
- To: `mongodb+srv://IoTAppPython:MySecurePass123!@cluster0.xxxxx.mongodb.net/`

**Important:** If your password has special characters (like `!`, `@`, `#`, etc.), you might need to URL-encode them:
- `!` becomes `%21`
- `@` becomes `%40`
- `#` becomes `%23`
- Or just try the password as-is first - it usually works.

---

## Change 2: Add Database Name

Change the ending from `/` to `/iot_security?retryWrites=true&w=majority`

**Example:**
- Before: `mongodb+srv://IoTAppPython:MySecurePass123!@cluster0.xxxxx.mongodb.net/`
- After: `mongodb+srv://IoTAppPython:MySecurePass123!@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority`

---

## Complete Example

**What MongoDB Atlas gives you:**
```
mongodb+srv://IoTAppPython:<password>@cluster0.abc123.mongodb.net/
```

**What you need (after editing):**
```
mongodb+srv://IoTAppPython:YourActualPassword@cluster0.abc123.mongodb.net/iot_security?retryWrites=true&w=majority
```

---

## Test Your Connection String

Once you have your edited connection string, test it:

**PowerShell (Windows):**
```powershell
cd c:\IoT-security-app-python
$env:MONGO_URI="mongodb+srv://IoTAppPython:YourPassword@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority"
python scripts\test_mongodb_connection.py
```

**Or use single quotes (PowerShell):**
```powershell
$env:MONGO_URI='mongodb+srv://IoTAppPython:YourPassword@cluster0.xxxxx.mongodb.net/iot_security?retryWrites=true&w=majority'
python scripts\test_mongodb_connection.py
```

**Important:** In PowerShell, you MUST use `$env:MONGO_URI=` and wrap the string in quotes because the `&` character is special. Single quotes work too.

(Replace `YourPassword` and `cluster0.xxxxx` with your actual values)

Should print: `✓ Connection successful!`

---

## Use in Railway

Copy your **final edited connection string** and paste it as the `MONGO_URI` value in Railway Variables.
