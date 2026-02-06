# Device Agent – Connect Real Devices to the App

The device agent runs on a machine on your **same network** as your IoT devices (e.g. Raspberry Pi, PC, or NAS). It can:

1. **Discover devices** – Run `python discover.py` to scan your network and send the list to the app. Then in **Dashboard → IoT Device Management** click **Refresh discovered devices** and add them to your account.
2. **Report online/offline** – Run `python device_agent.py` so devices show as **online** or **offline** in the app.

## What you need

1. **API key** – From the app: **Settings → Connect real devices** → copy your device agent API key (or generate one).
2. **App URL** – Your deployed app base URL (e.g. `https://your-app.example.com`).
3. **Device list** – For each device you want to monitor: a **device_id** (must match what you use in the app if you added it manually), **name**, **type**, and **IP** (or hostname) on your LAN.

## Discover devices on your network

1. Install Python 3 and `requests` (see below).
2. Configure `.env` with `API_BASE_URL` and `DEVICE_AGENT_API_KEY` (from **Settings → Device agent key**).
3. Run discovery once:
   ```bash
   python discover.py
   ```
4. In the app go to **Dashboard → IoT Device Management**. Under **Discover devices on your network** click **Refresh discovered devices**, then **Add to my devices** for each device you want to add.

Optional: set `DISCOVERY_SUBNET=192.168.1.0/24` or `DISCOVERY_START` / `DISCOVERY_END` in `.env` to scan a different range.

## Quick setup (for heartbeats / online status)

1. **Install Python 3** and `requests`:
   ```bash
   pip install requests
   ```

2. **Configure** (in the same folder as `device_agent.py`):
   - Copy `.env.example` to `.env`.
   - Set `API_BASE_URL` and `DEVICE_AGENT_API_KEY` in `.env`.
   - Copy `devices.example.json` to `devices.json` and edit: add your devices with `device_id`, `name`, `type`, and `ip` (and optional `port`, default 80).

3. **Run**:
   ```bash
   python device_agent.py
   ```
   Leave it running (or run as a service – see below).

## devices.json format

Each entry can have:

| Field        | Required | Description |
|-------------|----------|-------------|
| `device_id` | Yes      | Unique ID (e.g. `ring-front-door`). Use the same ID in the app if you added the device manually. |
| `name`      | Yes      | Display name (e.g. "Ring Doorbell"). |
| `type`      | Yes      | One of: Camera, Router, Sensor, Smart Speaker, Doorbell, etc. |
| `ip`        | Yes      | IP or hostname on your LAN (e.g. `192.168.1.50`). |
| `port`      | No       | Port to check (default 80). Use 443 for HTTPS-only devices. |

Example:

```json
[
  {
    "device_id": "ring-front-door",
    "name": "Ring Doorbell",
    "type": "Doorbell",
    "ip": "192.168.1.50"
  }
]
```

## How it works

- The agent checks each device by opening a **TCP connection** to `ip:port` (default port 80). If the connection succeeds, the device is reported as **online**; otherwise **offline**.
- It sends a heartbeat to `POST /api/heartbeat` with your **X-API-Key** so devices are linked to your account.
- If a device is not yet in the app, it is **auto-enrolled** and appears in your dashboard. You can also add devices manually in the app and use the same `device_id` in `devices.json` so the agent updates their status.

## Run as a service (optional)

- **Linux (systemd):** Create a unit file that runs `python /path/to/agent/device_agent.py` and restart on failure.
- **Windows:** Use Task Scheduler or NSSM to run the script at startup.
- **Docker:** Use a small image with Python and `requests`, mount `.env` and `devices.json`, and run `device_agent.py`.

## Security

- Keep `.env` and your API key **private**. Do not commit `.env` or share your key.
- The agent only needs **outbound** HTTPS access to your app; no inbound ports are required on your network.
