# Twilio trial account – why SMS / WhatsApp / Voice might not arrive

On a **trial account**, Twilio only delivers to numbers you have explicitly verified (and for WhatsApp, to users who have opted in). If nothing is coming through, work through this checklist in the Twilio Console.

---

## 1. Verify the number that receives alerts (SMS & Voice)

**Console:** [Twilio Console](https://console.twilio.com) → **Phone Numbers** → **Manage** → **Verified Caller IDs**  
(or search for “Verified Caller IDs” in the console.)

- Add the **exact** number you use in the app for **Phone number** (e.g. `+447418097636`) if it is not already there.
- Twilio will send a code by SMS or voice call; enter it to verify.
- **Trial rule:** SMS and voice calls from your app can only be sent **to** numbers listed here. If your number isn’t verified, Twilio will reject the request and you won’t get the message or call.

Use the same number in:

- Twilio **Verified Caller IDs**
- Your app: **Settings → Notification preferences → Phone number**

---

## 2. WhatsApp – opt-in and number

**Console:** **Messaging** → **Try it out** → **Send a WhatsApp message**, or **Messaging** → **WhatsApp senders**.

- With a trial/sandbox, the recipient usually must **send a join phrase** to your Twilio WhatsApp number first (e.g. “join &lt;your-code&gt;”). Until they do, Twilio may block or drop messages to them.
- The number in the app (**WhatsApp number** in Notification preferences) should be the number of the WhatsApp account that completed opt-in (same as or different from the SMS/voice number).

If you’re on the **WhatsApp sandbox**:

- In Twilio, open **Messaging** → **Try it out** → **Send a WhatsApp message** and note the **join phrase** and the **sandbox sender number** (e.g. `+14155238886`).
- On the phone that should receive alerts, open WhatsApp and send that join phrase (e.g. `join abc-xyz`) to the sandbox number. You should get a reply from Twilio confirming you joined.
- **Important:** In your app’s `.env` you must set **`TWILIO_WHATSAPP_NUMBER`** to that **sandbox number** (e.g. `+14155238886`). Do **not** use your regular `TWILIO_PHONE_NUMBER` for WhatsApp when using the sandbox—the sandbox only accepts messages sent *from* the sandbox number. Restart the app after changing `.env`.
- Then test again from your app (e.g. Settings → Test WhatsApp).

---

## 3. Check Twilio phone number and credentials

**Console:** **Phone Numbers** → **Manage** → **Active Numbers**

- You should have at least one **Twilio number** (the “from” number for SMS and voice).
- In your app’s `.env` you must set:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_PHONE_NUMBER` = that Twilio number (e.g. `+1234567890`)
  - For **WhatsApp Sandbox**: `TWILIO_WHATSAPP_NUMBER` must be the **sandbox sender number** (e.g. `+14155238886` from Twilio Console → Messaging → Try it out → Send a WhatsApp message). Using your regular `TWILIO_PHONE_NUMBER` here will cause WhatsApp messages to fail in the sandbox.

If any of these are wrong or missing, the app may show “Twilio configured” but requests will still fail.

---

## 4. Check the app and Twilio logs

**In the app (terminal):**

- On startup you should see something like:  
  `[NOTIFICATIONS] Twilio configured: True | SMS enabled: True | Voice ready: True | WhatsApp ready: True`
- When a device goes offline you should see lines like:  
  `[NOTIFY] Attempting SMS to +44***36` and then either `Sent` or an error (e.g. Twilio error code).

**In Twilio Console:** **Monitor** → **Logs** → **Messaging** or **Voice**

- Look for failed attempts to your number. Common trial errors:
  - **21608** – “Cannot send to unverified number” (or similar) → add and verify that number in Verified Caller IDs.
  - **21614** – “Number is not a valid mobile number” (or similar) → check E.164 format (e.g. `+447418097636`).
  - **63016** – WhatsApp: user has not opted in → complete WhatsApp sandbox opt-in (step 2).

---

## 5. UK numbers (SMS)

- Sending **to** UK numbers may have extra rules (e.g. alphanumeric sender, A2P). Trial can still work to **verified** UK numbers.
- If you see a Twilio error about “UK” or “geo permissions”, check **Messaging** → **Regulatory Compliance** (or similar) in the console and Twilio’s UK SMS docs.

---

## Quick checklist

| Check | Where | Action |
|-------|--------|--------|
| Receiving number verified | Twilio → Phone Numbers → Verified Caller IDs | Add and verify the number you use in the app (SMS + Voice). |
| WhatsApp opt-in | Twilio → WhatsApp sandbox / senders | Have the recipient send the join phrase to your Twilio WhatsApp number. |
| Twilio number set in app | Your `.env` | Set `TWILIO_PHONE_NUMBER` (and `TWILIO_WHATSAPP_NUMBER` if used). |
| Correct number in app | App → Settings → Notification preferences | Phone number and WhatsApp number must match what you verified / opted in (e.g. `+447418097636`). |
| Errors in Twilio | Twilio → Monitor → Logs | Use the error code (e.g. 21608, 63016) to fix verification or WhatsApp opt-in. |

After changing anything in Twilio (e.g. verifying a number or completing WhatsApp opt-in), trigger another offline alert and check both the app terminal and Twilio logs again.
