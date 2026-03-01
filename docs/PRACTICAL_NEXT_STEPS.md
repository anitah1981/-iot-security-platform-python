# Practical Next Steps – DNS & Unknown Device Detection

## 1. Platform: Enable network monitoring

In your deployed app (Railway, etc.) set:

```
ENABLE_NETWORK_MONITORING=true
```

**Note:** In cloud deployment, the platform cannot scan private LANs (192.168.x.x). It helps with IP-change alerts for devices that report their IP. For DNS and unknown-device detection, use the agent watchdog (below).

---

## 2. Device agent: DNS server change detection

The agent watchdog reads your system’s DNS servers and compares them to a baseline.

**Setup in `agent/.env`:**

```
EXPECTED_DNS=192.168.1.1,8.8.8.8
ENABLE_DNS_CHECK=true
```

- Use your router IP and/or preferred DNS servers (comma-separated).
- If current DNS differs from this list, an alert is sent to the platform.

**Runs automatically** with `device_agent.py` when `ENABLE_NETWORK_WATCHDOG=true` (default).

---

## 3. Device agent: Unknown device detection

The watchdog scans your LAN for devices not in `devices.json` and not your router (.1).

**Setup in `agent/.env`:**

```
ENABLE_UNKNOWN_DEVICE_CHECK=true
WATCHDOG_INTERVAL=60
```

- Uses ping + ARP to discover devices on the subnet from your first device in `devices.json`.
- Unknown IPs are reported to the platform; alerts are deduplicated for 6 hours.

**Optional:**
```
WATCHDOG_SCAN_RANGE=50
```
Scans .1–.50 by default; increase (e.g. 100) for larger subnets.

---

## 4. Quick checklist

| Step | Action |
|------|--------|
| Platform | Set `ENABLE_NETWORK_MONITORING=true` in deployed app env |
| Agent .env | Add `EXPECTED_DNS=your_router,8.8.8.8` (or your preferred DNS) |
| Agent .env | Keep `ENABLE_NETWORK_WATCHDOG=true` (default) |
| Run agent | `python device_agent.py` – heartbeat + watchdog run together |

Standalone watchdog run: `python network_watchdog.py` (one-off check).
