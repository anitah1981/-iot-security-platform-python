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
| `port`      | No       | Single port to check (default 80). Use 443 for HTTPS-only devices. |
| `ports`     | No       | **List of ports** to try; device is online if **any** port accepts a connection. Use for devices that may use different services (e.g. `[80, 443, 8080]`). Covers all common IoT bases. |
| `check`     | No       | Set to `"none"` for devices that don't respond to port checks (e.g. doorbells, cameras). The app will mark them offline only when heartbeats stop. |

**Common ports by device type:** See **docs/SECURITY_AND_AVAILABILITY.md** for the full table. Quick reference: Cameras 80, 443, 554 (RTSP), 8080, 37777, 34567; smart speakers 80, 443; doorbells often cloud-only → use `"check": "none"`. When unsure, use `"ports": [80, 443]`.

Example:

```json
[
  {
    "device_id": "ring-front-door",
    "name": "Ring Doorbell",
    "type": "Doorbell",
    "ip": "192.168.1.50",
    "check": "none"
  }
]
```

## Network watchdog (DNS + unknown devices)

The agent includes a **network watchdog** that runs alongside heartbeats (default every 60s). It detects:
- **DNS server changes** – if your DNS servers differ from `EXPECTED_DNS` in `.env`, an alert is sent
- **Unknown devices on the network** – scans your LAN for devices not in `devices.json`, alerts if found

**Setup:** Add to `.env`:
```
EXPECTED_DNS=192.168.1.1,8.8.8.8
ENABLE_NETWORK_WATCHDOG=true
WATCHDOG_INTERVAL=60
```

Set `EXPECTED_DNS` to your **actual** router/DNS (comma-separated). Example: if your router is `192.168.0.1`, use `EXPECTED_DNS=192.168.0.1,8.8.8.8` so you don't get false "DNS changed" alerts. Run standalone: `python network_watchdog.py`.

**Watchdog troubleshooting**

- **"Failed to send security report to platform"** – Check: (1) `API_BASE_URL` is reachable from the machine running the agent (e.g. `http://127.0.0.1:8000` if the app runs on the same PC; use the real URL if the app is on another machine or in the cloud). (2) `DEVICE_AGENT_API_KEY` in `.env` matches the key from the app **Settings → Connect real devices**. If the key is wrong, the log will show "Report rejected: 401" or similar.
- **"Unknown devices" includes 224.x.x.x** – Multicast addresses (224.0.0.x) are now filtered out; update the agent script if you still see them.
- **DNS changed when you didn't change it** – Set `EXPECTED_DNS` to match your real router (e.g. `192.168.0.1` for a 192.168.0.x network).

## How it works

- The agent checks each device by opening a **TCP connection** to `ip:port` (or, if `ports` is set, tries each port until one accepts). If any connection succeeds, the device is **online**; otherwise **offline**.
- It sends a heartbeat to `POST /api/heartbeat` with your **X-API-Key** so devices are linked to your account.
- If a device is not yet in the app, it is **auto-enrolled** and appears in your dashboard. You can also add devices manually in the app and use the same `device_id` in `devices.json` so the agent updates their status.

## Run automatically (as a service)

### Windows

**Option A – Task Scheduler (built-in)**

1. Open **Task Scheduler** (search "Task Scheduler" in Start).
2. **Create Basic Task** → Name: e.g. "Alert-Pro Device Agent" → Next.
3. Trigger: **When the computer starts** → Next.
4. Action: **Start a program** → Next.
5. Program: `python` (or full path, e.g. `C:\Python311\python.exe`).
6. Add arguments: `device_agent.py`.
7. Start in: folder where the agent lives, e.g. `C:\IoT-security-app-python\agent`.
8. Finish, then right‑click the task → **Properties** → enable **Run whether user is logged on or not** if you want it to run before login; set **Run with highest privileges** only if needed.
9. Optional: **If the task fails, restart every** 1 minute.

**Option B – NSSM (run as Windows service)**

1. Download [NSSM](https://nssm.cc/download).
2. Open Command Prompt as Administrator:
   ```cmd
   nssm install AlertProAgent "C:\Python311\python.exe" "C:\IoT-security-app-python\agent\device_agent.py"
   ```
3. In the NSSM window, set **Startup directory** to `C:\IoT-security-app-python\agent`.
4. Install service. Start it: `nssm start AlertProAgent`.

### Linux (systemd)

1. Create a unit file, e.g. `/etc/systemd/system/alertpro-agent.service`:

   ```ini
   [Unit]
   Description=Alert-Pro Device Agent
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/agent
   ExecStart=/usr/bin/python3 /home/pi/agent/device_agent.py
   Restart=always
   RestartSec=30

   [Install]
   WantedBy=multi-user.target
   ```

2. Adjust `User`, `WorkingDirectory`, and `ExecStart` to your paths.
3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable alertpro-agent
   sudo systemctl start alertpro-agent
   sudo systemctl status alertpro-agent
   ```

### Docker

Use an image with Python and `requests`, mount `.env` and `devices.json`, and run `device_agent.py`. Example:

```bash
docker run -d --restart unless-stopped \
  -v /path/to/agent/.env:/app/.env \
  -v /path/to/agent/devices.json:/app/devices.json \
  your-image python device_agent.py
```

## Security

- Keep `.env` and your API key **private**. Do not commit `.env` or share your key.
- The agent only needs **outbound** HTTPS access to your app; no inbound ports are required on your network.
