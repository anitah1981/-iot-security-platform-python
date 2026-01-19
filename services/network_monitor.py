# services/network_monitor.py - Network Change Detection & Monitoring
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from bson import ObjectId
import asyncio
import socket

from database import get_database
from services.notification_service import send_alert_notification


class NetworkMonitor:
    """Monitor network changes: DNS changes, unknown IPs, new devices"""
    
    def __init__(self):
        self.check_interval_seconds = 30  # Check every 30 seconds
        self.is_running = False
    
    async def check_network_changes(self):
        """Main monitoring loop - checks for network changes"""
        db = await get_database()
        
        # Get all devices
        devices = await db.devices.find({}).to_list(length=1000)
        
        for device in devices:
            current_ip = device.get("ipAddress")
            if not current_ip:
                continue
            
            # Check for IP changes
            await self._check_ip_change(device, current_ip, db)
            
            # Check for DNS changes
            await self._check_dns_change(device, current_ip, db)
            
            # Check for unknown IPs on network
            await self._check_unknown_ips(device, db)
    
    async def _check_ip_change(self, device: Dict, current_ip: str, db):
        """Check if device IP has changed"""
        device_id = device.get("_id")
        device_name = device.get("name", "Unknown Device")
        
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
            # Try to resolve IP to hostname
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            
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
            for i in range(1, 255):
                test_ip = f"{network_prefix}.{i}"
                if test_ip not in known_ips and test_ip != device_ip:
                    # Quick connectivity check (simplified)
                    is_alive = await self._ping_ip(test_ip)
                    if is_alive:
                        unknown_ips.append(test_ip)
            
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
        try:
            # Try to connect to common ports
            for port in [80, 443, 22, 23, 3389]:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    if result == 0:
                        return True
                except:
                    continue
            return False
        except Exception:
            return False
    
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


def start_network_monitoring():
    """Start network monitoring in background"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = NetworkMonitor()
        # Run in background thread
        import threading
        import asyncio
        
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_monitor_instance.run_monitoring_loop())
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()


def stop_network_monitoring():
    """Stop network monitoring"""
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance.stop()
        _monitor_instance = None
