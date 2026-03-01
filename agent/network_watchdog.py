#!/usr/bin/env python3
"""
Network Watchdog - runs on your LAN alongside the device agent.
Detects: DNS server changes, unknown devices on the network.
Reports findings to the platform via X-API-Key.
"""
import json
import os
import platform
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = os.getenv("DEVICE_AGENT_CONFIG_DIR", str(SCRIPT_DIR))
BASELINE_FILE = Path(CONFIG_DIR) / ".watchdog_baseline.json"
WATCHDOG_INTERVAL = int(os.getenv("WATCHDOG_INTERVAL", "60"))
ENABLE_DNS_CHECK = os.getenv("ENABLE_DNS_CHECK", "true").lower() == "true"
ENABLE_UNKNOWN_DEVICE_CHECK = os.getenv("ENABLE_UNKNOWN_DEVICE_CHECK", "true").lower() == "true"
PING_TIMEOUT = float(os.getenv("WATCHDOG_PING_TIMEOUT", "1.0"))
SCAN_RANGE = int(os.getenv("WATCHDOG_SCAN_RANGE", "50"))


def _load_env():
    env_path = Path(SCRIPT_DIR) / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_expected_dns():
    raw = os.getenv("EXPECTED_DNS", "").strip()
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def get_current_dns_servers():
    servers = []
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | ForEach-Object { $_.ServerAddresses } | Where-Object { $_ }"
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if out.returncode == 0 and out.stdout:
                for line in out.stdout.strip().splitlines():
                    ip = line.strip()
                    if ip and _is_valid_ip(ip):
                        servers.append(ip)
        else:
            resolv = Path("/etc/resolv.conf")
            if resolv.exists():
                for line in resolv.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split(None, 1)
                        if len(parts) >= 2:
                            ip = parts[1].strip()
                            if _is_valid_ip(ip):
                                servers.append(ip)
    except Exception as e:
        print("[Watchdog] DNS read error:", e)
    return servers


def _is_valid_ip(s):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", s)
    if not m:
        return False
    return all(0 <= int(g) <= 255 for g in m.groups())


def _is_private_or_unicast(ip):
    """Exclude multicast (224-239), reserved, and link-local (169.254) from 'unknown device' alerts."""
    if not _is_valid_ip(ip):
        return False
    parts = [int(p) for p in ip.split(".")]
    first = parts[0]
    if first == 224 or first == 225 or (first >= 226 and first <= 239):
        return False
    if first == 169 and parts[1] == 254:
        return False
    return True


def check_dns_change():
    current = get_current_dns_servers()
    expected = get_expected_dns()
    if not expected:
        return False, current, []
    changed = set(current) != set(expected)
    return changed, current, expected


def get_network_prefix_from_devices(devices):
    for dev in devices:
        ip = dev.get("ip") or dev.get("ip_address") or dev.get("host")
        if ip and _is_valid_ip(ip):
            parts = ip.split(".")
            if len(parts) == 4:
                return ".".join(parts[:3])
    return None


def _ping_one(ip):
    system = platform.system()
    try:
        if system == "Windows":
            cmd = ["ping", "-n", "1", "-w", str(int(PING_TIMEOUT * 1000)), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(max(1, int(PING_TIMEOUT))), ip]
        r = subprocess.run(cmd, capture_output=True, timeout=PING_TIMEOUT + 2)
        return r.returncode == 0
    except Exception:
        return False


def _get_arp_ips():
    ips = []
    try:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout:
            for m in re.finditer(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", out.stdout):
                ip = m.group(1)
                if _is_valid_ip(ip):
                    ips.append(ip)
    except Exception as e:
        print("[Watchdog] ARP error:", e)
    return ips


def scan_network_for_devices(prefix, known_ips):
    if not prefix:
        return []
    reachable = []
    end = min(255, SCAN_RANGE + 1)
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(_ping_one, "{}.{}".format(prefix, i)): i for i in range(1, end)}
        for f in as_completed(futures, timeout=60):
            try:
                if f.result():
                    i = futures[f]
                    reachable.append("{}.{}".format(prefix, i))
            except Exception:
                pass
    arp_ips = set(_get_arp_ips())
    discovered = set(reachable) | arp_ips
    unknown = [ip for ip in discovered if ip not in known_ips and _is_valid_ip(ip) and _is_private_or_unicast(ip)]
    return sorted(set(unknown))


def load_devices():
    dev_file = Path(CONFIG_DIR) / "devices.json"
    if not dev_file.exists():
        return []
    with open(dev_file) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("devices", data.get("devices_list", []))


def get_known_ips(devices, prefix):
    known = set()
    for dev in devices:
        ip = dev.get("ip") or dev.get("ip_address") or dev.get("host")
        if ip and _is_valid_ip(ip):
            known.add(ip)
    if prefix:
        known.add("{}.1".format(prefix))
    return known


def send_security_report(base_url, api_key, payload):
    url = base_url.rstrip("/") + "/api/agent/security-report"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code in (200, 201):
            return True
        print("[Watchdog] Report rejected:", r.status_code, r.text[:200] if r.text else "")
        return False
    except requests.exceptions.ConnectionError as e:
        print("[Watchdog] Cannot reach platform (check API_BASE_URL and that the server is running):", e)
        return False
    except Exception as e:
        print("[Watchdog] Report failed:", e)
        return False


def run_watchdog(base_url, api_key):
    _load_env()
    report = {"dns_changed": False, "dns_servers": [], "expected_dns": [], "unknown_ips": []}

    if ENABLE_DNS_CHECK:
        changed, current, expected = check_dns_change()
        report["dns_servers"] = current
        report["expected_dns"] = expected
        report["dns_changed"] = changed
        if changed and expected:
            print("[Watchdog] DNS changed: expected", expected, "got", current)

    if ENABLE_UNKNOWN_DEVICE_CHECK:
        devices = load_devices()
        prefix = get_network_prefix_from_devices(devices)
        known = get_known_ips(devices, prefix)
        unknown = scan_network_for_devices(prefix, known) if prefix else []
        report["unknown_ips"] = unknown
        if unknown:
            suffix = " ..." if len(unknown) > 10 else ""
            print("[Watchdog] Unknown devices on network:", unknown[:10], suffix)

    if report["dns_changed"] or report["unknown_ips"]:
        ok = send_security_report(base_url, api_key, report)
        if not ok:
            print("[Watchdog] Failed to send security report to platform")


if __name__ == "__main__":
    _load_env()
    base = os.getenv("API_BASE_URL", "").rstrip("/")
    key = os.getenv("DEVICE_AGENT_API_KEY", "")
    if not base or not key:
        print("Set API_BASE_URL and DEVICE_AGENT_API_KEY in .env")
        sys.exit(1)
    run_watchdog(base, key)
