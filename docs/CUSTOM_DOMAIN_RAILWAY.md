# Link Your Purchased Domain to the App (Railway)

Use your own domain (e.g. proalert.com) instead of the default Railway URL (your-app.up.railway.app). Railway handles HTTPS (SSL) for you.

---

## 1. Add the custom domain in Railway

1. Open **Railway** and go to your project and your service (the web app).
2. Go to **Settings** then **Networking** (or **Public Networking**).
3. Under **Domains**, click **Add custom domain** (or **Custom Domain**).
4. Enter your domain:
   - Root domain: yourdomain.com
   - Or a subdomain: app.yourdomain.com or www.yourdomain.com
5. Save. Railway will show you the **DNS target** to use (e.g. your-app.up.railway.app or a specific CNAME target).

---

## 2. Point your domain at Railway (DNS)

At the place where you **bought the domain** (e.g. GoDaddy, Namecheap, Google Domains, Cloudflare):

- **If you use a subdomain** (e.g. app.yourdomain.com):
  - Add a **CNAME** record:
    - Name/Host: app (or whatever subdomain you chose)
    - Value/Target: the Railway domain Railway gave you (e.g. your-app-production.up.railway.app)
    - TTL: 300 or default

- **If you use the root domain** (yourdomain.com with no www): see **Root domain (yourdomain.com) – detailed steps** below.

Railway's **Domains** screen in the dashboard will show the exact record type and value to use for your domain.

---

## Root domain (yourdomain.com) – detailed steps

The **root** of your domain is the bare name with no subdomain: `yourdomain.com` (not `www.yourdomain.com` or `app.yourdomain.com`). Standard DNS does **not** allow a CNAME record on the root. So you have two ways to make `https://yourdomain.com` work with Railway.

---

### Why CNAME on the root is a problem

- A **CNAME** record says “this name is an alias for another name” (e.g. “yourdomain.com is an alias for your-app.up.railway.app”).
- DNS rules say the **root** of a domain (the “apex”) cannot be a CNAME, because other important records (e.g. MX for email) must live at the root.
- So for the root you must use either **CNAME flattening** (your provider resolves the CNAME for you and returns A/AAAA) or an **A** / **ALIAS** / **ANAME** record that points to Railway.

---

### Option A: CNAME flattening (e.g. Cloudflare)

**What it is:** Your DNS provider (e.g. Cloudflare) lets you add something that *looks* like a CNAME for the root. They resolve the target and serve A/AAAA records to the rest of the internet, so the root “points” to Railway without breaking DNS rules.

**When to use it:** Your DNS is at a provider that supports CNAME flattening (Cloudflare does; many others do not).

**Steps:**

