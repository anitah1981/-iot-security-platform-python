# Build the LaTeX report (runs report/build.ps1). Safe to run from any directory.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $root "report\build.ps1")
