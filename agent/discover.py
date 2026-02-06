#!/usr/bin/env python3
"""
Discovery script – run on a computer on your network to find smart appliances and cameras.
Scans the local subnet and POSTs the list to the IoT Security platform so you can add them
in the app (Dashboard → IoT Device Management → Discover devices on your network → Refresh).

Usage:
  python discover.py

Configure: same .env as device_agent.py (API_BASE_URL, DEVICE_AGENT_API_KEY).
Optional: DISCOVERY_SUBNET=192.168.1.0/24 or DISCOVERY_START=192.168.1.1 DISCOVERY_END=192.168.1.254
"""
import json
import os
import socket
import sys
import concurrent.futures
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent


def load_env():
    env_path = Path(SCRIPT_DIR) / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_subnet_range():
    """Return (start_ip, end_ip) as strings for the range to scan."""
    subnet = os.getenv("DISCOVERY_SUBNET", "192.168.1.0/24")
    if "/" in subnet:
        base, bits = subnet.rsplit("/", 1)
        bits = int(bits)
        # Simple /24: 192.168.1.1 - 192.168.1.254
        parts = [int(x) for x in base.split(".")]
        if bits == 24 and len(parts) == 4:
            start = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
            end = f"{parts[0]}.{parts[1]}.{parts[2]}.254"
            return start, end
        # Fallback: .1 to .254
        base_str = ".".join(str(p) for p in parts[:3])
        return f"{base_str}.1", f"{base_str}.254"
    start = os.getenv("DISCOVERY_START", "192.168.1.1")
    end = os.getenv("DISCOVERY_END", "192.168.1.254")
    return start, end


def ip_to_int(ip):
    parts = [int(x) for x in ip.split(".")]
    return (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]


def int_to_ip(n):
    return f"{(n >> 24) & 255}.{(n >> 16) & 255}.{(n >> 8) & 255}.{n & 255}"


def check_reachable(ip, port=80, timeout=1.0):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error, OSError):
        return False


def get_hostname(ip, timeout=1.0):
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        return name
    except (socket.herror, socket.gaierror, socket.timeout, OSError):
        return None


def scan_one(ip, ports=(80, 443, 8080, 8000), timeout=1.0):
    for port in ports:
        if check_reachable(ip, port, timeout):
            hostname = get_hostname(ip, timeout)
            return {"ip": ip, "hostname": hostname, "mac": None}
    return None


def main():
    load_env()
    base_url = os.getenv("API_BASE_URL", "").rstrip("/")
    api_key = os.getenv("DEVICE_AGENT_API_KEY", "")
    if not base_url or not api_key:
        print("Configure API_BASE_URL and DEVICE_AGENT_API_KEY in .env (see .env.example)")
        sys.exit(1)

    start_str, end_str = get_subnet_range()
    start_i = ip_to_int(start_str)
    end_i = ip_to_int(end_str)
    # Limit to 254 hosts
    if end_i - start_i > 254:
        end_i = start_i + 254
    ips = [int_to_ip(i) for i in range(start_i, end_i + 1)]

    print(f"Scanning {len(ips)} IPs ({start_str} - {end_str})...")
    devices = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = {ex.submit(scan_one, ip): ip for ip in ips}
        for f in concurrent.futures.as_completed(futures):
            try:
                r = f.result()
                if r:
                    devices.append(r)
                    print(f"  Found: {r['ip']}" + (f" ({r['hostname']})" if r.get("hostname") else ""))
            except Exception as e:
                pass

    print(f"Found {len(devices)} device(s). Sending to app...")
    url = f"{base_url}/api/discovery"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    try:
        r = requests.post(url, json={"devices": devices}, headers=headers, timeout=30)
        if r.status_code in (200, 201):
            print("Done. Open Dashboard → IoT Device Management → Refresh discovered devices to add them.")
        else:
            print(f"API error: {r.status_code} {r.text[:200]}")
            sys.exit(1)
    except Exception as e:
        print(f"Request failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
