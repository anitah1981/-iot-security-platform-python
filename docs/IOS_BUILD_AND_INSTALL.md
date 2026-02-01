# iOS Build & Install on Your iPhone (Apple Developer)

Use this guide to build the IoT Security app for iOS and install it on your iPhone. You’ve already signed up for Apple Developer and paid; EAS will use it for signing and distribution.

---

## Prerequisites

- **Apple Developer account** (paid) – you have this.
- **EAS CLI** – already used for Android. If needed: `npm install -g eas-cli`
- **Logged into Expo** – run `eas whoami` in the `mobile` folder; if not logged in, run `eas login`.
- **iPhone** – same Apple ID as your developer account is best for internal installs.

---

## Step 1: Build the iOS app with EAS

1. Open a terminal (PowerShell or Command Prompt).
2. Go to the mobile project:
   ```powershell
   cd c:\IoT-security-app-python\mobile
   ```
3. Start the iOS build:
   ```powershell
   eas build --platform ios --profile preview
   ```
4. When EAS asks questions, use these answers:
   - **Apple ID / Apple Developer account:** Sign in with the Apple ID that has the paid Apple Developer membership.
   - **Generate/use credentials:** Choose **Let EAS manage** (recommended) so EAS creates/uses the right certificates and provisioning profiles.
   - **Register devices for internal distribution:** If it asks to register your iPhone, say **Yes** and follow the prompts (you may need to enter your device name or UDID; EAS can guide you).
5. Wait for the build to finish (often 10–20 minutes). EAS will show a build URL and, when done, a **download link** for the `.ipa` or a link to install on your device.

---

## Step 2: Install the app on your iPhone

1. **Get the install link**  
   When the build finishes, EAS will show a link like:  
   `https://expo.dev/accounts/anitah1981/projects/iot-security-platform/builds/...`  
   Open that page on your **Mac or Windows PC** in a browser.

2. **On the build page:**  
   - Click **Install** or **Download** (or the QR code / device install link).  
   - You may get an **internal distribution** link that only works on registered devices.

3. **On your iPhone:**  
   - Open the **same install link** in **Safari** (not Chrome).  
   - Tap **Install** and accept the profile/app install.  
   - If iOS says “Untrusted Developer”:  
     - Go to **Settings → General → VPN & Device Management**.  
     - Tap your developer profile (e.g. your Apple ID or team name).  
     - Tap **Trust**, then try opening the app again.

4. **Open the app**  
   Find **IoT Security** on the home screen and tap it. The app will use the `apiUrl` in `app.json` (e.g. your ngrok URL or production backend).

---

## Step 3 (optional): Use your backend URL

- **For local/testing:** The app is already set to use your ngrok URL in `app.json` (`extra.apiUrl`). Keep the backend and ngrok running when testing.
- **For production:** When your backend is deployed, change `extra.apiUrl` in `mobile/app.json` to your real API URL, then run `eas build --platform ios --profile preview` again and re-install.

---

## If EAS asks to register your device

- For **internal (preview)** builds, Apple requires devices to be registered in your Apple Developer account.
- EAS can do this for you: when it asks, choose to register the device and follow the prompts.
- You may need your iPhone’s **name** (e.g. “Anita’s iPhone”) or **UDID**.  
  - **UDID:** On iPhone go to **Settings → General → About**; or connect the phone to a Mac and use Finder (or Apple Configurator) to see the UDID.  
  - Some EAS flows let you register by connecting the iPhone or by entering UDID on the Expo website.

---

## Quick reference

| Step | Action |
|------|--------|
| 1 | `cd c:\IoT-security-app-python\mobile` |
| 2 | `eas build --platform ios --profile preview` |
| 3 | Sign in with Apple ID (paid developer), let EAS manage credentials |
| 4 | Wait for build; open build page and get install link |
| 5 | On iPhone: open link in Safari → Install → Trust in Settings if needed |
| 6 | Open **IoT Security** on the home screen |

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| “No valid code signing” | In EAS, choose **Let EAS manage** credentials and use the Apple ID that has the paid developer membership. |
| “Device not registered” | Register the device when EAS prompts, or in Apple Developer Portal → Devices, add the iPhone UDID, then rebuild. |
| “Untrusted Developer” on iPhone | Settings → General → VPN & Device Management → tap your developer profile → Trust. |
| App installs but won’t open | Ensure the app is built with the same bundle ID and that the device is registered for the provisioning profile. |

Once the build has finished and you’ve installed the app on your iPhone, you’re done with this flow. We can pause Android and come back to it anytime; for now you can focus on iOS with this guide.
