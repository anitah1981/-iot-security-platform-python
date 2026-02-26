# routes/network.py - Network Monitoring & Change Detection
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional
from bson import ObjectId
import socket
import asyncio
import subprocess
import re
import platform
from concurrent.futures import ThreadPoolExecutor

from database import get_database
from routes.auth import get_current_user, require_admin
from services.network_monitor import NetworkMonitor, start_network_monitoring, stop_network_monitoring, is_network_monitoring_enabled
from middleware.security import limiter

router = APIRouter()


def _identify_device_type(hostname: str = None, mac: str = None) -> str:
    """Identify device type from hostname or MAC vendor. Returns device type string."""
    if not hostname and not mac:
        return "Other"
    
    h = (hostname or "").lower()
    m = (mac or "").lower()
    
    # Hostname patterns - comprehensive list
    # Doorbells & Cameras
    if any(x in h for x in ["ring", "doorbell", "door-bell", "doorbot", "ringdoorbell"]):
        return "Doorbell"
    if any(x in h for x in ["camera", "cam-", "ipcam", "webcam", "nvr", "hikvision", "dahua", "arlo", "blink", "wyze", "nest-cam", "eufy-cam"]):
        return "Camera"
    
    # Network Equipment
    if any(x in h for x in ["router", "gateway", "ap-", "access-point", "modem", "wifi", "netgear", "tp-link", "asus-rt", "linksys"]):
        return "Router"
    
    # Smart Speakers & Assistants
    if any(x in h for x in ["echo", "alexa", "echo-", "echo.", "amazon-echo", "google-home", "googlenest", "homepod", "apple-homepod", "speaker", "sonos", "bose-speaker"]):
        return "Smart Speaker"
    
    # Thermostats & Climate
    if any(x in h for x in ["thermostat", "nest", "ecobee", "hive-therm", "tado", "honeywell"]):
        return "Thermostat"
    
    # Smart TVs & Streaming
    if any(x in h for x in ["smart-tv", "smarttv", "roku", "firetv", "fire-tv", "appletv", "apple-tv", "chromecast", "samsung-tv", "lg-tv", "sony-tv", "androidtv"]):
        return "Smart TV"
    
    # Sensors
    if any(x in h for x in ["sensor", "motion", "door-sensor", "window-sensor", "multisensor", "motion-sensor"]):
        return "Sensor"
    
    # Hubs & Controllers
    if any(x in h for x in ["hive", "philips-hue", "hue-bridge", "lifx", "wemo", "smartthings", "homekit", "hubitat", "vera"]):
        return "Smart Home Hub"
    
    # Smart Plugs & Switches
    if any(x in h for x in ["plug", "switch", "outlet", "smart-plug", "smart-switch", "wemo-switch", "tp-link-plug"]):
        return "Smart Plug"
    
    # MAC vendor patterns (OUI - first 3 bytes identify manufacturer)
    # Comprehensive database of common IoT device manufacturers
    mac_prefix = m.replace(":", "")[:6] if m else ""
    
    # Ring (Amazon) - Doorbells
    if mac_prefix in ["74c63b", "b0c7de", "6cadf8", "d86162", "c8dfe2", "443266"]:
        return "Doorbell"
    
    # Nest (Google) - Thermostats & Cameras
    if mac_prefix in ["18b430", "64168d", "f8f005", "0c4de9"]:
        if "cam" in h or "camera" in h:
            return "Camera"
        return "Thermostat"
    
    # TP-Link - Smart Plugs, Cameras, Routers
    if mac_prefix in ["50c7bf", "c006c3", "a0f3c1", "689e19", "f4f26d", "1c3bf5"]:
        if "cam" in h or "camera" in h:
            return "Camera"
        if "router" in h or "ap" in h:
            return "Router"
        return "Smart Plug"
    
    # Amazon Echo/Alexa
    if mac_prefix in ["f0d2f1", "b8f009", "8871e5", "fc650a", "38f73d", "44650d", "04f1a1"]:
        return "Smart Speaker"
    
    # Google Home/Nest
    if mac_prefix in ["f4f5d8", "b4f61c", "a4f1e8", "1c5a3e", "54a050", "6c709f"]:
        return "Smart Speaker"
    
    # Apple HomePod/Apple TV
    if mac_prefix in ["90dd5d", "acde48", "4c57ca", "7c6df8", "d8a25e", "483b38"]:
        if "appletv" in h or "apple-tv" in h:
            return "Smart TV"
        return "Smart Speaker"
    
    # Roku
    if mac_prefix in ["d8310d", "b82ca0", "b0a737", "cc6ea4", "dc3a5e", "08056d"]:
        return "Smart TV"
    
    # Samsung SmartThings & TVs
    if mac_prefix in ["ecf4bb", "2c44fd", "78bdbc", "d85d4c", "a82066", "c85b76"]:
        if "tv" in h or "smart-tv" in h:
            return "Smart TV"
        return "Smart Home Hub"
    
    # Philips Hue
    if mac_prefix in ["001788", "ecb5fa", "000d6f"]:
        return "Smart Home Hub"
    
    # Wyze Cameras
    if mac_prefix in ["2cab00", "7c78b2"]:
        return "Camera"
    
    # Arlo Cameras
    if mac_prefix in ["283695"]:
        return "Camera"
    
    # Sonos Speakers
    if mac_prefix in ["542a1b", "5cafd2", "b8e937", "949f3e"]:
        return "Smart Speaker"
    
    # Netgear (Routers & Arlo)
    if mac_prefix in ["30469a", "9c3dcf", "a040a0", "e091f5"]:
        if "cam" in h or "arlo" in h:
            return "Camera"
        return "Router"
    
    # Hive (British Gas)
    if mac_prefix in ["001c2b"]:
        return "Thermostat"
    
    # Eufy (Anker)
    if mac_prefix in ["801f02"]:
        return "Camera"
    
    return "Other"


