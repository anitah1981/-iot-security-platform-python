# Security, availability and CIA alignment

Alert-Pro is designed for **fast, accurate detection** of device loss and network compromise (WiFi interception, DNS change, device offline) with **minimal false positives** and **high availability**. Design goal: **maximize correctness and availability** with strong CIA (Confidentiality, Integrity, Availability) posture.

## Offline detection (security-focused)

- **Default:** A device is marked **offline** after **2 missed heartbeats** (e.g. 30s interval → 60s, 15s → 30s), with a **minimum of 30 seconds** and **maximum of 90 seconds**. This is short enough to detect WiFi takeover, DNS hijack, or device removal quickly, without triggering on brief network jitter.
- **Sweep interval:** The background sweep runs every **20 seconds**, so offline status is updated promptly.
- **Per-device override:** For high-security devices (cameras, doorbells, critical sensors), set **Offline after (seconds)** in the app to **30–45 seconds** so the platform marks them offline as soon as heartbeats stop. Range: 30–300 seconds.

## Heartbeat interval

- **Recommended:** Use a **15–30 second** heartbeat interval in the device agent (e.g. `DEVICE_AGENT_INTERVAL=15` in `.env`) so the platform sees missed heartbeats quickly. With a 30s default offline threshold (2× interval), 15s heartbeats give ~30s detection.
- **Trade-off:** Shorter intervals = faster detection and slightly more traffic; 15–30s is a good balance for security and availability.

## Port coverage for all IoT appliances

Different devices listen on different ports. To **cover all bases** for all IoT appliances:

1. **Use multiple ports** in the agent’s `devices.json` with the **`ports`** array. The agent tries each port; if **any** accepts a TCP connection, the device is reported online.
   - Example: `"ports": [80, 443, 8080]` for HTTP/HTTPS and common camera UIs.
   - Cameras: 80, 443, 554 (RTSP), 8080, 37777 (Dahua), 34567.
   - Smart speakers / displays: 80, 443.
   - Doorbells / cloud-only devices: use `"check": "none"` and rely on heartbeat presence only.

2. **Per-device:** Set the right `port` or `ports` (or `check: "none"`) so every device type is correctly probed.

**Common ports by IoT type:** Cameras `[80, 443, 554, 8080, 37777, 34567]`; smart speakers `[80, 443]`; routers `[80, 443, 8443]`; doorbells/cloud-only `"check": "none"`; NAS `[80, 443, 5000, 8080]`; unknown `[80, 443, 8080]`. See **agent/README.md** for details.

## CIA (Confidentiality, Integrity, Availability)

- **Confidentiality:** API keys and secrets are not logged; TLS for all app traffic; device agent uses HTTPS only. Store API keys in `.env` and never commit them.
- **Integrity:** Device status and alerts reflect actual heartbeat and sweep logic; optional audit logging for device/create/update; alerts are immutable once created (resolve, don’t edit).
- **Availability:** Short offline threshold and 20s sweep keep status accurate; optional per-device **Offline after (seconds)** for critical devices; multi-port checks reduce false “offline” when a device listens on a non-default port. Design goal: **high correctness and availability** with minimal downtime and false negatives.

## Summary

| Setting | Recommendation |
|--------|----------------|
| Heartbeat interval | 15–30s (agent) |
| Offline threshold | Default 2× interval (min 30s, max 90s); set 30–45s for high-security devices |
| Ports | Use `ports: [80, 443, ...]` or device-type-specific ports; use `check: "none"` for cloud-only devices |
| Sweep | 20s (platform) – no config change needed |

This keeps detection **fast and realistic** for security (WiFi/DNS/device compromise) while keeping the system **correct and available** with minimal false offline/online flapping.

---

## Practical next steps: DNS and unknown device detection

### 1. Platform – enable network monitoring

Set `ENABLE_NETWORK_MONITORING=true` in your deployed app. In cloud setups this helps with IP-change alerts; LAN scanning still requires the agent.

### 2. Agent – DNS server change detection

Add to `agent/.env`:
```
EXPECTED_DNS=192.168.1.1,8.8.8.8
ENABLE_DNS_CHECK=true
```
Set `EXPECTED_DNS` to your router and preferred DNS. The watchdog compares system DNS to this and alerts if it changes.

### 3. Agent – unknown device detection

Enable in `agent/.env` (on by default):
```
ENABLE_UNKNOWN_DEVICE_CHECK=true
WATCHDOG_INTERVAL=60
```
The agent scans the LAN (ping + ARP), compares to known devices in `devices.json`, and alerts on unknown IPs.

### 4. Run the agent

`python device_agent.py` runs heartbeats and the watchdog. Set `EXPECTED_DNS` before first run.
