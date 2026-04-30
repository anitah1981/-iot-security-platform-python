# Table 5 — Sample test scenarios (paste into Ch.11)

**Suggested location:** **Chapter 11** after **§11.2 Testing Strategy** or at start of **§11.3 Functional Testing**.  
**Caption:** *Table 5: Representative test scenarios and outcomes.*

| ID | Scenario | Steps (summary) | Expected | Actual (your run) | Pass / Fail |
|----|----------|-----------------|----------|-------------------|-------------|
| T1 | Device registration | Authenticate; POST/ UI create device with valid metadata | Device persisted; visible in list; owner scoped | | |
| T2 | Invalid device input | Submit missing required field or invalid enum | 4xx validation; no partial record | | |
| T3 | Heartbeat online | Send heartbeats within interval | Status online; `lastSeen` updates | | |
| T4 | Heartbeat → offline | Stop heartbeats past tolerance | Status offline/degraded; alert path triggered | | |
| T5 | Anomaly escalation | Repeated misses + IP change pattern (per your rules) | Severity increases vs single miss | | |
| T6 | Alert notify | Trigger alert; configured channels | Notification received or logged graceful failure | | |
| T7 | AuthZ boundary | Request another user’s device without permission | Denied | | |
| T8 | Rate limit / auth abuse | Rapid failed logins or heartbeat spam (if enabled) | Throttle / 429 as designed | | |

Fill **Actual** and **Pass/Fail** from your lab notes. Trim rows if space is tight (keep T1, T3, T4, T7 as minimum).
