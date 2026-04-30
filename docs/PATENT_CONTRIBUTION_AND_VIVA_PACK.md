# Patent Contribution and Viva Pack

This document consolidates:

1. Patent-relevant technical contribution write-up (report-ready)
2. Claim-to-implementation evidence mapping template
3. 3-4 minute viva script

Use this as a working draft for your June 2026 patent-aligned deliverable.

---

## 1) Patent-Relevant Technical Contribution and Validation

### 1.1 Technical Field and Problem Context

This project is in the field of IoT security monitoring, specifically detection and management of suspicious connectivity and behavioral events in consumer and small-business smart-device environments.

The practical problem addressed is that many systems either:

- operate as isolated vendor apps, or
- use simplistic single-signal logic (for example, "device offline = alert").

In real deployments this often causes high false positives, duplicate notifications, and weak incident context for post-event analysis.

Pro-Alert addresses this by combining device telemetry, heartbeat timing, temporal logic, incident grouping, and auditable outcomes across web and mobile.

The patent-relevant contribution is **not** generic SaaS features (login, billing, CRUD) in isolation; it is the technical method that transforms raw telemetry into higher-confidence incidents with controlled escalation and traceability.

### 1.2 Patent-Relevant Contribution

The contribution is a **multi-signal IoT incident detection and response method** that:

1. Ingests periodic heartbeat/status telemetry from devices and/or network agent
2. Applies timing-aware offline inference (rather than immediate binary failure)
3. Correlates events across devices/context within temporal windows
4. Produces deduplicated, severity-scored incident candidates
5. Routes outcomes through channel-aware notification and audit-linked timeline outputs

This is a technical pipeline from telemetry to actionable incident.

### 1.3 Why This Is More Than a Standard Dashboard

A conventional implementation surfaces isolated per-device offline events.

This method introduces:

- temporal filtering,
- cross-device correlation,
- incident-level aggregation,
- severity/escalation mapping, and
- auditable event-chain preservation.

Expected technical effects:

- lower false positives,
- fewer duplicate alerts,
- faster actionable detection,
- stronger post-incident accountability.

### 1.4 Claimed Novelty Framing (Project-Level)

The inventive step is framed as the **combination and sequencing** of:

- heartbeat-driven state inference with missed-window logic,
- cross-device temporal correlation,
- deduplicated incident aggregation,
- severity-based escalation,
- integrated audit/timeline evidence.

The novelty claim is on method/system behavior, not generic API/UI implementation alone.

### 1.5 System Implementation Mapping (Artefact to Contribution)

- **Ingestion and status updates:** heartbeat endpoints and sweep/background logic.
- **Detection/correlation:** threshold windows and temporal correlation rules.
- **Incident generation:** severity and deduplication to reduce alert noise.
- **Response:** channel-based notifications per user preference and severity.
- **Accountability:** audit logs and timeline evidence for post-incident review.
- **Deployability:** integrated into web/mobile product stack, showing practical utility.

### 1.6 Method Description (Algorithmic View)

1. Collect telemetry per device at interval `t`
2. Infer local state from heartbeat age + configured intervals + overrides
3. Apply temporal filters to suppress transient noise
4. Correlate multi-device/network signals inside window `W`
5. Compute severity from scope, duration, recurrence, and confidence signals
6. Deduplicate/merge equivalent event patterns
7. Dispatch notifications per channel and severity policy
8. Persist incident/audit records for traceability

### 1.7 Validation Strategy and Experimental Design

Compare:

- **Baseline:** simple per-device offline thresholding
- **Proposed:** correlated multi-signal method

Test scenarios:

1. Benign single-device dropout
2. Coordinated multi-device dropout
3. Intermittent unstable connectivity (flapping)
4. Sustained outage requiring escalation

Metrics:

- time-to-detect
- false positives
- false negatives
- duplicate alert count
- time-to-actionable incident
- (optional) notification relevance score

Evidence capture:

- logs and timestamps
- alert stream snapshots
- incident timeline screenshots
- audit log records linked to event chain

### 1.8 Expected Technical Effect

Relative to baseline, expected effects are:

- reduced alert noise via deduplication and incident grouping,
- improved signal fidelity via temporal/multi-device correlation,
- faster operational response through better severity prioritization,
- stronger accountability through integrated audit/timeline outputs.

### 1.9 Distinguishing Patent Core vs Commodity Features

- **Patent core:** multi-signal correlation + incident logic + technical effect.
- **Commodity features:** generic auth, billing, standard pages, typical CRUD.

This distinction avoids over-claiming and demonstrates mature technical/IP reasoning.

### 1.10 Limitations and Future Extensions

