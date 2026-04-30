# Mermaid diagrams for the dissertation

Copy a fenced block into [Mermaid Live Editor](https://mermaid.live), export **PNG** (high resolution if needed), insert in Word with caption.

**Placement** — see `REPORT_VISUALS_PLACEMENT.md` (Figures 5, 6, 7 alternative, 11).

---

## Figure 5 — Anomaly decision flow (Ch.9 §9.6)

```mermaid
flowchart TD
  A[Heartbeat received or sweep tick] --> B{Interval within expected + grace?}
  B -->|Yes| C[Stay / normalise status]
  B -->|No| D[Increment missed / anomaly score]
  D --> E{Repeated misses or IP change + offline?}
  E -->|No / transient| F[Low severity / log only]
  E -->|Yes| G[Escalate severity]
  G --> H[Create or update alert]
  H --> I[Notification pipeline per prefs]
```

---

## Figure 6 — Notification escalation (Ch.9 §9.7)

```mermaid
flowchart LR
  L[Low / info] --> E[Email / in-app]
  M[Medium] --> S[Email + SMS]
  H[High / critical] --> V[SMS + voice / max channel]
```

---

## Figure 7 — Data relationships (alternative to SVG; Ch.9 §9.8 or Ch.10 §10.4)

```mermaid
erDiagram
  USER ||--o{ DEVICE : owns
  DEVICE ||--o{ ALERT : generates
  USER ||--o| NOTIFY_PREFS : has
  DEVICE {
    string id
    datetime lastSeen
    string status
  }
  ALERT {
    string id
    string severity
    datetime created
  }
```

*(ER syntax is illustrative; MongoDB is document-oriented — mention that in caption.)*

---

## Figure 11 — Future-work roadmap (Ch.13)

```mermaid
timeline
    title Future enhancements (high level)
    section Near term
        Hardening & UX polish : Hardening & UX polish
        Richer dashboards : Richer dashboards
    section Mid term
        Adaptive thresholds : Adaptive thresholds
        Queue-backed ingestion : Queue-backed ingestion
    section Longer term
        ML-assisted anomaly : ML-assisted anomaly
        Smart-home / router integrations : Smart-home / router integrations
```

*(If `timeline` fails in your Mermaid version, use the flowchart below.)*

```mermaid
flowchart LR
  A[Current prototype] --> B[Threshold tuning & UX]
  B --> C[Scale-out / queues]
  C --> D[ML anomaly]
  D --> E[Integrations & commercial]
```

---

## Optional — layered threat (device → network → cloud → user)

```mermaid
flowchart BT
  U[User / SMB operator]
  C[Cloud / vendor APIs]
  N[Home router / Wi-Fi LAN]
  D[IoT devices]
  D --> N
  N --> C
  U --> N
  U --> C
```

Use in **Ch.6** only if you want another schematic beyond Figures 1–2.
