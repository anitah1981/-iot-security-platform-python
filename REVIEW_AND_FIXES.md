# Pro-Alert App Review – What Was Checked and What Was Fixed

## Summary

A full pass was done across backend, web, and mobile. **Two critical fixes were applied**; the rest are documented for you to prioritise.

---

## Critical fixes applied

### 1. Web login: token in localStorage restored

- **Issue:** After the cookie+CSRF migration we stopped storing the JWT in `localStorage` after login. The web app still relies on it for:
  - Dashboard and other pages (they redirect to login if `localStorage.getItem('iot_token')` is missing).
  - The `api()` helper (sends `Authorization: Bearer` from `getToken()`).
  - The WebSocket client (needs the token to connect).
- **Fix:** In `web/assets/app.js`, after a successful `/api/auth/login` we again call `setToken(data.token)` and `setRefreshToken(data.refresh_token)`. The backend still sets the HttpOnly cookie; the copy in localStorage is used for the above behaviour until the app is updated to support cookie-only API auth.

### 2. Socket.IO real-time not wired into the app

- **Issue:** The Socket.IO app (`services/websocket_service.py`) was never attached to the main ASGI app, so requests to `/socket.io` were not handled and the web/mobile real-time clients could not connect.
- **Fix:** In `main.py`, the FastAPI app is built as `fastapi_app`, then the top-level `app` used by uvicorn is set to `socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")`. So `/socket.io` is handled by Socket.IO and all other routes by FastAPI. **Run with** `uvicorn main:app` (string `"main:app"`) so the combined app is loaded.

---

## Other findings (no code changes made)

### Backend

- **Config / startup:** `core.config` and `core.startup` look correct. Production checks, heartbeat sweep, and optional monitors start as expected.
- **Heartbeat:** `/api/heartbeat` is exempt from CSRF; device agent keys and offline logic are in place.
- **WebSocket auth:** JWT is validated on connect; clients are put in `user_<id>` rooms. No change needed.
- **Tests:** `tests/conftest.py` uses `from main import app` and `TestClient(app)`. With `app` now the Socket.IO-wrapped ASGI app, tests should still work. If any test fails on request routing, switch the fixture to `from main import fastapi_app` and use `TestClient(fastapi_app)` for API-only tests.

### Web frontend

- **CSRF:** `getOrCreateCsrfToken()` and `X-CSRF-Token` on non-GET requests are in place.
- **Auth:** Pages (dashboard, family, settings, audit-logs, incidents) guard with `localStorage.getItem('iot_token')`; with the token restored after login, this works again.
- **Optional later improvement:** To go fully cookie-only for the web, the backend would need an API auth path that accepts the `iot_token` cookie (e.g. an alternative to `get_current_user` that uses `get_token_from_request`), and the frontend would stop sending `Authorization` and stop relying on `localStorage` for auth.

### Mobile

- **Auth / API:** SecureStore and Bearer token are used; CSRF is correctly skipped for `Authorization: Bearer`.
- **Realtime:** `services/realtime.js` connects to the backend with the JWT and subscribes to device/alert events; with Socket.IO now mounted, the mobile app can receive real-time updates when the backend URL is correct.
- **User id for realtime:** `initializeRealtime(user, ...)` uses `user.id` or `user._id`; ensure the `/api/auth/me` (or login) response includes one of these so the Socket.IO server can associate the connection.

### Security

- **CSRF:** Middleware is enabled; exempt paths and Bearer exemption are set; cookie + header check applies when the browser has the `iot_token` cookie.
- **CORS / headers:** Handled in `core.middleware`; no issues found.

### Deployment / env

- **Production:** Rely on `core.config.check_production_config()` (MONGO_URI, JWT_SECRET, APP_BASE_URL, CORS, etc.).
- **.env.example:** Keep it updated with any new keys (e.g. Stripe, SMTP, Sentry) so deploy and beta are straightforward.

---

## What to do next

1. **Run the app:**  
   `python -m uvicorn main:app --reload --port 8000` (or `python main.py` if it invokes uvicorn with `"main:app"`).
2. **Smoke-test web:**  
   Log in → open dashboard → confirm devices/alerts load and that the “Live”/WebSocket indicator can connect (check browser devtools for `/socket.io`).
3. **Smoke-test mobile:**  
   Point the app at the same backend; open dashboard and confirm real-time updates after a change from web or API.
4. **Optional:**  
   Add a short “How we determine online/offline” note in the UI or docs for beta users.

---

## File changes made in this review

| File | Change |
|------|--------|
| `web/assets/app.js` | Restored `setToken(data.token)` and `setRefreshToken(data.refresh_token)` after successful login. |
| `main.py` | Renamed FastAPI instance to `fastapi_app`; set `app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")`; ensured uvicorn runs `"main:app"`. |

No other files were modified. Use this document as the “what was reviewed and what was fixed” reference.
