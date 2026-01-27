# Alert Severity Classification Guide

This document explains how alerts are classified into severity levels: **Low**, **Medium**, **High**, and **Critical**.

## Overview

Alert severity determines:
- **Notification channels** that will be used (email, SMS, WhatsApp, voice)
- **Quiet hours behavior** (only critical alerts bypass quiet hours)
- **User attention priority** in the dashboard

---

## Severity Levels

### 🔴 **CRITICAL** - Immediate Action Required

**Definition:** Issues that pose an immediate security threat, cause complete device failure, or indicate a coordinated attack.

**Characteristics:**
- Requires immediate user attention
- Triggers all notification channels (email, SMS, WhatsApp, voice)
- Bypasses quiet hours
- Indicates active security breach or system-wide failure

**Examples:**
- **Connectivity:** Device offline unexpectedly (missed multiple heartbeats)
- **Security:** Potential WiFi jamming detected (3+ connectivity alerts in 1 hour)
- **Security:** Mass disconnection (3+ devices offline simultaneously - coordinated attack)
- **Power:** Complete power loss affecting multiple devices
- **System:** Complete device failure or compromise detected

**Notification Behavior:**
- ✅ Sent immediately via all enabled channels
- ✅ Bypasses quiet hours
- ✅ Voice calls triggered for critical alerts

---

### 🟠 **HIGH** - Urgent Attention Needed

**Definition:** Significant security concerns, suspicious activity, or major system issues that need prompt investigation.

**Characteristics:**
- Requires prompt attention (within hours)
- Triggers email, SMS, and WhatsApp (if enabled)
- Respects quiet hours (suppressed during quiet hours)

**Examples:**
- **Connectivity:** Device appears offline (missed heartbeats)
- **Security:** Suspicious activity detected on device
- **Security:** DNS hostname changed unexpectedly
- **Security:** Unknown device(s) detected on network
- **Security:** Device changed to suspicious IP address (0.0.0.0, 127.x.x.x, 169.254.x.x)
- **System:** Major system malfunction affecting device operation

**Notification Behavior:**
- ✅ Sent via email, SMS, WhatsApp (if enabled)
- ⚠️ Suppressed during quiet hours
- ❌ Voice calls not triggered

---

### 🟡 **MEDIUM** - Important but Not Urgent

**Definition:** Notable changes, anomalies, or issues that should be monitored but don't require immediate action.

**Characteristics:**
- Important to be aware of
- Triggers email and WhatsApp (if enabled)
- Respects quiet hours

**Examples:**
- **Security:** IP address changed (normal network behavior, but worth noting)
- **Security:** Rapid IP changes (3+ changes in 1 hour - potential instability)
- **Security:** Device behavior anomalies detected
- **System:** Signal strength low (degraded but still functional)
- **System:** Performance degradation detected
- **Connectivity:** Intermittent connectivity issues

**Notification Behavior:**
- ✅ Sent via email, WhatsApp (if enabled)
- ⚠️ Suppressed during quiet hours
- ❌ SMS and voice calls not triggered

---

### 🟢 **LOW** - Informational

**Definition:** Minor issues, routine changes, or informational alerts that don't require action.

**Characteristics:**
- Informational only
- Typically sent via email only
- Respects quiet hours

**Examples:**
- **System:** Minor performance fluctuations
- **System:** Routine maintenance notifications
- **Connectivity:** Brief connectivity hiccups (auto-recovered)
- **Security:** Minor configuration changes
- **System:** Low battery warning (device still operational)

**Notification Behavior:**
- ✅ Sent via email only (if enabled)
- ⚠️ Suppressed during quiet hours
- ❌ SMS, WhatsApp, and voice calls not triggered

---

## Alert Types and Typical Severities

### **Connectivity Alerts**
- **Critical:** Device offline unexpectedly, mass disconnection
- **High:** Device appears offline (missed heartbeats)
- **Medium:** Intermittent connectivity issues
- **Low:** Brief connectivity hiccups (auto-recovered)

