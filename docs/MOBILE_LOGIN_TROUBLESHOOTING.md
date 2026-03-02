# Mobile app – can't log in

## 1. See what the app is using

The **Login** screen now shows:
- **Server:** the API URL the app was built with (e.g. `https://pro-alert.co.uk`).
- **Check connection** – tap to test if that URL is reachable.

## 2. Rebuild after changing the API URL

The API URL is fixed at **build time** from `app.json` → `expo.extra.apiUrl`.

- Edit `mobile/app.json` and set `extra.apiUrl` to your live backend.
- Run: `cd mobile` then `eas build --platform ios --profile preview`.
- Install the **new** build on your phone.

## 3. Backend (Railway / production)

- **ALLOWED_HOSTS** must include your API host (e.g. `pro-alert.co.uk,www.pro-alert.co.uk`).
- **CORS_ORIGINS** can be your web origin; the native app does not send Origin so CORS does not block it.

## 4. Use the same account as on the web

Log in with the same email and password you use in a browser at that backend.

## 5. Error messages

- **"Can't reach server..."** – wrong URL, no internet, or server down. Tap **Check connection** and fix URL/rebuild.
- **"Invalid email or password"** – wrong credentials or account doesn’t exist on that backend.
- **"Email not verified..."** – verify email on the web first (when REQUIRE_EMAIL_VERIFICATION=true).
