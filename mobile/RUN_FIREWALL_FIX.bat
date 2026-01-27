@echo off
echo ========================================
echo Expo Firewall Fix - Run as Administrator
echo ========================================
echo.
echo This will configure Windows Firewall for Expo.
echo.
echo IMPORTANT: Right-click this file and select
echo "Run as Administrator" for it to work!
echo.
pause

powershell.exe -ExecutionPolicy Bypass -File "%~dp0fix-firewall.ps1"

pause
