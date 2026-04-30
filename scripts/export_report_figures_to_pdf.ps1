# Export SVG report figures to PDF for pdflatex (expects Inkscape on PATH).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root "docs\report_figures"
$dst = Join-Path $root "report\figures"
New-Item -ItemType Directory -Force -Path $dst | Out-Null

$inkscape = Get-Command inkscape -ErrorAction SilentlyContinue
if (-not $inkscape) {
  Write-Host "Inkscape not found on PATH. Install Inkscape or export SVGs manually to report/figures/*.pdf"
  exit 1
}

Get-ChildItem -Path $src -Filter "*.svg" | ForEach-Object {
  $out = Join-Path $dst ($_.BaseName + ".pdf")
  Write-Host "Exporting $($_.Name) -> $out"
  & inkscape $_.FullName --export-type=pdf --export-filename="$out"
}

Write-Host "Done."
