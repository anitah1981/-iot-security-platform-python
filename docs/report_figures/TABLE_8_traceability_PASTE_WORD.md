# §8.6 — Traceability for Word (sequential Table 1–4)

**Numbering:** **Table 1** = research gap (Ch.7 §7.6), already in your report. **Tables 2–4** below = requirements traceability (paste into **Ch.8 §8.6**). Matches a **global** Figure 1 / Table 1 style throughout the thesis.

---

## Opening paragraph (paste under §8.6)

The following tables provide forward traceability from the project objectives in §5.3 through the functional requirements (FR1–FR8) and non-functional requirements (NFR1–NFR7) defined in this chapter, to the system design (Chapter 9), implementation (Chapter 10), and testing and evaluation (Chapter 11). **Table 2** maps each objective to the chapter where it is primarily evidenced. **Tables 3 and 4** map each requirement to the subsections that address it; subsection numbers match this report’s table of contents. The Obj. column indicates which objectives (O2–O5) each requirement supports: O2 requirements definition, O3 design, O4 implementation, O5 evaluation.

---

## Table 2 — Objectives to report chapters

*Table 2: Mapping of project objectives (§5.3) to report chapters.*

| Obj. | Objective (from §5.3) | Primary evidence in report |
|------|------------------------|----------------------------|
| O1 | Analyse security and availability risks in home/SMB IoT | Ch.6 (background); Ch.7 (literature; including Table 1 / §7.6 research gap) |
| O2 | Define functional and non-functional requirements | Ch.8 (this chapter; §8.3–§8.4); Tables 3–4 |
| O3 | Design architecture for registration, monitoring, anomaly detection | Ch.9 (system design) |
| O4 | Implement prototype (heartbeat, alerting) | Ch.10 (implementation) |
| O5 | Evaluate via structured testing and scenarios | Ch.11 (testing and evaluation) |
| O6 | Critically reflect; identify further development | Ch.12 (reflection); Ch.13 (future work) |

---

## Table 3 — Functional requirements traceability

*Table 3: FR1–FR8 mapped to design (Ch.9), implementation (Ch.10), and testing (Ch.11) subsections.*

| ID | Requirement (summary) | Obj. | Design (Ch.9) | Implementation (Ch.10) | Testing (Ch.11) |
|----|------------------------|------|---------------|------------------------|-----------------|
| FR1 | User registration and authentication | O2–O5 | §9.3–§9.4 | §10.3, §10.9 | §11.5 |
| FR2 | IoT device registration | O2–O5 | §9.4, §9.8 | §10.5 | §11.3.1 |
| FR3 | Device heartbeat monitoring | O2–O5 | §9.5 | §10.6 | §11.3.2 |
| FR4 | Availability status (online/offline/degraded) | O2–O5 | §9.3–§9.5 | §10.5–§10.6 | §11.3.2 |
| FR5 | Anomaly detection (behaviour / connectivity) | O2–O5 | §9.6 | §10.7 | §11.3.3 |
| FR6 | Alert generation and multi-channel notification | O2–O5 | §9.7 | §10.8 | §11.4 |
| FR7 | Historical logging and retention | O2–O5 | §9.8 | §10.4, §10.10 | §11.3, §11.6 |
| FR8 | Dashboard visualisation | O2–O5 | §9.3 | §10.2–§10.3 | §11.3 |

---

## Table 4 — Non-functional requirements traceability

*Table 4: NFR1–NFR7 mapped to design (Ch.9), implementation (Ch.10), and testing (Ch.11) subsections.*

| ID | Requirement (summary) | Obj. | Design (Ch.9) | Implementation (Ch.10) | Testing (Ch.11) |
|----|------------------------|------|---------------|------------------------|-----------------|
| NFR1 | Security (authentication, transport hardening, abuse resistance) | O2–O5 | §9.4, §9.9 | §10.9 | §11.5 |
| NFR2 | Privacy / data minimisation (GDPR-aligned) | O2–O5 | §6.5; §9.4, §9.8 | §10.4–§10.5, §10.9 | §11.5 |
| NFR3 | Usability for non-experts | O2–O5 | §9.3 | §10.2–§10.3 | §11.6 |
| NFR4 | Scalability | O2–O5 | §9.2, §9.8 | §10.10 | §11.6 |
| NFR5 | Reliability / false-positive control | O2–O5 | §9.5–§9.6 | §10.6–§10.7 | §11.3.2–§11.3.3 |
| NFR6 | Performance (timely heartbeats and alerts) | O2–O5 | §9.2 | §10.10 | §11.6 |
| NFR7 | Maintainability / modularity | O2–O5 | §9.2, §9.9 | §10.3 | §11.9 |

**Note:** NFR2 cites §6.5 (Background) as well as Ch.9. **§11.3** in FR7 refers to the functional testing block as a whole (§11.3.1–§11.3.3).

---

Styled HTML: `TABLE_8_traceability_USER_TOC.html`
