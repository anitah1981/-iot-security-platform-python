# Mobile app – can't log in

## 1. See what the app is using

After the changes in this repo, the **Login** screen shows:
- **Server:** the API URL the app was built with (e.g. `https://pro-alert.co.uk`).
- **Check connection** – tap to test if that URL is reachable.

Use that to confirm the app is pointing at the right backend.

## 2. Rebuild after changing the API URL

The API URL is fixed at **build time** from `app.json` → `expo.extra.apiUrl`.

- Edit `mobile/app.json` and set `extra.apiUrl` to your live backend (e.g. `https://pro-alert.co.uk`).
- Run:
  ```bash
  cd mobile
  eas build --platform ios --profile preview
  ```
- Install the **new** build on your phone. Old builds still use the old URL.

## 3. Backend (Railway / production)

For the app to reach your API:

- **ALLOWED_HOSTS** must include your API host, e.g.:
  - `pro-alert.co.uk,www.pro-alert.co.uk`
  - or your Railway host if you use that URL.
- **CORS_ORIGINS** can be your web origin (e.g. `https://pro-alert.co.uk`). The native app does not send an Origin header, so CORS does not block it.

## 4. Use the same account as on the web

Log in with the **same email and password** you use in a browser at that same backend. The account must exist in the database that backend uses.

## 5. Clear error messages

After the updates, failed login shows:
- **"Can't reach server..."** – app cannot contact the API (wrong URL, no internet, or server down).
- **"Invalid email or password"** – credentials wrong or account doesn’t exist on that backend.
- **"Email not verified..."** – backend has `REQUIRE_EMAIL_VERIFICATION=true`; verify the email first on the web.

If you see **"Can't reach server"**, tap **Check connection** and fix the URL (then rebuild) or your network/host config.
