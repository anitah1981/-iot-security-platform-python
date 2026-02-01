# Android Emulator Setup (Option A) – Complete Steps

Follow these steps in order to get the Android emulator running on your laptop and view your built app.

---

## Step 1: Re-run the Android Studio installer (add Android Virtual Device)

1. **Close Android Studio** completely.
2. **Open the installer:**
   - **Option A:** In Windows search, type **Apps & features** → open it → find **Android Studio** → click it → click **Modify**.
   - **Option B:** Or run the same `android-studio-*.exe` installer you used originally (re-download from https://developer.android.com/studio if needed).
3. In the installer window:
   - Click **Next** until you see the list of components.
   - Ensure **Android Virtual Device** is **checked** (along with Android Studio).
   - Click **Next**, then **Install** / **Finish**.
4. **Restart your PC** if the installer suggests it (optional but can help).

---

## Step 2: Open SDK Manager and install Android Emulator

1. **Open Android Studio** (from the Start menu).
2. On the **Welcome** screen, click **More Actions** (three dots or link at the bottom).
3. Click **SDK Manager**.
4. In the SDK Manager window:
   - Click the **SDK Tools** tab (not SDK Platforms).
   - In the search/filter box, type **Emulator**.
   - Find **Android Emulator** and **tick the checkbox** next to it.
   - You can **leave "Android Emulator hypervisor driver" unchecked** (it often fails on Windows; the emulator can run without it).
   - Click **Apply** → **OK** and wait for the download/install to finish.
5. If you see any error about the hypervisor driver, click **OK** and ignore it. Close the installer window when done.

---

## Step 3: Create a virtual device (AVD)

1. On the Android Studio **Welcome** screen, click **More Actions** again.
2. Click **Virtual Device Manager** (or **Device Manager**).
3. Click **Create Device** (or the **+** button).
4. In the device list:
   - Select **Pixel 8** (or any phone, e.g. Pixel 6).
   - Click **Next**.
5. **System image:**
   - Select **API 34** (Android 14) with **x86_64** (e.g. "Google Play Intel x86_64 Atom" or "UpsideDownCake").
   - If the image shows **Download**, click it and wait for the download to finish, then select it.
   - Click **Next**.
6. **Advanced settings (important):**
   - Click **Show Advanced Settings**.
   - Find **Graphics** and set it to **Software** (so it works without the hypervisor driver).
   - Click **Finish**.
7. Your new device appears in the list. Click the **Play (▶)** button next to it to start the emulator.
8. Wait until the virtual phone screen appears (can take a minute the first time).

---

## Step 4: Install your built APK on the emulator

1. **Download your APK** from Expo:
   - In your browser, go to: **https://expo.dev/accounts/anitah1981/projects/iot-security-platform/builds**
   - Click the **latest successful Android** build (green check / "Finished").
   - Click **Download** to get the `.apk` file (e.g. to your Downloads folder).
2. **Install on the emulator:**
   - With the **emulator window open** (virtual phone visible), **drag the downloaded `.apk` file** from File Explorer onto the emulator window.
   - On the emulator, accept the install prompt (Install / Open).
3. **Open the app:** On the emulator, open the app drawer and tap **IoT Security** (or your app name).

---

## Troubleshooting

| Problem | What to do |
|--------|------------|
| "Dependant package with key emulator not found" | You're in Step 2: make sure **Android Emulator** is ticked in SDK Tools and click Apply. Then close and reopen Virtual Device Manager. |
| Hypervisor driver fails | Ignore it. Use **Graphics: Software** when creating the AVD (Step 3). |
| Emulator is very slow | Normal when using Software graphics. You can try enabling virtualization in BIOS (Intel VT-x / AMD-V) and then installing the hypervisor driver later. |
| No "Android Virtual Device" in installer | Use "Modify" on Android Studio in Apps & features, or re-download the full installer from developer.android.com/studio. |

---

## Quick checklist

- [ ] Step 1: Re-run installer, **Android Virtual Device** checked
- [ ] Step 2: SDK Manager → SDK Tools → **Android Emulator** ticked → Apply
- [ ] Step 3: Virtual Device Manager → Create Device → Pixel 8, API 34, **Graphics: Software** → Finish → ▶
- [ ] Step 4: Download APK from Expo builds → drag onto emulator → install and open

Once these are done, you’ll have the emulator running and your app installed on it.
