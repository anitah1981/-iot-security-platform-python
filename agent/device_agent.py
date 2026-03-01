#!/usr/bin/env python3
"""
Device Agent – runs on your network (e.g. Raspberry Pi, PC, NAS) and sends heartbeats
to the IoT Security platform so your real devices (Alexa, Ring, cameras, etc.) show
as online/offline in the app.

Configure: copy .env.example to .env and devices.example.json to devices.json.
Get your API key from the app: Settings → Connect real devices.
"""
import json
import os
import socket
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

# Default paths
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = os.getenv("DEVICE_AGENT_CONFIG_DIR", str(SCRIPT_DIR))
DEVICES_FILE = Path(CONFIG_DIR) / "devices.json"
INTERVAL_SEC = int(os.getenv("DEVICE_AGENT_INTERVAL", "30"))
TIMEOUT_SEC = float(os.getenv("DEVICE_AGENT_TIMEOUT", "5"))
WATCHDOG_INTERVAL = int(os.getenv("WATCHDOG_INTERVAL", "60"))
ENABLE_WATCHDOG = os.getenv("ENABLE_NETWORK_WATCHDOG", "true").lower() == "true"


def load_env():
    # Load .env from script dir first so DEVICE_AGENT_CONFIG_DIR can override
    env_path = Path(SCRIPT_DIR) / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    base = os.getenv("API_BASE_URL", "").rstrip("/")
    key = os.getenv("DEVICE_AGENT_API_KEY", "")
    if not base or not key:
        return None, None
    return base, key


def load_devices():
    if not DEVICES_FILE.exists():
        return []
    with open(DEVICES_FILE) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("devices", data.get("devices_list", []))


def check_reachable(host: str, port: int = 80, timeout: float = TIMEOUT_SEC) -> bool:
    """Try TCP connect to host:port. Use port 80 or 443 for HTTP devices."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error, OSError):
        return False


def check_reachable_multi(host: str, ports: list, timeout: float = TIMEOUT_SEC) -> bool:
    """Try TCP connect to host on any of the given ports. Online if any succeeds."""
    for port in ports:
        try:
            p = int(port)
            if 1 <= p <= 65535 and check_reachable(host, p, timeout):
                return True
        except (ValueError, TypeError):
            continue
    return False


def get_ports_to_check(dev: dict) -> list:
    """Resolve port(s) to probe: 'ports' (list) or single 'port'. Covers all common IoT bases."""
    ports = dev.get("ports")
    if isinstance(ports, list) and len(ports) > 0:
        return [int(p) for p in ports if str(p).isdigit() or isinstance(p, int)]
    port = dev.get("port", 80)
    try:
        return [int(port)]
    except (TypeError, ValueError):
        return [80]


def is_reachable_any_port(host: str, ports: list, timeout: float = TIMEOUT_SEC) -> bool:
    """True if any of the given ports accepts a TCP connection (covers different IoT services)."""
    for port in ports:
        if check_reachable(host, port, timeout):
            return True
    return False


def send_heartbeat(base_url: str, api_key: str, device_id: str, status: str, ip_address: str = None, name: str = None, device_type: str = None):
    url = f"{base_url}/api/heartbeat"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    body = {"device_id": device_id, "status": status}
    if ip_address:
        body["ip_address"] = ip_address
    if name or device_type:
        body["metadata"] = {}
        if name:
            body["metadata"]["name"] = name
        if device_type:
            body["metadata"]["type"] = device_type
    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        if r.status_code in (200, 201):
            return True, None
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


def main():
    base_url, api_key = load_env()
    config_dir = os.getenv("DEVICE_AGENT_CONFIG_DIR", str(SCRIPT_DIR))
    global DEVICES_FILE
    DEVICES_FILE = Path(config_dir) / "devices.json"
    if not base_url or not api_key:
        print("Configure API_BASE_URL and DEVICE_AGENT_API_KEY in .env (see .env.example)")
        sys.exit(1)
    devices = load_devices()
    if not devices:
        print("Add devices to devices.json (see devices.example.json)")
        sys.exit(1)

    print(f"Device agent started. Reporting {len(devices)} device(s) every {INTERVAL_SEC}s to {base_url}")
    if ENABLE_WATCHDOG:
        print("Network watchdog enabled (DNS + unknown device detection)")
    last_watchdog = 0
    while True:
        for dev in devices:
            device_id = dev.get("device_id") or dev.get("id") or dev.get("name", "unknown")
            name = dev.get("name") or device_id
            device_type = dev.get("type", "Unknown")
            ip = dev.get("ip") or dev.get("ip_address") or dev.get("host")
            # "check": "none" or "skip_reachability": true = don't probe device (e.g. doorbells that
            # don't listen on common ports). Platform marks offline only when heartbeats stop.
            skip_check = dev.get("check") == "none" or dev.get("skip_reachability") is True
            if not ip:
                send_heartbeat(base_url, api_key, device_id, "offline", None, name, device_type)
                continue
            if skip_check:
                status = "online"
            else:
                ports = get_ports_to_check(dev)
                reachable = is_reachable_any_port(ip, ports, TIMEOUT_SEC)
                status = "online" if reachable else "offline"
            ok, err = send_heartbeat(base_url, api_key, device_id, status, ip, name, device_type)
            if not ok:
                print(f"[WARN] {device_id}: {err}")
        if ENABLE_WATCHDOG and (time.time() - last_watchdog) >= WATCHDOG_INTERVAL:
            try:
                from network_watchdog import run_watchdog
                run_watchdog(base_url, api_key)
                last_watchdog = time.time()
            except Exception as e:
                print(f"[WARN] Watchdog error: {e}")
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
