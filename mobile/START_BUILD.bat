@echo off
echo ========================================
echo Building Mobile Apps with EAS
echo ========================================
echo.
echo This will build iOS and Android apps.
echo.
echo Step 1: Installing EAS CLI...
call npm install -g eas-cli
echo.
echo Step 2: Please login to Expo
echo (You'll be prompted to login)
echo.
pause
call eas login
echo.
echo Step 3: Configuring project...
call eas build:configure
echo.
echo ========================================
echo Configuration complete!
echo ========================================
echo.
echo Next steps:
echo 1. Update apiUrl in app.json with your backend URL
echo 2. Run: eas build --platform ios --profile preview
echo 3. Run: eas build --platform android --profile preview
echo.
pause