def _parse_router_ip(router_ip: str) -> Optional[str]:
    """Validate router IP and return network prefix (first 3 octets)."""
    try:
        parts = router_ip.strip().split(".")
        if len(parts) != 4:
            return None
        for p in parts:
            n = int(p)
            if n < 0 or n > 255:
                return None
        return ".".join(parts[:3])
    except Exception:
        return None


def _ping_sync(ip: str, timeout_ms: int = 2000) -> bool:
    """Return True if host responds to ping. Windows: -w is milliseconds; Linux: -W is seconds."""
    try:
        creationflags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        if platform.system() == "Windows":
            # -w = timeout in milliseconds
            r = subprocess.run(
                ["ping", "-n", "1", "-w", str(max(500, timeout_ms)), ip],
                capture_output=True,
                timeout=min(10, (timeout_ms // 1000) + 2),
                creationflags=creationflags,
            )
        else:
            # -W = timeout in seconds
            r = subprocess.run(
                ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), ip],
                capture_output=True,
                timeout=(timeout_ms // 1000) + 2,
            )
        return r.returncode == 0
    except Exception:
        return False


def _get_arp_table_sync() -> Dict[str, str]:
    """Return dict ip -> mac (e.g. '192.168.1.5' -> 'aa:bb:cc:dd:ee:ff')."""
    result = {}
    try:
        if platform.system() == "Windows":
            out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5,
                                 creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
            if out.returncode != 0:
                return result
            # Windows: "  192.168.1.1    aa-bb-cc-dd-ee-ff     dynamic"
            for line in out.stdout.splitlines():
                m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F\-:]+)", line)
                if m:
                    ip_part, mac_part = m.group(1), m.group(2).replace("-", ":").lower()
                    if re.match(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", mac_part) or len(mac_part) == 17:
                        result[ip_part] = mac_part
        else:
            out = subprocess.run(["arp", "-n"], capture_output=True, text=True, timeout=5)
            if out.returncode != 0:
                out = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=5)
                if out.returncode != 0:
                    return result
                for line in out.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and parts[0].replace(".", "").isdigit():
                        result[parts[0]] = parts[4].lower()
            else:
                for line in out.stdout.splitlines():
                    m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+ether\s+([0-9a-f:]+)", line)
                    if m:
                        result[m.group(1)] = m.group(2).lower()
    except Exception:
        pass
    return result

