"""
services/security_monitor.py - Security monitoring and threat detection

Features:
- Network scan detection (abnormal port activity)
- Suspicious IP connections
- Device behavior anomalies

For MVP: Basic anomaly detection based on device patterns
For Production: Would integrate with network traffic analysis, IDS/IPS systems
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from bson import ObjectId


class SecurityMonitor:
    """Security monitoring service for IoT devices"""
    
    # Known malicious IP patterns (simplified for MVP)
    SUSPICIOUS_IP_PATTERNS = [
        "0.0.0.0",
        "127.",  # Loopback (suspicious if external device reports it)
        "169.254.",  # Link-local (APIPA)
    ]
    
    async def check_ip_change_anomaly(
        self, 
        db, 
        device_id: str, 
        new_ip: str, 
        old_ip: str,
        new_mac: Optional[str] = None,
        old_mac: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect suspicious IP address or MAC address changes
        
        Returns alert context if suspicious, None otherwise
        """
        # Check for MAC spoofing / IP Hijacking
        if old_mac and new_mac and old_mac.lower() != new_mac.lower():
            # The MAC address changed for the same device ID
            if old_ip == new_ip:
                # Same IP, different MAC -> ARP Spoofing / IP Hijacking
                return {
                    "alert_type": "mac_spoofing",
                    "reason": f"Network Interception Detected: Another device is attempting to impersonate your appliance at {new_ip}",
                    "old_mac": old_mac,
                    "new_mac": new_mac,
                    "severity": "critical"
                }
            else:
                # Different IP, different MAC -> Device replaced or spoofed
                return {
                    "alert_type": "device_replaced",
                    "reason": f"Hardware fingerprint changed for this device (MAC changed from {old_mac} to {new_mac})",
                    "old_mac": old_mac,
                    "new_mac": new_mac,
                    "severity": "high"
                }
        
        # If IP changed but MAC is the same, it's a legitimate router DHCP reassignment (Safe)
        if old_ip != new_ip and old_mac and new_mac and old_mac.lower() == new_mac.lower():
            # Legitimate IP change, do not alert
            return None
        # Check for suspicious IPs
        for pattern in self.SUSPICIOUS_IP_PATTERNS:
            if new_ip.startswith(pattern):
                return {
                    "alert_type": "suspicious_ip",
                    "reason": f"Device changed to suspicious IP: {new_ip}",
                    "old_ip": old_ip,
                    "new_ip": new_ip,
                    "severity": "high"
                }
        
        # Check for rapid IP changes (potential network instability or attack)
        device = await db.devices.find_one({"_id": ObjectId(device_id)})
        if device:
            ip_history = device.get("ipAddressHistory", [])
            if len(ip_history) > 5:
                # Check if there have been more than 3 IP changes in the last hour
                recent_changes = len(set(ip_history[-5:]))
                if recent_changes > 3:
                    return {
                        "alert_type": "rapid_ip_change",
                        "reason": f"Device changed IP {recent_changes} times recently",
                        "ip_history": ip_history[-5:],
                        "severity": "medium"
                    }
        
        return None
    
    async def check_connection_loss_pattern(
        self,
        db,
        device_id: str,
        alert_type: str = "connectivity"
    ) -> Optional[Dict[str, Any]]:
        """
        Detect patterns that might indicate WiFi jamming or DoS attacks
        
        Looks for:
        - Repeated connectivity alerts in short time period
        - Multiple devices going offline simultaneously
        """
        # Check for frequent disconnections (potential jamming)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_alerts = await db.alerts.count_documents({
            "deviceId": ObjectId(device_id),
            "type": "connectivity",
            "createdAt": {"$gte": cutoff}
        })
        
        if recent_alerts >= 3:
            return {
                "alert_type": "potential_jamming",
                "reason": f"Device has {recent_alerts} connectivity alerts in the last hour",
                "severity": "critical",
                "recommended_action": "Check for WiFi interference or jamming"
            }
        
        # Check for multiple devices offline simultaneously (coordinated attack or power/network issue)
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        all_recent_offline = await db.alerts.count_documents({
            "type": "connectivity",
            "severity": {"$in": ["high", "critical"]},
            "createdAt": {"$gte": recent_time}
        })
        
        if all_recent_offline >= 3:
            return {
                "alert_type": "mass_disconnection",
                "reason": f"{all_recent_offline} devices went offline in the last 5 minutes",
                "severity": "critical",
                "recommended_action": "Check network infrastructure and security"
            }
        
        return None
    
    async def analyze_device_behavior(
        self,
        db,
        device_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze device behavior for anomalies
        
        For MVP: Basic checks
        For Production: ML-based anomaly detection
        """
        if not metadata:
            return None
        
        device = await db.devices.find_one({"_id": ObjectId(device_id)})
        if not device:
            return None
        
        # Check for unexpected metadata changes
        anomalies = []
        
        # Example: Check if device type suddenly changed (could indicate compromise)
        if "type" in metadata and metadata["type"] != device.get("type"):
            anomalies.append({
                "anomaly": "device_type_mismatch",
                "expected": device.get("type"),
                "reported": metadata["type"]
            })
        
        # Check for signal strength anomalies (sudden drops might indicate jamming)
        current_signal = metadata.get("signal_strength")
        historical_signal = device.get("signalStrength")
        
        if current_signal is not None and historical_signal is not None:
            if current_signal < historical_signal - 40:  # 40 dB drop is significant
                anomalies.append({
                    "anomaly": "signal_strength_drop",
                    "previous": historical_signal,
                    "current": current_signal,
                    "drop": historical_signal - current_signal
                })
        
        if anomalies:
            return {
                "alert_type": "behavior_anomaly",
                "reason": "Device behavior anomalies detected",
                "anomalies": anomalies,
                "severity": "medium"
            }
        
        return None


# Singleton instance
_security_monitor = SecurityMonitor()


def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor instance"""
    return _security_monitor
