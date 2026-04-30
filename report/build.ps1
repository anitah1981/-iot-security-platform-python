# Build report PDF: pdflatex -> biber -> pdflatex x2
#
# If discovery fails, set the folder that contains pdflatex.exe, then run again:
#   $env:IOT_REPORT_TEX_BIN = 'C:\path\to\miktex\bin\x64'
#   .\build.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

function Find-PdfLatexUnder {
    param([string]$Root, [int]$MaxDepth = 14)
    if (-not (Test-Path -LiteralPath $Root)) { return $null }
    $hit = Get-ChildItem -LiteralPath $Root -Filter pdflatex.exe -File -Recurse -Depth $MaxDepth -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($hit) { return $hit.DirectoryName }
    return $null
}

function Find-TeXBin {
    if ($env:IOT_REPORT_TEX_BIN) {
        $p = $env:IOT_REPORT_TEX_BIN.TrimEnd('\')
        if (Test-Path (Join-Path $p "pdflatex.exe")) { return $p }
        Write-Host "IOT_REPORT_TEX_BIN is set but pdflatex.exe was not found in: $p" -ForegroundColor Red
        exit 1
    }

    $cmd = Get-Command pdflatex.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return [System.IO.Path]::GetDirectoryName($cmd.Source)
    }

    $dirs = @(
        "$env:ProgramFiles\MiKTeX\miktex\bin\x64"
        "${env:ProgramFiles(x86)}\MiKTeX\miktex\bin\x64"
        "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64"
    )
    foreach ($d in $dirs) {
        if (Test-Path (Join-Path $d "pdflatex.exe")) { return $d }
    }

    foreach ($root in @(
            "$env:ProgramFiles\MiKTeX"
            "$env:LOCALAPPDATA\Programs\MiKTeX"
            "$env:USERPROFILE\scoop\apps\miktex"
        )) {
        $found = Find-PdfLatexUnder -Root $root
        if ($found) { return $found }
    }

    $chocoLib = "$env:ProgramData\chocolatey\lib\miktex"
    if (Test-Path -LiteralPath $chocoLib) {
        $found = Find-PdfLatexUnder -Root $chocoLib -MaxDepth 20
        if ($found) { return $found }
    }

    $texRoot = "C:\texlive"
    if (Test-Path $texRoot) {
        $years = Get-ChildItem -Path $texRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^\d{4}$' } |
            Sort-Object { [int]$_.Name } -Descending
        foreach ($y in $years) {
            $bd = Join-Path $y.FullName "bin\windows"
            if (Test-Path (Join-Path $bd "pdflatex.exe")) { return $bd }
        }
    }

    return $null
}

$texBin = Find-TeXBin
if (-not $texBin) {
    $exampleBin = Join-Path $env:LOCALAPPDATA "Programs\MiKTeX\miktex\bin\x64"
    $searchRoots = @($env:ProgramFiles, (Join-Path $env:LOCALAPPDATA "Programs"))
    Write-Host ""
    Write-Host "pdflatex.exe was not found. Install MiKTeX, or point the script at your TeX bin folder." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "--- Install ---" -ForegroundColor Yellow
    Write-Host "  winget install MiKTeX.MiKTeX"
    Write-Host "  https://miktex.org/download"
    Write-Host ""
    Write-Host "After install: open MiKTeX Console once, let updates finish, then close this window and open a NEW PowerShell." -ForegroundColor Yellow
    Write-Host "  cd $here"
    Write-Host "  .\build.ps1"
    Write-Host ""
    Write-Host "--- Already installed? Set bin path for this session ---" -ForegroundColor Yellow
    Write-Host "  `$env:IOT_REPORT_TEX_BIN = '$exampleBin'"
    Write-Host "  .\build.ps1"
    Write-Host ""
    Write-Host "Search for pdflatex.exe (can take a minute):" -ForegroundColor Yellow
    $sr0 = $searchRoots[0]
    $sr1 = $searchRoots[1]
    Write-Host "  Get-ChildItem -Path '$sr0', '$sr1' -Filter pdflatex.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 FullName"
    Write-Host ""
    exit 1
}

$env:PATH = "$texBin;$env:PATH"
Write-Host "Using TeX: $texBin" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $texBin "biber.exe"))) {
    Write-Host @"

biber.exe not found in $texBin
Open MiKTeX Console -> Packages -> search 'biber' -> install. Then run Tasks -> Update package database.

"@ -ForegroundColor Yellow
    exit 1
}

function Invoke-TeX($pass) {
    & pdflatex.exe -interaction=nonstopmode -halt-on-error main.tex
    if ($LASTEXITCODE -ne 0) { throw "pdflatex failed ($pass)." }
}

try {
    Invoke-TeX "pass 1"
    & biber.exe main
    if ($LASTEXITCODE -ne 0) { throw "biber failed." }
    Invoke-TeX "pass 2"
    Invoke-TeX "pass 3"
    Write-Host "OK: main.pdf in $here" -ForegroundColor Green
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