Current limitations:

- predominantly rule-based correlation,
- external-provider dependency for outbound channels,
- optimization currently aimed at household/SMB scale.

Future extension (PG-level direction):

- adaptive anomaly scoring models,
- confidence-weighted correlation from historical behavior,
- richer playbook/policy orchestration,
- larger-scale evaluation across diverse IoT estates.

### 1.11 IP and Disclosure Position

A provisional application has been filed. This deliverable should:

1. evidence practical implementation of the invention concept,
2. provide technical validation and traceability,
3. support transition to full claims before non-provisional filing.

Before further public disclosure, align wording with attorney/uni IP guidance.

---

## 2) Claim-to-Implementation Evidence Map (Template)

Use this table directly in your appendix and replace placeholders with final claim IDs and figure references.

| Claim Ref | Claim Element (Plain English) | Implementation Evidence (Code/Module) | Runtime/Test Evidence | Notes / Gaps |
|---|---|---|---|---|
| C1 | Method ingests periodic heartbeat/status signals | `routes/heartbeat.py`, `services/heartbeat_sweep.py`, `services/device_status_monitor.py` | Heartbeat logs, `lastSeen` transitions | Confirm timing windows documented |
| C2 | Offline inference uses temporal thresholds | `models.py` (`heartbeat_interval`, `offline_after_seconds`) + sweep logic | Scenario test: short dropout non-escalation | Add threshold parameter table |
| C3 | Multi-device temporal correlation generates incident candidates | `routes/incidents.py` and related correlation flow | Correlation screenshots + test outputs | Clarify correlation window constants |
| C4 | Deduplication reduces repeated equivalent alerts | Alert generation/handling services and routes | Before/after duplicate counts | Add compact metric chart |
| C5 | Severity maps to escalation/notification routing | `services/notification_service.py`, `routes/notification_preferences.py` | Channel tests by severity | Include one full trace per severity |
| C6 | Response chain is auditable | `services/audit_logger.py`, `routes/audit.py` | Audit/timeline screenshots | Map IDs across events for traceability |
| C7 | Session/security actions integrate with accountability model | `routes/auth.py` session revoke + MFA events | Session revoke + MFA logs | Supporting control; not core novelty |
| C8 | Practical industrial applicability across clients | `web/*`, `mobile/src/*` | Same incident flow visible on web/mobile | Include paired evidence captures |

### How to Use

- Replace `C1...C8` with provisional claim numbering if available.
- Keep claim language plain-English for examiners/assessors.
- Reference figures/tables from your results section.

---

## 3) 3-4 Minute Viva Script (Patent Section)

"Next, I will explain the patent-relevant contribution and how I validated it in the artefact.

The key point is that I am not claiming the entire app is novel. Features like authentication, billing, and standard dashboards are commodity engineering. The patent-relevant part is the **method** Pro-Alert uses to turn raw IoT telemetry into actionable incidents with better signal quality.

The method begins with heartbeat and status ingestion from devices and the local agent. Instead of treating every missing heartbeat as immediate critical failure, it applies temporal inference using heartbeat intervals and timeout windows, which reduces transient noise.

Events are then processed in a correlation window. Related multi-device and network-context changes are evaluated together, not as isolated alerts. The output is an incident candidate with severity classification, deduplication, and escalation routing.

The intended technical effect is improved operational quality: fewer duplicate alerts, lower false positives, and faster time-to-actionable incident.

To support this, I mapped each claim element to implementation modules and runtime evidence. For example:
- heartbeat ingestion and timeout logic map to heartbeat/sweep services,
- correlation and incident handling map to incidents and alerts flow,
- deduplication and severity routing map to notification logic and preferences,
- audit/timeline records provide traceability.

Validation compares this method against a baseline per-device threshold detector. Scenarios include benign single dropouts, coordinated outages, and unstable flapping connectivity. Metrics include detection latency, false positives/negatives, duplicate counts, and time-to-actionable incident.

This shows technical effect rather than purely UI improvements.

Finally, I explicitly separate patent core from product infrastructure:
the patent core is the multi-signal correlation and incident method; the broader app demonstrates practical deployability and industrial relevance.

So this section is designed to support both academic assessment and progression from provisional filing toward full claims."

---

## 4) Optional Checklist Before Final Submission

- [ ] Claim mapping table completed with final claim IDs
- [ ] Baseline vs proposed metrics table populated
- [ ] Evidence screenshots labeled and cross-referenced
- [ ] Patent core vs commodity distinction stated clearly
- [ ] Disclosure wording reviewed against provisional scope
- [ ] Attorney/uni IP office wording review completed

