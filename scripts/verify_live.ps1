# Post-deploy smoke tests against your live URL (custom domain recommended).
# Usage (from repo root):
#   $env:LIVE_URL = "https://your-domain.com"
#   .\scripts\verify_live.ps1
# Optional:
#   $env:TEST_EMAIL = "..."
#   $env:TEST_PASSWORD = "..."
#
# Requires Python 3 on PATH. Uses scripts/verify_live.py (stdlib-only).

param(
    [string] $LiveUrl = $env:LIVE_URL
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not $LiveUrl) {
    Write-Error "Set LIVE_URL or pass -LiveUrl 'https://your-domain.com'"
    exit 2
}

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "python not found on PATH"
    exit 2
}

& python "$root\scripts\verify_live.py" $LiveUrl
exit $LASTEXITCODE
