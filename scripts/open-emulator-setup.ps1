# Open helpers for Android Emulator setup (Option A)
# Run: .\scripts\open-emulator-setup.ps1

Write-Host "`n=== Android Emulator Setup (Option A) ===" -ForegroundColor Cyan
Write-Host "`n1. Opening 'Apps & features' so you can MODIFY Android Studio..." -ForegroundColor Yellow
Write-Host "   -> Find 'Android Studio', click it, click MODIFY" -ForegroundColor Gray
Write-Host "   -> Ensure 'Android Virtual Device' is CHECKED, then complete install.`n" -ForegroundColor Gray
Start-Process "ms-settings:appsfeatures"

Write-Host "2. Opening Expo builds page (download APK after emulator is running)..." -ForegroundColor Yellow
Start-Process "https://expo.dev/accounts/anitah1981/projects/iot-security-platform/builds"

Write-Host "`n3. Full step-by-step guide:" -ForegroundColor Yellow
Write-Host "   $((Get-Location).Path)\docs\ANDROID_EMULATOR_SETUP.md`n" -ForegroundColor Gray
Write-Host "Done. Follow ANDROID_EMULATOR_SETUP.md for Steps 2-4 after modifying Android Studio." -ForegroundColor Green
Write-Host ""
