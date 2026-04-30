"""
Export docs/report_figures/*.svg to report/figures/<same basename>.pdf
Creates placeholder PDFs for screenshot-only figures (login, alerts).

Usage (from repo root):
  pip install svglib reportlab
  python scripts/export_report_figures_to_pdf.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = ROOT / "docs" / "report_figures"
OUT_DIR = ROOT / "report" / "figures"

# Basenames that must exist for LaTeX (see report/chapters/figure-basenames.tex)
SVG_MAP = [
    "FIGURE_4_1_attack_surface",
    "FIGURE_4_2_threat_categories",
    "FIGURE_3_system_architecture",
    "FIGURE_9_dashboard_wireframe",
    "FIGURE_4_heartbeat_sequence",
    "FIGURE_7_data_model",
    "FIGURE_8_module_map",
    "FIGURE_10_performance_sketch",
]

PLACEHOLDERS = {
    "FIGURE_SCREEN_LOGIN": "Placeholder: replace with login / authentication screenshot (export as PDF).",
    "FIGURE_SCREEN_ALERTS": "Placeholder: replace with active and resolved alerts screenshot (export as PDF).",
}


def svg_to_pdf(svg_path: Path, pdf_path: Path) -> None:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF

    drawing = svg2rlg(str(svg_path))
    if drawing is None:
        raise RuntimeError(f"svglib could not parse: {svg_path}")
    renderPDF.drawToFile(drawing, str(pdf_path))


def write_placeholder(pdf_path: Path, message: str) -> None:
    w, h = A4
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.setFont("Helvetica", 11)
    y = h - 72
    for line in message.split(". "):
        if line.strip():
            c.drawString(72, y, (line.strip() + ("." if not line.endswith(".") else ""))[:100])
            y -= 16
    c.rect(72, 72, w - 144, h - 200, stroke=1, fill=0)
    c.save()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    for base in SVG_MAP:
        svg = SVG_DIR / f"{base}.svg"
        pdf = OUT_DIR / f"{base}.pdf"
        if not svg.is_file():
            errors.append(f"Missing SVG: {svg}")
            continue
        try:
            svg_to_pdf(svg, pdf)
            print(f"OK {pdf.name}")
        except Exception as e:
            errors.append(f"{base}: {e}")

    for base, msg in PLACEHOLDERS.items():
        pdf = OUT_DIR / f"{base}.pdf"
        try:
            write_placeholder(pdf, msg)
            print(f"OK {pdf.name} (placeholder)")
        except Exception as e:
            errors.append(f"{base}: {e}")

    if errors:
        print("\nWarnings/errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
