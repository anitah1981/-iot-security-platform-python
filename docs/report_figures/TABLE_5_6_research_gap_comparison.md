# Comparison table — research gap (Section 5.6–5.7)

**Suggested caption:** *Table 5.1: Comparison of consumer IoT applications, enterprise SIEM-style monitoring, and the proposed solution across deployment and privacy dimensions.*

**Where to use:** After the “Identified research gap” or “Commercial and academic solutions” discussion (§5.5–5.6), before §5.7 Summary.

**How to use in Word:**  
- Copy the **Markdown table** below (Word 365 can paste tables from some formats), or  
- Open **`TABLE_5_6_research_gap_comparison.html`** in a browser, select the table, copy, paste into Word, then apply your thesis table style.

---

## Markdown (version for editing)

| Dimension | Consumer / vendor IoT apps | Enterprise SIEM / IDS | Pro-Alert (this project) |
|-----------|----------------------------|------------------------|---------------------------|
| **Cost** | Typically low incremental cost (bundled with device; may include subscriptions per vendor). | High: licences, infrastructure, and skilled staff. | Low to moderate: software hosting and optional notification services (e.g. SMS); no enterprise licence model assumed. |
| **Setup** | Low: pairing and vendor app install; minimal technical skill. | High: integration with logs, agents, network taps, tuning, and ongoing administration. | Moderate: user account, device registration, optional lightweight agent on an existing LAN host for heartbeats. |
| **Visibility** | Fragmented: one app per vendor; weak cross-device and cross-brand situational awareness. | Strong within instrumented corporate estates; unified dashboards and correlation. | Consolidated dashboard for registered devices; emphasis on **availability** and **heartbeat-style** status rather than full traffic analytics. |
| **Hardware** | None beyond phones, hubs, and the IoT devices themselves. | Often additional appliances, agents, collectors, or TAPs. | **No dedicated monitoring appliance required**; operates as a cloud-hosted (or self-hosted) service with optional agent on commodity hardware. |
| **Privacy** | Data flows to multiple vendor clouds; policies vary. | Centralised logging and inspection; strong governance needed for proportionality and retention. | **Metadata-oriented** monitoring (e.g. status, timestamps, connectivity indicators); avoids deep packet inspection and payload capture as a design choice, aligning with minimisation goals. |

---

## Notes for the report body

- Use the table to **justify the gap**: row **Visibility** + **Cost** shows why SMB/home users lack an affordable middle ground.
- **Pro-Alert** row should match what you actually implemented (adjust wording if your deployment differs, e.g. fully self-hosted).
