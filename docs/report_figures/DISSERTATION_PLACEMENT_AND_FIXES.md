# Where each asset goes (your TOC: Ch.4 Abstract … Ch.14 Conclusion)

Your **contents list** uses **Chapter 4 = Abstract**, **Chapter 5 = Introduction**, **Chapter 6 = Background**, **Chapter 7 = Literature**, **Chapter 8 = Requirements**, **Chapter 9 = System Design**, **Chapter 10 = Implementation**, **Chapter 11 = Testing**, **Chapter 12 = Reflection**, **Chapter 13 = Future work**, **Chapter 14 = Conclusion**.

---

## Figures — placement vs your Table of Figures

| Your figure | Put the image after / in | File in repo (if using SVG) |
|-------------|--------------------------|-----------------------------|
| **Figure 1** | **Ch.6 §6.1** (Growth of IoT / attack surface) | `FIGURE_4_1_attack_surface.svg` |
| **Figure 2** | **Ch.6 §6.2** (IoT-specific threats) | `FIGURE_4_2_threat_categories.svg` |

### Research gap: table, not a figure

If any draft text calls the comparison grid “Figure 3”, use a **table** instead:

- **Table 1** in **Ch.7 §7.6** (Identified Research Gap) — keep as the first numbered table if you use global **Table 1, 2, 3…**  
- Source: `TABLE_5_6_research_gap_comparison.html` / `.md` — caption **Table 1** if you use sequential numbering.

---

## Requirements traceability (Chapter 8)

**Ready-made:** `TABLE_8_traceability_USER_TOC.html` (browser → copy tables) or **`TABLE_8_traceability_PASTE_WORD.md`** — **Tables 2–4** for **Ch.8 §8.6**, using **global sequential** numbering after **Table 1** (research gap at §7.6).

| Table | Place | Role |
|-------|--------|------|
| **Table 1** | **Ch.7 §7.6** | Research gap comparison (already in your draft) |
| **Table 2** | **§8.6** | Objectives → chapters |
| **Table 3** | **§8.6** | FR traceability |
| **Table 4** | **§8.6** | NFR traceability |

Suggested lead-in sentence:

*Tables 2–4 trace objectives and requirements forward to system design (Ch.9), implementation (Ch.10), and testing and evaluation (Ch.11).*

### § columns (your headings)

| Topic | Design | Implementation | Testing |
|-------|--------|----------------|--------|
| | **Ch.9** | **Ch.10** | **Ch.11** |
| Auth / security | §9.3–9.4, §9.9 | §10.3, §10.9 | §11.5 |
| Devices | §9.4, §9.8 | §10.5 | §11.3.1 |
| Heartbeat / status | §9.5 | §10.6 | §11.3.2 |
| Anomaly | §9.6 | §10.7 | §11.3.3 |
| Alerts | §9.7 | §10.8 | §11.4 |
| Data / history | §9.8 | §10.4, §10.10 | §11.3, §11.6 |
| Dashboard / UI | §9.3 | §10.2–10.3 | §11.3 |
| Privacy (legal context) | **§6.5** (Background) + Ch.9 as needed | §10.4–10.5, §10.9 | §11.5 |

Legacy file `TABLE_7_traceability_USER_TOC.html` used **Ch.8–10** as design/impl/test; your document uses **Ch.9–11** — use **`TABLE_8_traceability_USER_TOC.html`** instead.

---

## Figures to add (System Design, Chapter 9)

Your draft cites **Figure 5.1** and **Figure 5.2** inside **Ch.9** — renumber to match **Chapter 9**:

| Draft citation | Should become | Section |
|----------------|---------------|---------|
| Figure 5.1 (system architecture) | **Figure 9.1** | **§9.2** Overall System Architecture |
| Figure 5.2 (heartbeat flow) | **Figure 9.2** | **§9.5** Heartbeat Monitoring Mechanism |

Add both to the **Table of Figures**.

---

## Cross-reference fixes (search in Word)

| Find (wrong) | Replace with |
|--------------|--------------|
| **Chapter 2** (background / problem definition) | **Chapter 6** |
| **Chapter 3** (literature) | **Chapter 7** |
| **Chapter 4** (requirements) | **Chapter 8** |
| **Chapter 4** (design) — in design chapter intro | **Chapter 8** (requirements) |
| **Chapter 5** (design) — in implementation intro | **Chapter 9** |
| **Chapter 4** (requirements) — in implementation intro | **Chapter 8** |
| **Chapter 1** (objectives) | **Chapter 5** or **§5.3** |
| “requirements … **Chapter 2**” and “**Chapter 3**” in **§8.1** | **Chapter 6** and **Chapter 7** |

**§5.6 Structure of the Report** — your paragraph (**Ch.6** background through **Ch.14** conclusion) **matches** this TOC; no change needed unless wording tweaks.

---

## Duplicate / typo text (Introduction)

- **§5.1** — Remove duplicate “However, this rapid adoption…” sentence (keep one version).
- **§5.5** — Full stop after “…monitoring of device status information”.

---

## Suggested List of Tables

| Item |
|------|
| Table 1 Comparison consumer / SIEM / proposed solution (research gap) |
| Table 2 Objectives → chapters |
| Table 3 FR traceability |
| Table 4 NFR traceability |

## Suggested List of Figures (extend your current two)

| Item |
|------|
| Figure 1 … attack surface … |
| Figure 2 … threat categories … |
| Figure 9.1 System architecture … |
| Figure 9.2 Heartbeat processing flow … |

---

## Quick checklist

- [ ] **§8.1** — fix “Chapter 2/3” → **6/7**; **§8.6** — add **Tables 2–4** (traceability); “Chapter 1” → **§5.3** / **Ch.5**.  
- [ ] **§9.1** — requirements = **Chapter 8**; **5.1/5.2** → **9.1/9.2**; insert figures **9.1**, **9.2**.  
- [ ] **§10.1** — design = **Chapter 9**; requirements = **Chapter 8**.  
- [ ] **§12.2** — objectives = **Chapter 5** / **§5.3**.  
- [ ] **§7.6** — **Table 1** (research gap); **List of Tables** includes **Tables 1–4**.  
- [ ] Lists of tables/figures updated.
