"""
Extract ICA_1.docx body in order (paragraphs, tables, images) for LaTeX merge.
Run: python scripts/docx_extract_ica1.py
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "report" / "ICA_1.docx"
OUT_DIR = ROOT / "report" / "figures"
META_DIR = ROOT / "report" / "_ica1_extract"


def tex_escape(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\\", "\\textbackslash{}")
    s = s.replace("&", "\\&")
    s = s.replace("%", "\\%")
    s = s.replace("#", "\\#")
    s = s.replace("_", "\\_")
    s = s.replace("{", "\\{")
    s = s.replace("}", "\\}")
    s = s.replace("^", "\\textasciicircum{}")
    s = s.replace("~", "\\textasciitilde{}")
    s = s.replace("\u2019", "'")
    s = s.replace("\u2018", "'")
    s = s.replace("\u201c", "``")
    s = s.replace("\u201d", "''")
    s = s.replace("\u2013", "--")
    s = s.replace("\u2014", "---")
    s = s.replace("\u00a0", "~")
    s = s.replace("\u00a7", "\\S{}")
    s = s.replace("\u2011", "-")
    s = s.replace("\u2026", "\\ldots{}")
    s = s.replace("\u2192", "$\\rightarrow$")
    return s


def table_to_tex(tbl) -> str:
    rows = []
    for row in tbl.rows:
        cells = [tex_escape(c.text.strip().replace("\n", " ")) for c in row.cells]
        rows.append(cells)
    if not rows:
        return ""
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    w = 0.92 / max(n, 1)
    colspec = "".join(f"p{{{w:.3f}\\textwidth}}" for _ in range(n))
    lines = [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule"]
    for i, r in enumerate(rows):
        lines.append(" & ".join(r) + " \\\\")
        if i == 0 and len(rows) > 1:
            lines.append("\\midrule")
        elif 0 < i < len(rows) - 1:
            lines.append("\\midrule")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    return "\n".join(lines)


def extract_images_from_docx() -> dict[str, Path]:
    """rId -> extracted file path (png)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(DOCX)
    rels_xml = z.read("word/_rels/document.xml.rels").decode("utf-8")
    rid_to_target: dict[str, str] = {}
    for m in re.finditer(
        r'<Relationship[^>]+Id="([^"]+)"[^>]+Target="([^"]+)"', rels_xml
    ):
        rid, target = m.group(1), m.group(2)
        if target.startswith("media/"):
            rid_to_target[rid] = "word/" + target.replace("\\", "/")
    out: dict[str, Path] = {}
    for rid, internal in rid_to_target.items():
        if internal not in z.namelist():
            continue
        ext = Path(internal).suffix.lower() or ".bin"
        dest = META_DIR / f"embed_{rid}{ext}"
        dest.write_bytes(z.read(internal))
        out[rid] = dest
    return out


def blip_rids(paragraph_element) -> list[str]:
    rids = []
    for blip in paragraph_element.iter(qn("a:blip")):
        r = blip.get(qn("r:embed"))
        if r:
            rids.append(r)
    return rids


def main() -> None:
    rid_files = extract_images_from_docx()
    d = Document(DOCX)
    body = d.element.body
    sequence: list[tuple] = []

    for child in body:
        tag = child.tag
        if tag == qn("w:p"):
            texts = []
            for t in child.iter(qn("w:t")):
                if t.text:
                    texts.append(t.text)
            para_text = "".join(texts)
            rids = blip_rids(child)
            if rids:
                for rid in rids:
                    sequence.append(("IMAGE", rid, para_text.strip()))
            elif para_text.strip():
                sequence.append(("P", para_text))
        elif tag == qn("w:tbl"):
            for tbl in d.tables:
                if tbl._tbl is child:
                    sequence.append(("T", tbl))
                    break

    # Write sequence summary and tables as .tex snippets
    lines = [f"% Auto-extracted from {DOCX.name} — do not hand-edit without re-run", ""]
    img_idx = 0
    for kind, *rest in sequence:
        if kind == "P":
            (text,) = rest
            lines.append("% ---")
            lines.append(tex_escape(text))
            lines.append("")
        elif kind == "T":
            (tbl,) = rest
            lines.append("\\begin{table}[htbp]")
            lines.append("  \\centering")
            lines.append("  \\small")
            lines.append("  \\caption{TABLECAPTION}")
            lines.append("  \\label{tab:ICA1PLACEHOLDER}")
            lines.append(table_to_tex(tbl))
            lines.append("\\end{table}")
            lines.append("")
        elif kind == "IMAGE":
            rid, caption = rest
            img_idx += 1
            src = rid_files.get(rid)
            if not src:
                continue
            # Copy to figures as ICA1_fig_N.png (includegraphics supports png with pdflatex)
            dest = OUT_DIR / f"ICA1_embed_{img_idx}{src.suffix}"
            shutil.copy2(src, dest)
            cap = tex_escape(caption) if caption else f"Figure {img_idx}"
            lines.append("\\begin{figure}[htbp]")
            lines.append("  \\centering")
            lines.append(f"  \\includegraphics[width=0.92\\textwidth]{{figures/{dest.name}}}")
            lines.append(f"  \\caption{{{cap}}}")
            lines.append(f"  \\label{{fig:ica1_{img_idx}}}")
            lines.append("\\end{figure}")
            lines.append("")

    META_DIR.joinpath("raw_sequence.tex").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", META_DIR / "raw_sequence.tex")
    print("Images copied to report/figures as ICA1_embed_*.png")


if __name__ == "__main__":
    main()
