# Step-by-step: building report visuals

Use the same tool for every figure so the style matches (colours, font). **Recommended:** [diagrams.net](https://app.diagrams.net) (free) or **PowerPoint** with snap-to-grid.

---

## 1. Figures 1 & 2 — Threat landscape (Ch.6 §6.1 & §6.2; TOC may label them Figure 1 / 2)

**Done for you:** see `FIGURE_4_1_attack_surface.svg`, `FIGURE_4_2_threat_categories.svg`, and Mermaid sources in `FIGURE_4_1_4_2_threat_landscape.md`.

**Steps if you redraw by hand:**

1. Draw a **horizontal band** labelled “4.1 Expanded attack surface”.
2. Add **6 boxes** (device types from your text).
3. Draw arrows down to one box: **Wi-Fi / LAN / router**.
4. Branch to **Vendor cloud** and **Users (no IDS/SIEM)**.
5. Below, a second band **“4.2 Threats”** with 5 boxes (hijacking, DDoS, exfiltration, jamming, silent failure).
6. Add **dashed arrows** from network/user area down to threats (conceptual exposure).

---

## 2. Research-gap comparison table (§5.6–5.7)

**Ready-made:** `TABLE_5_6_research_gap_comparison.md` (Markdown) and `TABLE_5_6_research_gap_comparison.html` (open in browser → copy table → paste into Word). Columns: **cost**, **setup**, **visibility**, **hardware**, **privacy** for consumer apps vs enterprise SIEM vs Pro-Alert.

---

## 3. Requirements traceability (Ch.8 §8.6)

**Ready-made:** `TABLE_8_traceability_USER_TOC.html` / `TABLE_8_traceability_PASTE_WORD.md` — **Tables 2–4** (after **Table 1** at §7.6): objectives → chapters; FR; NFR. § columns for Ch.9–11.

---

## 4. Figure 7.1 — System architecture

1. **Three layers** (top to bottom): **Client** (browser / mobile) → **API + middleware** (FastAPI) → **Data** (MongoDB).
2. Side box: **Device agent** → `POST /api/heartbeat` → API.
3. Optional: **Stripe / Twilio** as small external boxes with dashed lines.
4. Export PNG, 300 dpi if the brief requires print quality.

---

## 5. Figure 9.2 — Heartbeat / sweep flow

1. Use **Insert → SmartArt → Process** in Word, or a sequence in diagrams.net.
2. Steps: **Device** → **Heartbeat API** → **Update lastSeen** → **Background sweep** → **Status offline?** → **Create alert** → **Notifications**.
3. For “decision”, use a **diamond** (yes/no).

---

## 6. Anomaly logic flowchart (Ch.9 §9.6 — optional figure)

1. Start → **Missed heartbeat?** → **Within grace?** → **Escalate severity** / **IP change + offline?**
2. Keep **3–6 decision nodes** max so it fits one page.

---

## 7. Notification escalation (Ch.9 §9.7 — optional)

1. **Horizontal ladder**: Low → Email → SMS → Voice (or your actual tiers).
2. Or a **small table**: Severity | Channel.

---

## 8. Data model sketch (Ch.9 §9.8 — optional)

1. **Boxes**: User, Device, Alert, NotificationPreferences.
2. **Lines**: User **1—*** Device; Device **1—*** Alert.
3. No need for every field — **5–8 labels** total.

---

## 9. Module tree (Ch.10 §10.3)

1. In VS Code or Explorer, copy **folder names** under `routes/`, `services/`, `middleware/`.
2. Paste into Word as **monospace** tree or recreate as boxes in diagrams.net.

---

## 10. Evidence screenshot (Ch.10–11)

1. Run app locally or use staging; open **dashboard** with devices **online/offline**.
2. **Win+Shift+S** (Snipping Tool) → crop; paste into Word.
3. Caption: *Figure 10.x: Dashboard showing device availability states after heartbeat simulation.*

---

## 11. Test case table (Ch.11)

1. Columns: **ID** | **Requirement** | **Steps** | **Expected** | **Result** | **Pass/Fail**.
2. 5–10 rows for **registration**, **heartbeat/offline**, **alert**, **auth**.

---

## 12. Future-work roadmap (Ch.13)

1. **Horizontal timeline**: *Now* → *ML anomaly* → *Scale* → *Integrations*.
2. Three bullets under each milestone.

---

## Export checklist

- [ ] Figure numbers match your TOC (e.g. architecture = **Figure 9.1** in Ch.9).
- [ ] Every figure **cited in text** before it appears.
- [ ] Caption **below** figure in Word; **List of figures** if required.
- [ ] Same font size for all figure text (e.g. 10–11 pt).
