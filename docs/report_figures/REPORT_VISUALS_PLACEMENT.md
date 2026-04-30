# Report visuals — what was generated and where to place them

## If SVGs “don’t load”

1. **Open `PREVIEW_FIGURES.html` in Chrome or Edge** (double-click). All diagrams should render inline.  
2. **Microsoft Word** often handles **PNG** better than SVG: export from browser (screenshot the image) or open SVG in Inkscape / browser and save as PNG.  
3. Earlier files broke on **`&` in text** (invalid XML) and **corrupted Unicode**; all `FIGURE_*.svg` in this folder were rewritten as **strict XML** with ASCII-only labels. Re-copy from repo if you still have old files.

---

Your thesis uses **Figure 1–2** (Ch.6 threat landscape) and **Tables 1–4** (Ch.7–8) already. New assets below continue **global sequential figures** from **Figure 3** unless you insert optional STRIDE (see note).

| # | File(s) | Place in report (your TOC) | Caption suggestion |
|---|---------|----------------------------|--------------------|
| **Optional** | `FIGURE_OPTIONAL_STRIDE_lite.svg` | **Ch.6 §6.2** or **§6.4** — only if you want a STRIDE-style map *in addition to* Figures 1–2. If you add it as **Figure 3**, renumber **all following figures +1**. | *Figure X (Optional): STRIDE-oriented threat view for home/SMB IoT (simplified).* |
| **3** | `FIGURE_3_system_architecture.svg` | **Ch.9 §9.2** Overall System Architecture | *Figure 3: Layered system architecture (client, API, services, persistence; device heartbeat ingress).* |
| **4** | `FIGURE_4_heartbeat_sequence.svg` | **Ch.9 §9.5** Heartbeat Monitoring Mechanism | *Figure 4: Heartbeat processing and availability sweep (logical sequence).* |
| **5** | `REPORT_DIAGRAMS_MERMAID.md` → block “Anomaly” | **Ch.9 §9.6** Anomaly Detection Logic — export PNG from [mermaid.live](https://mermaid.live) | *Figure 5: Heuristic anomaly decision flow.* |
| **6** | `REPORT_DIAGRAMS_MERMAID.md` → “Escalation” | **Ch.9 §9.7** Alerting and Notification Design | *Figure 6: Notification escalation by severity.* |
| **7** | `REPORT_DIAGRAMS_MERMAID.md` → “ER” or `FIGURE_7_data_model.svg` | **Ch.9 §9.8** Data Storage *or* **Ch.10 §10.4** Data Modelling | *Figure 7: High-level data / collection relationships.* |
| **8** | `FIGURE_8_module_map.svg` | **Ch.10 §10.3** Backend Application Structure | *Figure 8: Backend module map (routes, services, middleware).* |
| **9** | `FIGURE_9_dashboard_wireframe.svg` (+ **replace with real screenshot** when possible) | **Ch.11 §11.3** Functional Testing *or* **Ch.10 §10.2** stack discussion | *Figure 9: Dashboard wireframe / device availability view (replace with screenshot if required).* |
| **10** | `FIGURE_10_performance_sketch.svg` | **Ch.11 §11.6** Performance and Reliability | *Figure 10: Qualitative view of monitoring load vs. response (illustrative).* |
| **11** | `REPORT_DIAGRAMS_MERMAID.md` → “Roadmap” | **Ch.13 §13.1** or end of **§13.7** Future Work | *Figure 11: High-level future-work roadmap.* |

**Already in repo (no change needed unless you tweak captions):**

| Asset | Location |
|-------|----------|
| Threat / attack-surface graphics | `FIGURE_4_1_attack_surface.svg`, `FIGURE_4_2_threat_categories.svg` — **Ch.6 §6.1**, **§6.2** |
| Research gap comparison | `TABLE_5_6_research_gap_comparison.html` / `.md` — **Ch.7 §7.6** as **Table 1** |
| Traceability | `TABLE_8_traceability_USER_TOC.html` / `TABLE_8_traceability_PASTE_WORD.md` — **Ch.8 §8.6** **Tables 2–4** |

**New table:**

| File | Location |
|------|----------|
| `TABLE_5_test_cases.html`, `.md` | **Ch.11 §11.2** or **§11.3** — **Table 5** (test / scenario evidencing) |

**Workflow:** For Mermaid diagrams, copy the block from `REPORT_DIAGRAMS_MERMAID.md` → Mermaid Live → **Export PNG** (300 dpi if required) → insert in Word → apply caption and List of Figures.

Update **§9.2** and **§9.5** text to cite **Figure 3** and **Figure 4** (not 5.1 / 5.2).
