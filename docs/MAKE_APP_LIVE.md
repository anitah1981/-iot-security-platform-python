# How to Make the Web App Live

This guide gets your IoT Security web app from **localhost** to a **public URL** so anyone can use it.

---

## Do it all (one script + follow steps)

1. **Run the deployment helper** (generates a JWT secret and prints step-by-step instructions):
   ```bash
   python scripts/do_it_all_deploy.py
   ```
2. **Follow the printed steps** – MongoDB Atlas → push to GitHub → Railway (or Render) → add variables (copy the generated `JWT_SECRET` into your host’s Variables).
3. **Generate domain** in Railway → set `APP_BASE_URL` and `CORS_ORIGINS` to that URL → redeploy if needed.

The script prints the exact variables to set and links to this doc. For more detail, see below.

---

## What You Need First

1. **MongoDB** – Your app stores data in MongoDB. For production, use **MongoDB Atlas** (free tier):
   - Go to https://www.mongodb.com/cloud/atlas
   - Create an account → Create a free cluster
   - Create a database user and get the **connection string** (e.g. `mongodb+srv://user:pass@cluster.mongodb.net/iot_security`)

2. **GitHub** – Your code should be in a GitHub repo so the hosting platform can deploy from it.

3. **Secrets** – You’ll set these in the host’s dashboard (never commit them):
   - `JWT_SECRET` – Run `python scripts/generate_secrets.py` or use a long random string (32+ chars)
   - Gmail App Password (if you want email) – see docs/API_KEYS_SETUP.md

---

## Fastest Option: Railway (~10 minutes)

1. **Sign up**  
   Go to https://railway.app and sign in with GitHub.

2. **New project**  
   Click **New Project** → **Deploy from GitHub repo** → select your `IoT-security-app-python` repo.

3. **Environment variables**  
   In the project, open **Variables** and add:

   | Variable        | Example / value |
   |-----------------|-----------------|
   | `MONGO_URI`     | Your Atlas connection string |
   | `JWT_SECRET`    | Long random string (32+ chars) |
   | `PORT`          | `8000` (Railway may set this automatically) |
   | `CORS_ORIGINS`  | Your app URL, e.g. `https://your-app.up.railway.app` |
   | `APP_BASE_URL`  | Same as CORS, e.g. `https://your-app.up.railway.app` |
   | `APP_ENV`       | `production` |

   Optional (for email): `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` (see .env.example and docs).

4. **Deploy**  
   Railway builds and runs your app. After the build finishes, open **Settings** → **Networking** → **Generate domain** to get a URL like `https://your-app.up.railway.app`.

5. **Set CORS and APP_BASE_URL**  
   Set `CORS_ORIGINS` and `APP_BASE_URL` to that exact URL (with `https://`), then redeploy if needed.

6. **Test**  
   Visit the URL → you should see the landing/login page. Try signup and login.

**Cost:** Railway has a free trial; then roughly $5–20/month depending on usage.

---

## Alternative: Render

1. Go to https://render.com and sign in with GitHub.
2. **New** → **Web Service** → connect your repo.
3. **Build:** `pip install -r requirements.txt`  
   **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add the same variables as above. Set `PORT=10000` (or leave Render’s default).
5. Set `CORS_ORIGINS` and `APP_BASE_URL` to your Render URL (e.g. `https://your-app.onrender.com`).

**Cost:** Free tier available; paid tier around $7+/month for production.

---

## After Going Live

- **Custom domain (optional):** See **Custom domain (your own URL)** below for linking a purchased domain to Railway.
- **Mobile app:** In `mobile/app.json` (or your config), set the API URL to your live URL so the app talks to the same backend.
- **Device agent / discovery:** In the agent’s `.env`, set `API_BASE_URL` to your live URL.

---

## Custom domain (your own URL)

To use a domain you purchased (e.g. proalert.com) instead of the Railway URL:

1. **Railway:** Open your service, **Settings**, **Networking**, **Add custom domain**. Enter your domain (e.g. yourdomain.com or app.yourdomain.com). Railway will show the DNS target to use.

2. **DNS at your registrar:** Where you bought the domain (GoDaddy, Namecheap, Cloudflare, etc.), add a **CNAME** record pointing your domain (or subdomain) to the Railway domain Railway showed you. For root domains (yourdomain.com), some providers need CNAME flattening or an A/ALIAS record; use the value Railway displays.

3. **Railway Variables:** Set `APP_BASE_URL` and `CORS_ORIGINS` to `https://yourdomain.com` (no trailing slash). If you use both root and www, set CORS to both: `https://yourdomain.com,https://www.yourdomain.com`. Redeploy.

4. **Wait:** DNS can take minutes to 48 hours; SSL on Railway is automatic and may take up to an hour after DNS is correct. Then open https://yourdomain.com and test login.

See `docs/CUSTOM_DOMAIN_RAILWAY.md` for a full checklist and root vs www notes.

---

## Keeping local and live in sync (same version on your domain)

**Single source of truth:** The code in your **GitHub repo**, **`main` branch**, is what Railway deploys. Whatever is pushed to `main` is what gets built and runs on your custom domain. There is only one codebase; local and live stay consistent when you follow this flow.

**Workflow:**

1. **Work locally** on the same repo (your current folder). Use branch **`main`** for everything that should go live.
2. **Commit** your changes: `git add -A` then `git commit -m "Your message"`.
3. **Push** to GitHub: `git push`. That updates `origin/main`.
4. **Railway** deploys from this repo. If auto-deploy is on, it builds from the latest push to `main`; that build is what runs at **your domain** (e.g. https://yourdomain.com).
5. **Config is per environment:**  
   - **Local:** Use `.env` with `APP_BASE_URL=http://localhost:8000`, `CORS_ORIGINS=http://localhost:8000` so the app works on your machine.  
   - **Live (Railway):** Use Railway **Variables** with `APP_BASE_URL=https://yourdomain.com`, `CORS_ORIGINS=https://yourdomain.com` (your real domain).  
   The **code** is the same; only these variables change by environment.

**Quick check that you’re in sync:**

- Run `git status` → should be clean (no uncommitted changes) when you want “live” to match your current code.
- Run `git log -1 --oneline` → note the commit hash (e.g. `32690d5`).
- In **Railway** → your service → **Deployments**: the latest successful deployment should show the **same commit** and message. That is the version running on your domain.

**Summary:** Develop on `main`, push to GitHub; Railway runs that same code on your domain. Keep `.env` for local and Railway Variables for production so changes stay consistent and only config differs by environment.

---

## More Detail

- **Full deployment options:** `docs/DEPLOYMENT.md`
- **Checklist:** `DEPLOYMENT_CHECKLIST.md`
- **Security:** `docs/SECURITY_CHECKLIST.md`
- **Custom domain on Railway:** `docs/CUSTOM_DOMAIN_RAILWAY.md`
