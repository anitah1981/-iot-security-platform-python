# Fix "Application failed to respond" / 502 on Railway

Your app returns 502 because it **crashes on startup**—usually from a missing or wrong `MONGO_URI`.

---

## Step 1: Open your project in Railway

1. Go to **https://railway.app** and sign in.
2. Click your project (**iot-security-platform-python**).
3. Click the service that runs your app.

---

## Step 2: Open the Variables tab

1. On the right, click the **Variables** tab.
2. You’ll see your environment variables (values are hidden for secrets).

---

## Step 3: Add or fix these variables

Add or update these. If a variable exists, edit it; if not, use **New Variable** or **Add Variable**.

| Variable        | Value                                                                 |
|-----------------|-----------------------------------------------------------------------|
| `MONGO_URI`     | Your MongoDB Atlas connection string (e.g. `mongodb+srv://user:pass@cluster.mongodb.net/iot_security?retryWrites=true&w=majority`) |
| `JWT_SECRET`    | Long random string (32+ chars). Run `python scripts/do_it_all_deploy.py` to generate one. |
| `APP_ENV`       | `production`                                                          |
| `APP_BASE_URL`  | Your Railway URL (e.g. `https://iot-security-platform-python-production-e18f.up.railway.app`) |
| `CORS_ORIGINS`  | Same as APP_BASE_URL (e.g. `https://iot-security-platform-python-production-e18f.up.railway.app`) |
| `PORT`          | `8000` (Railway may set this automatically)                           |

**Important:** `MONGO_URI` must be your **MongoDB Atlas** connection string, not `mongodb://localhost:27017`.

---

## Step 4: Get your MongoDB Atlas connection string

If you don’t have it:

1. Go to **https://cloud.mongodb.com** and sign in.
2. Open **Database** → **Connect** on your cluster.
3. Choose **Drivers** → **Python**.
4. Copy the connection string.
5. Replace `<password>` with your real password.
6. Add the database name: change `/` at the end to `/iot_security?retryWrites=true&w=majority`.

Example:  
`mongodb+srv://iotapp:YourPassword123@cluster0.abc123.mongodb.net/iot_security?retryWrites=true&w=majority`

---

## Step 5: Save and redeploy

1. Click **Save** or **Update** on the Variables section.
2. Railway usually redeploys automatically.
3. Wait 1–2 minutes.

---

## Step 6: Match the Target Port (CRITICAL for 502 fix)

If your app starts but you still get 502:

1. Go to **Settings** → **Networking** → **Public Networking**.
2. Find your domain (e.g. `iot-security-platform-python-production-e18f.up.railway.app`).
3. Click the **edit (pencil) icon** next to the domain.
4. Set **Target Port** to match what your app listens on.
   - Check Deploy Logs for `[START] Binding to 0.0.0.0:XXXX` or `Uvicorn running on http://0.0.0.0:XXXX`
   - Use that port (often **8000**).
5. Save and try again.

Railway’s proxy must connect to the same port your app uses. If they don’t match, you get 502.

---

## Step 7: Check Deploy Logs

1. Open the **Deployments** tab.
2. Click the latest deployment.
3. Open **Deploy Logs** (next to HTTP Logs).

You should see:

- `[START] Binding to 0.0.0.0:8000` (or whatever port)
- `Connected to MongoDB: iot_security`
- `Backend ready`
- `Application startup complete`

If you see `[FATAL] MONGO_URI is not set or still points to localhost`, add or fix `MONGO_URI` in Variables.

---

## Step 8: Test your app

Open your Railway URL in a browser. You should see the landing or login page instead of “Application failed to respond”.

---

## Still failing?

- In **Deploy Logs**, look for error messages and stack traces.
- Check that `MONGO_URI` has no typos and that the password is correct.
- Make sure MongoDB Atlas **Network Access** allows `0.0.0.0/0` (or your Railway IP), and that your database user exists.