### **Security Alerts**
- **Critical:** Potential WiFi jamming, coordinated attacks, active breach
- **High:** Suspicious activity, unknown devices, DNS changes, suspicious IPs
- **Medium:** IP address changes, rapid IP changes, behavior anomalies
- **Low:** Minor configuration changes

### **System Alerts**
- **Critical:** Complete device failure, system compromise
- **High:** Major system malfunction
- **Medium:** Signal strength low, performance degradation
- **Low:** Minor performance fluctuations, routine maintenance

### **Power Alerts**
- **Critical:** Complete power loss (multiple devices)
- **High:** Power issues affecting device operation
- **Medium:** Power fluctuations
- **Low:** Low battery warning (device still operational)

---

## Default Notification Channel Mapping

Based on severity, alerts are sent via:

| Severity | Email | SMS | WhatsApp | Voice |
|----------|-------|-----|----------|-------|
| **Critical** | ✅ | ✅ | ✅ | ✅ |
| **High** | ✅ | ✅ | ✅ | ❌ |
| **Medium** | ✅ | ❌ | ✅ | ❌ |
| **Low** | ✅ | ❌ | ❌ | ❌ |

*Note: Users can customize which severities trigger which channels in their notification preferences.*

---

## How Severity is Determined

### Automatic Assignment (by Monitoring Services)

1. **Heartbeat Sweep** (`services/heartbeat_sweep.py`)
   - Device offline → **HIGH** (connectivity)

2. **Security Monitor** (`services/security_monitor.py`)
   - Suspicious IP → **HIGH** (security)
   - Rapid IP changes → **MEDIUM** (security)
   - Potential jamming (3+ alerts/hour) → **CRITICAL** (security)
   - Mass disconnection (3+ devices) → **CRITICAL** (security)
   - Behavior anomalies → **MEDIUM** (security)

3. **Network Monitor** (`services/network_monitor.py`)
   - IP address change → **MEDIUM** (security)
   - DNS hostname change → **HIGH** (security)
   - Unknown device detected → **HIGH** (security)

### Manual Assignment

When creating alerts manually via API (`POST /api/alerts`), the severity must be specified in the request body:

```json
{
  "device_id": "...",
  "message": "Alert description",
  "severity": "high",  // Must be: "low", "medium", "high", or "critical"
  "type": "security"   // Must be: "connectivity", "power", "security", or "system"
}
```

---

## Best Practices for Severity Assignment

### When to Use **CRITICAL**
- Active security breach detected
- Complete system failure
- Coordinated attacks (multiple devices)
- Issues requiring immediate human intervention

### When to Use **HIGH**
- Security concerns (suspicious activity, unknown devices)
- Major functionality issues
- Issues that need prompt investigation (within hours)

### When to Use **MEDIUM**
- Notable changes worth monitoring
- Degraded performance (device still functional)
- Potential issues that may escalate

### When to Use **LOW**
- Informational only
- Routine changes
- Minor issues that don't affect functionality
- Auto-recovered issues

---

## Impact on Notification Features

### **Quiet Hours**
- **Critical alerts:** Always sent immediately (bypass quiet hours)
- **All other severities:** Suppressed during quiet hours (not sent until quiet hours end)

### **Escalation**
- Only applies to non-critical alerts
- If alert not resolved within escalation delay, may trigger additional notifications

---

## Summary

| Severity | Urgency | Notification Channels | Quiet Hours |
|----------|---------|----------------------|-------------|
| **Critical** | Immediate | All (Email, SMS, WhatsApp, Voice) | ❌ Bypassed |
| **High** | Urgent (hours) | Email, SMS, WhatsApp | ⚠️ Respected |
| **Medium** | Important | Email, WhatsApp | ⚠️ Respected |
| **Low** | Informational | Email only | ⚠️ Respected |

---

*Last Updated: January 2026*