@router.post("/check-device-status")
@limiter.limit("20/minute")
async def check_device_status(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Check real-time status of all user's devices by pinging their IPs.
    Updates device status to online/offline based on ping response.
    """
    from datetime import datetime
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get user's non-deleted devices
    devices = await db.devices.find({
        "$or": [{"userId": user_id}, {"user_id": user_id}],
        "isDeleted": {"$ne": True}
    }).to_list(length=1000)
    
    if not devices:
        return {"message": "No devices to check", "updated": 0}
    
    # Check each device: ping first, then port scan. Do NOT use ARP for online (stale ARP keeps devices "online" after WiFi off).
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=20)
    
    try:
        async def check_and_update(device):
            ip = device.get("ipAddress")
            if not ip or ip == "0.0.0.0":
                return None
            
            # 1. Ping first
            is_online = await loop.run_in_executor(executor, _ping_sync, ip, 1500)
            # 2. If ping fails, try ports (phones often block ping)
            if not is_online:
                test_ports = [80, 443, 8080, 5353, 62078]
                for port in test_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.5)
                        result = sock.connect_ex((ip, port))
                        sock.close()
                        if result == 0:
                            is_online = True
                            break
                    except Exception:
                        pass
            
            new_status = "online" if is_online else "offline"
            
            # Update if status changed
            if device.get("status") != new_status:
                now = datetime.utcnow()
                await db.devices.update_one(
                    {"_id": device["_id"]},
                    {"$set": {
                        "status": new_status,
                        "lastSeen": now if is_online else device.get("lastSeen"),
                        "updatedAt": now
                    }}
                )
                # When device goes offline, create alert and send notifications (same as background monitor)
                if new_status == "offline" and device.get("alertsEnabled", True):
                    user_id = device.get("userId") or device.get("user_id")
                    if user_id:
                        try:
                            from services.device_status_monitor import _create_connectivity_alert
                            await _create_connectivity_alert(
                                device["_id"],
                                device.get("name", "Unknown Device"),
                                user_id
                            )
                        except Exception as e:
                            print(f"[WARNING] Failed to create/send offline alert from API: {e}")
                return {"device_id": str(device["_id"]), "old": device.get("status"), "new": new_status}
            return None
        
        results = await asyncio.gather(*[check_and_update(d) for d in devices])
        updated = [r for r in results if r is not None]
        
        return {
            "message": "Device status check complete",
            "total_devices": len(devices),
            "updated": len(updated),
            "changes": updated
        }
    finally:
        executor.shutdown(wait=False)

@router.post("/scan")
@limiter.limit("5/minute")
async def scan_network(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Manually trigger a network scan for changes
    - Checks for IP changes
    - Checks for DNS changes
    - Detects unknown devices on network
    """
    try:
        monitor = NetworkMonitor()
        await monitor.check_network_changes()
        return {"message": "Network scan completed", "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Network scan failed: {str(e)}"
        )

@router.get("/changes")
async def get_network_changes(current_user: dict = Depends(get_current_user)):
    """
    Get recent network change alerts
    Shows IP changes, DNS changes, and unknown device detections
    """
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get user's devices
    devices = await db.devices.find({
        "$or": [
            {"userId": user_id},
            {"user_id": user_id}
        ]
    }).to_list(length=1000)
    
    device_ids = [d["_id"] for d in devices]
    
    # Get network-related alerts from last 7 days
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    alerts = await db.alerts.find({
        "deviceId": {"$in": device_ids},
        "type": "security",
        "context.change_type": {"$in": ["ip_change", "dns_change", "unknown_device"]},
        "createdAt": {"$gte": seven_days_ago}
    }).sort("createdAt", -1).to_list(length=100)
    
    return {
        "changes": [
            {
                "id": str(a["_id"]),
                "device_id": str(a.get("deviceId", "")),
                "message": a.get("message", ""),
                "severity": a.get("severity", "medium"),
                "change_type": a.get("context", {}).get("change_type", "unknown"),
                "created_at": a.get("createdAt"),
                "resolved": a.get("resolved", False)
            }
            for a in alerts
        ],
        "total": len(alerts)
    }

@router.get("/scan-devices")
@limiter.limit("5/minute")
async def scan_for_devices(
    request: Request,
    router_ip: Optional[str] = Query(None, description="Router/gateway IP (e.g. 192.168.1.1). If omitted, uses value from Settings."),
    current_user: dict = Depends(get_current_user)
):
    """
    Scan network for devices. Enter router IP to scan that network; returns IP, hostname (if available), and MAC (if available).
    Works when the app is running on the same network (e.g. on your PC or server).
    """
    db = await get_database()
    user_id = current_user["_id"]
    settings = await db.network_settings.find_one({"userId": user_id})

    if router_ip:
        network_prefix = _parse_router_ip(router_ip)
        if not network_prefix:
            return {
                "devices": [],
                "message": "Invalid router IP. Use format like 192.168.1.1",
                "error": "invalid_router_ip"
            }
        router_ip_use = router_ip.strip()
        if settings and not settings.get("routerIp"):
            await db.network_settings.update_one(
                {"userId": user_id},
                {"$set": {"routerIp": router_ip_use, "networkPrefix": network_prefix, "updatedAt": __import__("datetime").datetime.utcnow()}},
                upsert=True
            )
    else:
        if not settings or not settings.get("networkPrefix"):
            return {
                "devices": [],
                "message": "Enter your router IP above and click Scan, or set it in Settings first.",
                "error": "no_router_ip"
            }
        network_prefix = settings.get("networkPrefix")
        router_ip_use = settings.get("routerIp", f"{network_prefix}.1")

    SCAN_PORTS = [80, 443, 8008, 8080, 7000, 8009, 8443, 22, 5000, 554, 8888, 9000, 10000, 49152]
    SOCKET_TIMEOUT = 0.6
    MAX_WORKERS = 50
    
    # Scan full range .2 to .254
    ips_to_scan = [f"{network_prefix}.{i}" for i in range(2, 255) if f"{network_prefix}.{i}" != router_ip_use]

    def _is_valid_device_ip(ip: str) -> bool:
        """Filter out broadcast, multicast, and invalid IPs."""
        try:
            parts = ip.split(".")
            last_octet = int(parts[3])
            # Skip broadcast (.0, .255) and multicast (224-239)
            if last_octet == 0 or last_octet == 255 or (224 <= last_octet <= 239):
                return False
            return True
        except:
            return False

    def _check_device_sync(ip: str) -> Optional[Dict]:
        """Check if IP has a real device. Only return if we have STRONG evidence."""
        if not _is_valid_device_ip(ip):
            return None
        
        try:
            # Method 1: Try port scan (definitive proof of a device)
            open_ports = []
            for port in SCAN_PORTS:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(SOCKET_TIMEOUT)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    if result == 0:
                        open_ports.append(port)
                        return {"ip": ip, "ports_open": open_ports, "method": "port"}
                except Exception:
                    pass
            
            # Method 2: Try ping (only count as device if it responds)
            if _ping_sync(ip, timeout_ms=1500):
                return {"ip": ip, "ports_open": [], "method": "ping"}
            
            return None
        except Exception:
            return None

    try:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        try:
            # PHASE 1: Get ARP table (these are devices Windows has communicated with recently)
            arp = await loop.run_in_executor(executor, _get_arp_table_sync)
            
            # PHASE 2: Scan network for responsive devices
            scan_tasks = [loop.run_in_executor(executor, _check_device_sync, ip) for ip in ips_to_scan]
            scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)

            # Collect verified devices (only those that responded to port scan or ping)
            devices_by_ip = {}
            
            for r in scan_results:
                if isinstance(r, dict) and r and r.get("ip"):
                    ip = r["ip"]
                    devices_by_ip[ip] = {
                        "ip": ip,
                        "hostname": None,
                        "mac": arp.get(ip),
                        "ports_open": r.get("ports_open", []),
                        "detection_method": r.get("method", "unknown")
                    }
            
            # PHASE 3: Add ARP devices ONLY if they're in our subnet and respond to ping
            # This catches devices that might have been missed but are definitely on the network
            for arp_ip in arp.keys():
                if (arp_ip.startswith(network_prefix + ".") and 
                    arp_ip != router_ip_use and 
                    arp_ip not in devices_by_ip and
                    _is_valid_device_ip(arp_ip)):
                    # Verify ARP entry is real by pinging
                    if await loop.run_in_executor(executor, lambda ip=arp_ip: _ping_sync(ip, timeout_ms=1000)):
                        devices_by_ip[arp_ip] = {
                            "ip": arp_ip,
                            "hostname": None,
                            "mac": arp.get(arp_ip),
                            "ports_open": [],
                            "detection_method": "arp+ping"
                        }
            
            # PHASE 4: Get hostnames for all verified devices
            def _get_hostname_sync(ip: str) -> Optional[str]:
                try:
                    return socket.gethostbyaddr(ip)[0]
                except Exception:
                    return None

            hostname_tasks = [loop.run_in_executor(executor, _get_hostname_sync, ip) for ip in devices_by_ip]
            hostname_results = await asyncio.gather(*hostname_tasks, return_exceptions=True)
            for ip, hn in zip(devices_by_ip, hostname_results):
                if isinstance(hn, str) and hn:
                    devices_by_ip[ip]["hostname"] = hn

            detected_devices = list(devices_by_ip.values())
            for d in detected_devices:
                d["status"] = "online"
                if not d.get("ports_open"):
                    d["ports_open"] = []
                # Identify device type
                d["device_type"] = _identify_device_type(d.get("hostname"), d.get("mac"))
                # Remove internal detection_method before sending to frontend
                d.pop("detection_method", None)

            return {
                "devices": detected_devices,
                "network_prefix": network_prefix,
                "router_ip": router_ip_use,
                "total_detected": len(detected_devices),
                "ips_scanned": len(ips_to_scan),
            }
        finally:
            executor.shutdown(wait=True)
    except Exception as e:
        import traceback
        print(f"[ERROR] Network scan failed: {e}")
        print(traceback.format_exc())
        return {
            "devices": [],
            "message": f"Scan failed: {str(e)}",
            "error": "scan_failed",
            "router_ip": router_ip_use if 'router_ip_use' in locals() else None,
            "ips_scanned": len(ips_to_scan) if 'ips_to_scan' in locals() else 0,
        }

