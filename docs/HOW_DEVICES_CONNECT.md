# How Users Add Devices (Web, Android, iOS) and What “Connects” Them

This doc explains how devices are added in the IoT Security platform and what actually connects a device (e.g. Alexa, Ring doorbell) to the app.

---

## 1. How users add devices today (all three: web, Android, iOS)

### Where it happens

- **Web:** Dashboard → **➕ Add Device** (or Devices section) → form: Device ID, Name, Type, optional Router IP, optional Device IP.
- **Android / iOS:** Same flow in the mobile app: **Add Device** → user enters the same fields.

### What the user enters

| Field | Required | Meaning |
|-------|----------|--------|
| **Device ID** | Yes | A unique label you choose (e.g. `ring-front-door`, `alexa-living-room`). |
| **Name** | Yes | Display name (e.g. "Ring Doorbell", "Living Room Alexa"). |
| **Type** | Yes | Category: Camera, Router, Sensor, Smart Speaker, Doorbell, etc. |
| **Router IP** | No | Your router/gateway IP (used for context; optional). |
| **Device IP** | No | The device’s IP on your network (optional; can be filled later or by heartbeats). |

### What the backend does

- **Create device (API):** `POST /api/devices` with the above. The backend stores the device in the database and links it to the user (or family). No physical “connection” to the device happens here.
- **Heartbeat (optional):** If something later sends `POST /api/heartbeat` with that same `device_id`, the backend updates that device’s **last seen** and **online/offline** status. If no heartbeat is ever sent, the device stays in the list but typically shows as **offline**.

So today, “adding a device” = **creating a record** (manual on web/Android/iOS). The “connection” is either **manual data only** or **heartbeats from something else** (see below).

---

## 2. What actually “connects” a device to the app?

In this platform, “connected” means one or both of:

1. **The device exists in the app** (user added it manually) → you can see it, name it, group it, get alerts for it.
2. **Something sends heartbeats for that device** → the app can show it as online/offline and when it was last seen.

There is **no built‑in link** today between the app and the real hardware of an Alexa, Ring, or other third‑party device. The app does not talk to Amazon or Ring APIs, and there is no agent installed on the device itself.

So for **Alexa or Ring doorbell** specifically:

- **What exists today:** You can **add them manually** (Device ID e.g. `ring-front-door`, Name “Ring Doorbell”, Type “Doorbell”). They appear in the app and you can get alerts if you also have something sending heartbeats for that `device_id` (see below). Without heartbeats, they’re just “tracked” by name/type and stay offline.
- **What does *not* exist:** No automatic discovery of Alexa/Ring on your network, no Amazon/Ring cloud integration, and no app running on the Alexa/Ring device that talks to our backend.

---

## 3. Ways a “connection” can happen (today and possible future)

### A. Manual add only (today)

- User adds “Ring Doorbell” / “Living Room Alexa” in the app (web or mobile) with a chosen Device ID and type.
- **Connection:** None to the real device. The app only stores the record. Status will stay offline unless heartbeats are used (B or C).

### B. Heartbeats from the device agent (ready at launch)

- **Shipped:** A **device agent** is included in the project (`agent/` folder). Run it on a machine on your network (e.g. Raspberry Pi, PC, NAS). It checks each device (TCP connect to IP:port), then sends heartbeats to the platform so devices show as **online** or **offline** in the app.
- **API key:** In the app go to **Settings → Connect real devices**. Generate a **device agent API key** and put it in the agent’s `.env` as `DEVICE_AGENT_API_KEY`. Use the same `API_BASE_URL` as your deployed app. Add your devices to `devices.json` (device_id, name, type, ip, optional port).
- **How it works:** The agent calls `POST /api/heartbeat` with header **X-API-Key: your_key** and body e.g. `{"device_id": "ring-front-door", "status": "online", "ip_address": "192.168.1.50"}`. Devices are linked to your account and appear in the dashboard; new devices are auto-enrolled.
- **Setup:** See **agent/README.md** for install (pip install requests), config (`.env` + `devices.json`), and running the agent. This is **ready to use as soon as the app is live**.

### C. Manufacturer / cloud integrations (future)

- **Ring, Alexa, etc.:** A real “connection” from our app to Ring or Alexa would require:
  - **Ring:** Using Ring’s API (or official integration) so our backend can query device status / events.
  - **Alexa:** Using Alexa Smart Home or similar so our backend can see device state.
- In that world, **our backend** would talk to Amazon/Ring; the **web and mobile apps** would just show data we get from those APIs. Users might still “add” the device in our app, but we’d link it to the manufacturer’s device ID and pull status from their cloud.

We don’t have these integrations implemented yet; they are a possible future step.

### D. On‑device agent (future)

- An app or daemon runs **on the IoT device itself** (or on a gateway in the home) and sends heartbeats (or events) to our API. That would “connect” the device in the same way as B, but from the device or gateway.

---

## 4. Short answers to “how do users add devices?” and “what connects Alexa/Ring?”

| Question | Answer |
|----------|--------|
| **How do users add devices (web / Android / iOS)?** | Same flow everywhere: open **Add Device**, enter Device ID, Name, Type, and optional Router IP / Device IP. Submit → device is created in the backend and appears in the app. |
| **What connects the device to the app?** | Either **nothing** (manual entry only; device stays “offline”) or **something that sends heartbeats** for that `device_id` (e.g. your own agent/script, or a future integration). |
| **Alexa / Ring – how is the connection made?** | Use the **device agent**: add each device in `agent/devices.json` (device_id, name, type, ip). The agent pings them and sends heartbeats with your API key so they appear in the app as online/offline. No Ring/Alexa cloud integration required. |

---

## 5. Where in the code this lives

- **Adding a device (web):** `web/dashboard.html` (Add Device form), `web/assets/app.js` (submit → `POST /api/devices`).
- **Adding a device (mobile):** Same API `POST /api/devices` from the mobile app.
- **Backend create:** `routes/devices.py` → `create_device`; validates and stores in MongoDB.
- **Device agent API key:** Settings → Connect real devices; `routes/device_agent_key.py` (GET/POST regenerate); `services/device_agent_key_service.py` (generate/verify); heartbeats accept **X-API-Key** and associate devices with that user/family.
- **Heartbeats:** `routes/heartbeat.py` → `POST /api/heartbeat`; optional **X-API-Key**; updates `lastSeen`/status or auto-enrolls and links device to the key owner.
- **Device agent (shipped):** `agent/device_agent.py` + `agent/README.md`, `agent/.env.example`, `agent/devices.example.json`.
- **Offline detection:** `services/heartbeat_sweep.py` marks devices offline when no heartbeat is received for a while.
