# ✅ Fixed - Correct Command

**The error was:** `--lan` and `--host` can't be used together.

**Fixed command:**
```bash
npm run start:iphone
```

This now runs: `expo start --host 192.168.0.235`

---

## 🚀 **Try Again**

1. **Stop Expo** (if running): `Ctrl+C`

2. **Run:**
   ```bash
   npm run start:iphone
   ```

3. **Check terminal** - should show: `exp://192.168.0.235:8081`

4. **Connect iPhone:**
   - Camera app → Scan QR code
   - Or Safari → `exp://192.168.0.235:8081`

---

**This should work now!** ✅
