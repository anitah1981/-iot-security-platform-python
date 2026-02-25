# services/network_monitor.py - Network Change Detection & Monitoring
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from bson import ObjectId
import asyncio
import socket
import os

from database import get_database
from services.notification_service import send_alert_notification


class NetworkMonitor:
    """Monitor network changes: DNS changes, unknown IPs, new devices"""
    
    def __init__(self):
        self.check_interval_seconds = int(os.getenv("NETWORK_MONITOR_INTERVAL", "30"))
        self.max_devices = int(os.getenv("NETWORK_MONITOR_MAX_DEVICES", "200"))
        self.unknown_ip_limit = int(os.getenv("NETWORK_MONITOR_UNKNOWN_IP_LIMIT", "50"))
        self.unknown_ip_devices_per_cycle = int(os.getenv("NETWORK_MONITOR_UNKNOWN_IP_DEVICES_PER_CYCLE", "3"))
        self.unknown_ip_timeout_seconds = float(os.getenv("NETWORK_MONITOR_UNKNOWN_IP_TIMEOUT", "4"))
        self.is_running = False
    
    async def check_network_changes(self):
        """Main monitoring loop - checks for network changes"""
        db = await get_database()
        
        # Get all devices
        devices = await db.devices.find({}).to_list(length=self.max_devices)
        unknown_ip_checks = 0
        
        for device in devices:
            current_ip = device.get("ipAddress")
            if not current_ip:
                continue
            
            # Check for IP changes
            await self._check_ip_change(device, current_ip, db)
            
            # Check for DNS changes
            await self._check_dns_change(device, current_ip, db)
            
            # Check for unknown IPs on network
            if unknown_ip_checks < self.unknown_ip_devices_per_cycle:
                try:
                    await asyncio.wait_for(
                        self._check_unknown_ips(device, db),
                        timeout=self.unknown_ip_timeout_seconds
                    )
                except asyncio.TimeoutError:
                    print("[WARN] Unknown IP scan timed out for device", device.get("_id"))
                unknown_ip_checks += 1

            await asyncio.sleep(0)
    
    @staticmethod
    def _is_likely_router_ip(ip: str) -> bool:
        """Avoid creating 'IP changed to router' false alerts."""
        if not ip or ip in ("0.0.0.0", "127.0.0.1"):
            return True
        parts = ip.strip().split(".")
        if len(parts) != 4:
            return False
        try:
            if int(parts[3]) == 1:
                return True
        except ValueError:
            pass
        return False

    async def _check_ip_change(self, device: Dict, current_ip: str, db):
        """Check if device IP has changed"""
        device_id = device.get("_id")
        device_name = device.get("name", "Unknown Device")
        # Don't create "IP changed to X" when X is a router/gateway (common false positive)
        if self._is_likely_router_ip(current_ip):
            return
        # Optionally skip if current_ip matches user's configured router
        user_id = device.get("userId") or device.get("user_id")
        if user_id:
            settings = await db.network_settings.find_one({"userId": user_id})
            router = (settings or {}).get("routerIp") or (settings or {}).get("router_ip")
            if router and (current_ip.strip() == router.strip()):
                return

        # Get IP history
        ip_history = device.get("ipAddressHistory", [])

        # Get last known IP from history
        if ip_history and len(ip_history) > 1:
            last_ip = ip_history[-2] if len(ip_history) >= 2 else ip_history[-1]

            if last_ip != current_ip:
                # IP has changed - check if we already alerted recently
                recent_alert = await db.alerts.find_one({
                    "deviceId": device_id,
                    "message": {"$regex": f"IP address changed from {last_ip}"},
                    "createdAt": {"$gte": datetime.utcnow() - timedelta(hours=1)}
                })
                
                if not recent_alert:
                    # Create alert for IP change
                    alert_doc = {
                        "deviceId": device_id,
                        "message": f"IP address changed from {last_ip} to {current_ip}",
                        "severity": "medium",
                        "type": "security",
                        "context": {
                            "old_ip": last_ip,
                            "new_ip": current_ip,
                            "change_type": "ip_change"
                        },
                        "resolved": False,
                        "resolvedAt": None,
                        "createdAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow()
                    }
                    
                    result = await db.alerts.insert_one(alert_doc)
                    
                    # Send notifications
                    await send_alert_notification(
                        str(result.inserted_id),
                        str(device_id),
                        alert_doc["message"],
                        alert_doc["severity"]
                    )
    
    async def _check_dns_change(self, device: Dict, ip_address: str, db):
        """Check if DNS resolution for device has changed"""
        device_id = device.get("_id")
        device_name = device.get("name", "Unknown Device")
        
        try:
            # Try to resolve IP to hostname (offload blocking call)
            hostname, _, _ = await asyncio.to_thread(socket.gethostbyaddr, ip_address)
            
            # Get stored DNS info
            stored_hostname = device.get("dnsHostname")
            stored_ip = device.get("dnsResolvedIp")
            
            if stored_hostname and stored_hostname != hostname:
                # DNS hostname changed
                recent_alert = await db.alerts.find_one({
                    "deviceId": device_id,
                    "message": {"$regex": "DNS hostname changed"},
                    "createdAt": {"$gte": datetime.utcnow() - timedelta(hours=1)}
                })
                
                if not recent_alert:
                    alert_doc = {
                        "deviceId": device_id,
                        "message": f"DNS hostname changed from {stored_hostname} to {hostname}",
                        "severity": "high",
                        "type": "security",
                        "context": {
                            "old_hostname": stored_hostname,
                            "new_hostname": hostname,
                            "ip": ip_address,
                            "change_type": "dns_change"
                        },
                        "resolved": False,
                        "resolvedAt": None,
                        "createdAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow()
                    }
                    
                    result = await db.alerts.insert_one(alert_doc)
                    
                    await send_alert_notification(
                        str(result.inserted_id),
                        str(device_id),
                        alert_doc["message"],
                        alert_doc["severity"]
                    )
            
            # Update device with current DNS info
            await db.devices.update_one(
                {"_id": device_id},
                {
                    "$set": {
                        "dnsHostname": hostname,
                        "dnsResolvedIp": ip_address,
                        "dnsLastChecked": datetime.utcnow()
                    }
                }
            )
            
        except (socket.herror, socket.gaierror, OSError):
            # Cannot resolve - might be offline or not responding
            pass
        except Exception as e:
            print(f"[ERROR] DNS check failed for {device_name}: {e}")
    
    async def _check_unknown_ips(self, device: Dict, db):
        """Check for unknown IPs on the same network"""
        device_ip = device.get("ipAddress")
        if not device_ip:
            return
        
        # Extract network prefix (e.g., 192.168.1.x)
        try:
            ip_parts = device_ip.split('.')
            if len(ip_parts) != 4:
                return
            
            network_prefix = '.'.join(ip_parts[:3])  # 192.168.1
            
            # Get user's known devices
            user_id = device.get("userId") or device.get("user_id")
            if not user_id:
                return
            
            # Get all devices for this user/family
            family_id = device.get("family_id")
            if family_id:
                known_devices = await db.devices.find({
                    "family_id": family_id
                }).to_list(length=1000)
            else:
                known_devices = await db.devices.find({
                    "$or": [
                        {"userId": user_id},
                        {"user_id": user_id}
                    ]
                }).to_list(length=1000)
            
            # Build set of known IPs
            known_ips = set()
            for d in known_devices:
                ip = d.get("ipAddress")
                if ip:
                    known_ips.add(ip)
            
            # Scan network for unknown IPs (simplified - ping common IPs)
            # In production, use proper network scanning
            unknown_ips = []
            for i in range(1, self.unknown_ip_limit + 1):
                test_ip = f"{network_prefix}.{i}"
                if test_ip not in known_ips and test_ip != device_ip:
                    # Quick connectivity check (simplified)
                    is_alive = await self._ping_ip(test_ip)
                    if is_alive:
                        unknown_ips.append(test_ip)
                if i % 10 == 0:
                    await asyncio.sleep(0)
            
            # If we found unknown IPs, create alert
            if unknown_ips:
                # Check if we already alerted recently
                recent_alert = await db.alerts.find_one({
                    "deviceId": device.get("_id"),
                    "type": "security",
                    "message": {"$regex": "Unknown device detected"},
                    "createdAt": {"$gte": datetime.utcnow() - timedelta(hours=6)}
                })
                
                if not recent_alert:
                    alert_doc = {
                        "deviceId": device.get("_id"),
                        "message": f"Unknown device(s) detected on network: {', '.join(unknown_ips[:5])}" + 
                                  (f" and {len(unknown_ips)-5} more" if len(unknown_ips) > 5 else ""),
                        "severity": "high",
                        "type": "security",
                        "context": {
                            "unknown_ips": unknown_ips,
                            "network_prefix": network_prefix,
                            "change_type": "unknown_device"
                        },
                        "resolved": False,
                        "resolvedAt": None,
                        "createdAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow()
                    }
                    
                    result = await db.alerts.insert_one(alert_doc)
                    
                    await send_alert_notification(
                        str(result.inserted_id),
                        str(device.get("_id")),
                        alert_doc["message"],
                        alert_doc["severity"]
                    )
        
        except Exception as e:
            print(f"[ERROR] Unknown IP check failed: {e}")
    
    async def _ping_ip(self, ip: str, timeout: float = 1.0) -> bool:
        """Check if an IP is alive (simplified ping)"""
        def _sync_ping(target_ip: str, target_timeout: float) -> bool:
            try:
                for port in [80, 443, 22, 23, 3389]:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(target_timeout)
                        result = sock.connect_ex((target_ip, port))
                        sock.close()
                        if result == 0:
                            return True
                    except Exception:
                        continue
                return False
            except Exception:
                return False

        return await asyncio.to_thread(_sync_ping, ip, timeout)
    
    async def run_monitoring_loop(self):
        """Run continuous monitoring loop"""
        self.is_running = True
        print(f"[Network Monitor] Started monitoring network changes (checking every {self.check_interval_seconds} seconds)")
        
        while self.is_running:
            try:
                await self.check_network_changes()
            except Exception as e:
                print(f"[ERROR] Network monitor error: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval_seconds)
    
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        print("[Network Monitor] Stopped monitoring")


# Global instance
_monitor_instance: Optional[NetworkMonitor] = None
_monitor_task: Optional[asyncio.Task] = None


def is_network_monitoring_enabled() -> bool:
    return _monitor_instance is not None and _monitor_instance.is_running


def start_network_monitoring():
    """Start network monitoring in background (current event loop)"""
    global _monitor_instance, _monitor_task
    if _monitor_instance is None:
        _monitor_instance = NetworkMonitor()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            _monitor_task = loop.create_task(_monitor_instance.run_monitoring_loop())
    elif not _monitor_instance.is_running:
        _monitor_instance.is_running = True


def stop_network_monitoring():
    """Stop network monitoring"""
    global _monitor_instance, _monitor_task
    if _monitor_instance:
        _monitor_instance.stop()
        _monitor_instance = None
    if _monitor_task:
        _monitor_task.cancel()
        _monitor_task = None