@router.get("/verify-device")
@limiter.limit("10/minute")
async def verify_device_connection(
    request: Request,
    ip_address: str = Query(..., description="IP address to verify"),
    current_user: dict = Depends(get_current_user)
):
    """
    Verify that a device at the given IP is reachable and on the same network
    """
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get user's network settings
    settings = await db.network_settings.find_one({"userId": user_id})
    
    if not settings or not settings.get("networkPrefix"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please configure your router IP in settings first"
        )
    
    network_prefix = settings.get("networkPrefix")
    
    # Verify IP is valid
    try:
        ip_parts = ip_address.split('.')
        if len(ip_parts) != 4:
            raise ValueError("Invalid IP format")
        for part in ip_parts:
            num = int(part)
            if num < 0 or num > 255:
                raise ValueError("Invalid IP range")
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IP address format"
        )
    
    # Check if on same network
    device_prefix = '.'.join(ip_address.split('.')[:3])
    is_same_network = device_prefix == network_prefix
    
    if not is_same_network:
        return {
            "verified": False,
            "reachable": False,
            "same_network": False,
            "message": f"Warning: Device IP {ip_address} is not on your network ({network_prefix}.x). This may be a security risk.",
            "warning": "different_network"
        }
    
    # Test connectivity
    reachable = False
    hostname = None
    open_ports = []
    
    try:
        # Try common ports
        for port in [80, 443, 22, 23, 3389, 8080, 5000]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip_address, port))
                sock.close()
                if result == 0:
                    reachable = True
                    open_ports.append(port)
            except:
                continue
        
        # Try to get hostname
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
        except:
            pass
        
    except Exception as e:
        pass
    
    if reachable:
        return {
            "verified": True,
            "reachable": True,
            "same_network": True,
            "hostname": hostname,
            "open_ports": open_ports,
            "message": "Device is reachable and on your network"
        }
    else:
        return {
            "verified": False,
            "reachable": False,
            "same_network": True,
            "message": "Device IP is on your network but not currently reachable. Make sure the device is powered on and connected.",
            "warning": "not_reachable"
        }

@router.get("/monitoring/status")
async def monitoring_status(current_user: dict = Depends(require_admin)):
    return {"enabled": is_network_monitoring_enabled()}

@router.post("/monitoring/enable")
async def enable_monitoring(current_user: dict = Depends(require_admin)):
    start_network_monitoring()
    return {"enabled": is_network_monitoring_enabled()}

@router.post("/monitoring/disable")
async def disable_monitoring(current_user: dict = Depends(require_admin)):
    stop_network_monitoring()
    return {"enabled": is_network_monitoring_enabled()}
