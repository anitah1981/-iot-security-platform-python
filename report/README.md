# LaTeX dissertation/report (Harvard-style citations)

This folder contains a `report`/`main.tex` draft aligned to your chapter numbering (Chapter 5 = Introduction).

## Citations (Harvard-style)

The template uses `biblatex` **author--year** (`style=authoryear`) with **Biber**, which produces Harvard-like parenthetical citations such as `(Weber, 2010)` via `\parencite{...}`.

Build sequence:

1. `pdflatex main`
2. `biber main`
3. `pdflatex main`
4. `pdflatex main`

Run these from inside `report/`.

## Figures (SVG → PDF)

`pdflatex` does not reliably include `.svg` without extra tooling. The template expects **PDFs** in `report/figures/` with the same basename as the SVGs in `docs/report_figures/`.

If Inkscape is installed and on `PATH`:

```powershell
powershell -ExecutionPolicy Bypass -File ..\scripts\export_report_figures_to_pdf.ps1
```

Then rebuild LaTeX.

## Personalise

Edit the `\author{...}` block in `main.tex` and replace bracketed placeholders if any remain in the title page.

## Source files

Chapter sources live under `chapters/` (e.g.\ `abstract.tex`, `ch07-literature.tex`). `main.tex` uses `\input{chapters/abstract}` and `\include{chapters/ch07-literature}` among others. If a file is locked by the editor on Windows, close the tab before regenerating or overwriting it.

When pasting from Word into LaTeX, watch for characters that need escaping: `%`, `&`, `#`, `~`, and unmatched braces.
