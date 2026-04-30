"""
Generate report/chapters/*.tex from report/ICA_2.docx preserving body order.
Skips Word TOC blocks, keeps figure/table placement, writes numbered references.
Run from repo root: python scripts/ica2_emit_latex.py
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "report" / "ICA_2.docx"
FIG = ROOT / "report" / "figures"
META = ROOT / "report" / "_ica2_extract"


def tex_escape(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
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
    s = s.replace("\u00a7", "\\S{}")
    s = s.replace("\u2026", "\\ldots{}")
    s = s.replace("\u00b7", "$\\cdot$")
    s = s.replace("\u00a0", "~")
    return s.strip()


def clean_figure_caption(caption: str) -> str:
    """Remove redundant leading 'Figure ...' prefixes from caption text."""
    c = caption.strip()
    # Handles patterns like:
    # "Figure 11.1: Figure Qualitative Performance"
    # "Figure: Figure Qualitative Performance"
    c = re.sub(r"^\s*Figure\s*\d+(?:\.\d+)*\s*[:.\-]?\s*", "", c, flags=re.I)
    c = re.sub(r"^\s*Figure\s*[:.\-]?\s*", "", c, flags=re.I)
    c = re.sub(r"^\s*Figure\s+", "", c, flags=re.I)
    return c.strip()


def extract_rid_files() -> dict[str, Path]:
    FIG.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(DOCX)
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    rid_to: dict[str, str] = {}
    for m in re.finditer(
        r'<Relationship[^>]+Id="([^"]+)"[^>]+Target="([^"]+)"', rels
    ):
        rid, tgt = m.group(1), m.group(2)
        if "media/" in tgt and tgt.endswith((".png", ".jpeg", ".jpg", ".gif")):
            internal = "word/" + tgt if not tgt.startswith("word/") else tgt
            rid_to[rid] = internal.replace("\\", "/")
    out: dict[str, Path] = {}
    for rid, internal in rid_to.items():
        if internal not in z.namelist():
            continue
        ext = Path(internal).suffix.lower()
        dest = META / f"embed_{rid}{ext}"
        dest.write_bytes(z.read(internal))
        out[rid] = dest
    return out


_A_BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"


def blip_rids(p: Paragraph) -> list[str]:
    rids: list[str] = []
    for b in p._element.findall(f".//{_A_BLIP}"):
        rid = b.get(qn("r:embed")) or b.get(qn("r:link"))
        if rid:
            rids.append(rid)
    return rids


def walk(el, doc):
    tag = el.tag
    if tag == qn("w:p"):
        yield "p", Paragraph(el, doc)
    elif tag == qn("w:tbl"):
        yield "t", Table(el, doc)
    elif tag == qn("w:sdt"):
        sc = el.find(qn("w:sdtContent"))
        if sc is not None:
            for c in sc:
                yield from walk(c, doc)
    else:
        for c in el:
            yield from walk(c, doc)


def skip_toc(st: str | None, txt: str) -> bool:
    st = (st or "").lower()
    if st.startswith("toc"):
        return True
    if "table of figures" in st:
        return True
    t = txt.strip()
    if t in ("Contents", "Table of Figures", "Table of Tables"):
        return True
    return False


def table_tex(tbl: Table) -> str:
    rows = []
    for row in tbl.rows:
        rows.append([tex_escape(c.text.strip().replace("\n", " ")) for c in row.cells])
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
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines)


def build_blocks(doc: Document) -> list[tuple]:
    blocks: list[tuple] = []
    for c in doc.element.body:
        for typ, b in walk(c, doc):
            if typ == "p" and skip_toc(b.style.name, b.text):
                continue
            blocks.append((typ, b))
    return blocks


def emit_latex(doc: Document, rid_files: dict[str, Path]) -> str:
    blocks = build_blocks(doc)
    lines: list[str] = []
    fig_n = tab_n = 0
    i = 0

    def copy_embed(rid: str) -> str:
        nonlocal fig_n
        src = rid_files.get(rid)
        if not src:
            return ""
        fig_n += 1
        dest = FIG / f"ICA2_embed_{fig_n}{src.suffix}"
        shutil.copy2(src, dest)
        return dest.name

    while i < len(blocks):
        typ, b = blocks[i]

        if typ == "p":
            st = b.style.name or ""
            txt = b.text.strip()
            rids = blip_rids(b)

            if rids:
                cap = ""
                if i + 1 < len(blocks) and blocks[i + 1][0] == "p":
                    nb = blocks[i + 1][1]
                    nst = (nb.style.name or "").lower()
                    if "caption" in nst or nb.text.strip().lower().startswith("figure"):
                        cap = clean_figure_caption(tex_escape(nb.text.strip()))
                        i += 2
                    else:
                        cap = clean_figure_caption(tex_escape(txt)) if txt else ""
                        i += 1
                else:
                    cap = clean_figure_caption(tex_escape(txt)) if txt else ""
                    i += 1
                for rid in rids:
                    fn = copy_embed(rid)
                    if not fn:
                        continue
                    lines += [
                        "\\begin{figure}[htbp]",
                        "  \\centering",
                        f"  \\includegraphics[width=0.92\\textwidth]{{figures/{fn}}}",
                        f"  \\caption{{{cap}}}",
                        f"  \\label{{fig:ica2_{fig_n}}}",
                        "\\end{figure}",
                        "",
                    ]
                continue

            if st.startswith("Heading 1"):
                lines.append(f"\\chapter{{{tex_escape(txt)}}}")
                lines.append("")
                i += 1
                continue
            if st.startswith("Heading 2"):
                lines.append(f"\\section{{{tex_escape(txt)}}}")
                lines.append("")
                i += 1
                continue

            if not txt:
                i += 1
                continue

            if (st.lower().startswith("caption") or st == "Caption") and txt.lower().startswith("figure"):
                i += 1
                continue

            if (st.lower().startswith("caption") or st == "Caption") and txt.lower().startswith("table"):
                cap = tex_escape(txt)
                if i + 1 < len(blocks):
                    ntyp, nb = blocks[i + 1]
                    if ntyp == "p" and blip_rids(nb):
                        for rid in blip_rids(nb):
                            fn = copy_embed(rid)
                            if not fn:
                                continue
                            tab_n += 1
                            lines += [
                                "\\begin{table}[htbp]",
                                "  \\centering",
                                f"  \\includegraphics[width=0.92\\textwidth]{{figures/{fn}}}",
                                f"  \\caption{{{cap}}}",
                                f"  \\label{{tab:ica2_{tab_n}}}",
                                "\\end{table}",
                                "",
                            ]
                        i += 2
                        continue
                    if ntyp == "t":
                        tab_n += 1
                        lines += [
                            "\\begin{table}[htbp]",
                            "  \\centering",
                            "  \\small",
                            f"  \\caption{{{cap}}}",
                            f"  \\label{{tab:ica2_{tab_n}}}",
                            table_tex(nb),
                            "\\end{table}",
                            "",
                        ]
                        i += 2
                        continue
                i += 1
                continue

            lines.append(tex_escape(txt))
            lines.append("")
            i += 1
            continue

        if typ == "t":
            tab_n += 1
            lines += [
                "\\begin{table}[htbp]",
                "  \\centering",
                "  \\small",
                "  \\caption{}",
                f"  \\label{{tab:ica2_orphan_{tab_n}}}",
                table_tex(b),
                "\\end{table}",
                "",
            ]
            i += 1
            continue

        i += 1

    return "\n".join(lines)


def write_references_chapter(body: str, chapters_dir: Path) -> None:
    entries = [ln.strip() for ln in body.split("\n\n") if ln.strip()]
    # fallback if paragraph splitting is sparse
    if len(entries) < 4:
        entries = [ln.strip() for ln in body.splitlines() if ln.strip()]
    out = [
        "% Generated from ICA_2.docx — re-run: python scripts/ica2_emit_latex.py",
        "\\chapter*{References}",
        "\\addcontentsline{toc}{chapter}{References}",
        "",
        "\\begin{enumerate}",
    ]
    for e in entries:
        out.append(f"  \\item {e}")
    out += ["\\end{enumerate}", ""]
    chapters_dir.joinpath("ch15-references.tex").write_text(
        "\n".join(out), encoding="utf-8"
    )


def split_write(tex: str) -> None:
    parts = re.split(r"(?=\\chapter\{)", tex)
    chap = ROOT / "report" / "chapters"
    for block in parts:
        block = block.strip()
        if not block or not block.startswith("\\chapter"):
            continue
        m = re.match(r"\\chapter\{([^}]+)\}\s*(.*)", block, re.S)
        if not m:
            continue
        title, body = m.group(1), m.group(2).strip()
        key = title.lower()
        fname = None
        lbl = None
        if "abstract" in key:
            chap.joinpath("abstract.tex").write_text(body.strip() + "\n", encoding="utf-8")
            continue
        if "introduction" in key:
            fname, lbl = "ch05-introduction.tex", "ch:intro"
        elif "background" in key:
            fname, lbl = "ch06-background.tex", "ch:bg"
        elif "literature" in key:
            fname, lbl = "ch07-literature.tex", "ch:lit"
        elif "requirements" in key:
            fname, lbl = "ch08-requirements.tex", "ch:req"
        elif "system design" in key:
            fname, lbl = "ch09-design.tex", "ch:design"
        elif "implementation" in key:
            fname, lbl = "ch10-implementation.tex", "ch:impl"
        elif "testing" in key:
            fname, lbl = "ch11-testing.tex", "ch:test"
        elif "critical reflection" in key:
            fname, lbl = "ch12-reflection.tex", "ch:reflect"
        elif "future work" in key:
            fname, lbl = "ch13-future.tex", "ch:future"
        elif "conclusion" in key:
            fname, lbl = "ch14-conclusion.tex", "ch:conc"
        elif "references" in key:
            write_references_chapter(body, chap)
            continue
        if fname:
            content = (
                f"% Generated from ICA_2.docx — re-run: python scripts/ica2_emit_latex.py\n"
                f"\\chapter{{{title}}}\n\\label{{{lbl}}}\n\n{body}\n"
            )
            chap.joinpath(fname).write_text(content, encoding="utf-8")


def main() -> None:
    rid_files = extract_rid_files()
    doc = Document(DOCX)
    tex = emit_latex(doc, rid_files)
    META.joinpath("ica2_generated.tex").write_text(tex, encoding="utf-8")
    split_write(tex)
    print("OK:", META / "ica2_generated.tex")


if __name__ == "__main__":
    main()
