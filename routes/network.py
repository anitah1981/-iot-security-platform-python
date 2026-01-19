# routes/network.py - Network Monitoring & Change Detection
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Dict, Any, Optional
from bson import ObjectId
import socket
import asyncio

from database import get_database
from routes.auth import get_current_user
from services.network_monitor import NetworkMonitor, start_network_monitoring, stop_network_monitoring, is_network_monitoring_enabled
from middleware.security import limiter

router = APIRouter()

def _require_admin(user: dict):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

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
async def scan_for_devices(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Scan network for available devices (auto-detect IPs)
    Returns list of detected devices that can be added
    """
    db = await get_database()
    user_id = current_user["_id"]
    
    # Get user's network settings
    settings = await db.network_settings.find_one({"userId": user_id})
    
    if not settings or not settings.get("networkPrefix"):
        return {
            "devices": [],
            "message": "Please configure your router IP in settings first",
            "error": "no_router_ip"
        }
    
    network_prefix = settings.get("networkPrefix")
    router_ip = settings.get("routerIp", f"{network_prefix}.1")
    
    # Get user's existing devices
    existing_devices = await db.devices.find({
        "$or": [
            {"userId": user_id},
            {"user_id": user_id}
        ]
    }).to_list(length=1000)
    
    existing_ips = set(d.get("ipAddress") for d in existing_devices if d.get("ipAddress"))
    
    # Scan network for devices
    detected_devices = []
    
    async def check_ip(ip: str):
        """Check if IP is alive and get basic info"""
        try:
            # Quick port scan
            for port in [80, 443, 22, 8080, 5000]:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    if result == 0:
                        # Try to get hostname
                        try:
                            hostname, _, _ = socket.gethostbyaddr(ip)
                        except:
                            hostname = None
                        return {
                            "ip": ip,
                            "hostname": hostname,
                            "ports_open": [port],
                            "status": "online"
                        }
                except:
                    continue
            return None
        except Exception as e:
            return None
    
    # Scan IPs in network (limited to first 50 for performance)
    tasks = []
    for i in range(1, 51):  # Check .1 to .50
        ip = f"{network_prefix}.{i}"
        if ip not in existing_ips and ip != router_ip:
            tasks.append(check_ip(ip))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if result and isinstance(result, dict):
            detected_devices.append(result)
    
    return {
        "devices": detected_devices,
        "network_prefix": network_prefix,
        "router_ip": router_ip,
        "total_detected": len(detected_devices)
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
async def monitoring_status(current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    return {"enabled": is_network_monitoring_enabled()}

@router.post("/monitoring/enable")
async def enable_monitoring(current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    start_network_monitoring()
    return {"enabled": is_network_monitoring_enabled()}

@router.post("/monitoring/disable")
async def disable_monitoring(current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    stop_network_monitoring()
    return {"enabled": is_network_monitoring_enabled()}