1. **Use Cloudflare (or a similar provider) for DNS**
   - If your domain is not on Cloudflare yet: at [cloudflare.com](https://www.cloudflare.com), add your domain and change your registrar’s **nameservers** to the ones Cloudflare gives you (e.g. `ada.ns.cloudflare.com` and `bob.ns.cloudflare.com`). Your registrar has a “Nameservers” or “DNS” section where you paste these.
   - If you already use Cloudflare, skip to step 2.

2. **In Railway: add only the root**
   - Railway → your service → **Settings** → **Networking** → **Add custom domain**.
   - Enter **yourdomain.com** (no `www`). Railway will show a target, e.g. `your-app.up.railway.app` or a longer CNAME target.

3. **In Cloudflare: create the root record**
   - Go to **DNS** → **Records**.
   - **Add record:**
     - **Type:** `CNAME` (Cloudflare will flatten it for the root).
     - **Name:** `@` (the `@` means “root” in most dashboards).
     - **Target:** the exact value Railway showed you (e.g. `your-app.up.railway.app`). Do not add `https://` or a trailing dot unless Railway shows one.
     - **Proxy status:** Orange cloud (Proxied) is fine; grey (DNS only) is also fine.
     - **TTL:** Auto or 300.
   - Save.

4. **Wait**
   - DNS: usually 5–15 minutes; sometimes up to 48 hours.
   - Railway will then issue SSL for `yourdomain.com`. Give it up to about an hour after DNS is correct.

5. **App config**
   - In Railway **Variables**, set `APP_BASE_URL` and `CORS_ORIGINS` to `https://yourdomain.com` (no trailing slash), then redeploy.

**Result:** `https://yourdomain.com` goes to your app. If you also want `www.yourdomain.com`, use Option B for the www part, or add `www` in Railway and a CNAME for `www` in Cloudflare (see below).

---

### Option B: Root + www (CNAME for www, A/ALIAS for root)

**What it is:** You add **both** `yourdomain.com` and `www.yourdomain.com` in Railway. In DNS you use:
- a **CNAME** for `www` → Railway’s domain (this is always allowed), and  
- an **A** or **ALIAS/ANAME** record for the root → Railway (using the value Railway or your provider gives you).

**When to use it:** Any registrar or DNS provider; especially when CNAME flattening is not available (e.g. GoDaddy, Namecheap, Google Domains without Cloudflare).

**Steps:**

1. **In Railway: add both domains**
   - Railway → your service → **Settings** → **Networking** → **Domains**.
   - Click **Add custom domain**. Enter **yourdomain.com** (root). Note the target Railway shows (e.g. a hostname or an IP).
   - Click **Add custom domain** again. Enter **www.yourdomain.com**. Note the target (usually a CNAME like `your-app.up.railway.app`).

2. **In your DNS provider: add two records**

   **Record 1 – www (CNAME)**  
   - **Type:** CNAME  
   - **Name/Host:** `www` (or `www.yourdomain.com` depending on the provider; if it asks for “subdomain” only, use `www`).  
   - **Value/Target/Points to:** the **www** target Railway showed (e.g. `your-app.up.railway.app`).  
   - **TTL:** 300 or default.  
   - Save.

   **Record 2 – root (A or ALIAS)**  
   What you do here depends on your provider:

   - **If Railway shows an IP address for the root:**  
     - **Type:** A  
     - **Name/Host:** `@` or blank or `yourdomain.com` (whatever means “root” in your dashboard).  
     - **Value/Target:** that IP (e.g. `76.76.21.21` – use the IP Railway actually shows).  
     - **TTL:** 300 or default.

   - **If Railway shows a hostname for the root (or your provider supports ALIAS/ANAME):**  
     - **GoDaddy:** “A” record with “Points to” = hostname, or use their “Forwarding” to point root to `https://www.yourdomain.com` (then only www is on Railway; root redirects to www).  
     - **Namecheap:** “URL Redirect” or “ALIAS” if available; otherwise “A” if Railway gave an IP.  
     - **Google Domains (now Squarespace):** “Synthetic record” or “CNAME” for root if they support it; otherwise “A” with the IP Railway shows.  
     - **Cloudflare:** You can use CNAME flattening for the root (Option A) or an A record if Railway gives an IP.

   If your provider has no ALIAS and Railway did not give an IP, check Railway’s current docs for “root domain” or “apex”; they may list a fixed IP, or you can use Option A (e.g. move DNS to Cloudflare) for the root.

3. **Redirect www to root (optional but common)**
   - If you want **yourdomain.com** to be the main URL and **www.yourdomain.com** to redirect to it, you can set that in Railway if they offer “Redirect” for the www domain, or in your DNS provider (e.g. “Forwarding” in GoDaddy, “Redirect” in Cloudflare). Otherwise both URLs will work and show the same app.

4. **App config**
   - In Railway **Variables:**  
     - `APP_BASE_URL` = `https://yourdomain.com` (or `https://www.yourdomain.com` if you prefer www as main).  
     - `CORS_ORIGINS` = `https://yourdomain.com,https://www.yourdomain.com` (both, so both URLs work).  
   - Redeploy.

5. **Wait**
   - Same as Option A: wait for DNS (minutes to 48 hours) and for Railway to issue SSL (up to about an hour after DNS is correct).

**Result:** Both `https://yourdomain.com` and `https://www.yourdomain.com` hit your app. You can later add a redirect so one of them is the “main” URL if you want.

---

### Quick comparison

| Goal                         | Option A (CNAME flattening) | Option B (root + www)        |
|-----------------------------|------------------------------|------------------------------|
| Only root (yourdomain.com)  | Yes – one CNAME at root      | Yes – A/ALIAS for root       |
| Root and www both work      | Add www in Railway + CNAME   | Yes – CNAME for www, A for root |
| Best for                    | Cloudflare (or similar) users| Any provider                  |
| Needs ALIAS / flattening?    | Yes (handled by provider)    | Only for root if no IP given |

---

## 3. Update app config to use your domain

In Railway, open your service and go to **Variables**. Set:

| Variable        | Value |
|-----------------|--------|
| APP_BASE_URL    | https://yourdomain.com (or https://app.yourdomain.com, no trailing slash) |
| CORS_ORIGINS    | Same as APP_BASE_URL. If you use both root and www: https://yourdomain.com,https://www.yourdomain.com |

Then **redeploy** the service so the app uses the new URL for emails and CORS.

---

## 4. Wait for DNS and SSL

- **DNS:** Changes can take from a few minutes up to 24-48 hours. Use dnschecker.org to confirm your domain points to Railway.
- **SSL:** Railway issues HTTPS certificates automatically. It can take up to about an hour (sometimes longer) after DNS is correct. Do not remove and re-add the domain repeatedly or you may hit rate limits.

---

## 5. Optional: use both root and www

If you want both yourdomain.com and www.yourdomain.com to work:

1. In Railway, add **both** domains (root and www) in the same service Custom domains.
2. In your DNS: CNAME for www to your Railway domain; root use ALIAS/A or CNAME flattening as Railway or your provider recommends.
3. Set CORS_ORIGINS to both: https://yourdomain.com,https://www.yourdomain.com and APP_BASE_URL to the one you prefer (e.g. https://yourdomain.com).

---

## Checklist

- [ ] Custom domain added in Railway (Settings, Networking, Custom domain).
- [ ] DNS record (CNAME or A/ALIAS) set at your registrar pointing to Railway.
- [ ] APP_BASE_URL and CORS_ORIGINS in Railway Variables set to https://yourdomain.com (no trailing slash).
- [ ] Redeployed the service after changing variables.
- [ ] Waited for DNS propagation and SSL; then opened https://yourdomain.com and confirmed the app loads and login works.
- [ ] If you use Stripe or email links, they use APP_BASE_URL so password reset and verification emails will use your new domain.

For more: Railway Docs - Public Networking and Domains.
