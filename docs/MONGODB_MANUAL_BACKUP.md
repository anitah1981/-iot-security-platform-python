# Manual MongoDB backup (Atlas M0 / no continuous backup)

On the free M0 tier, Atlas doesn't run continuous backups. You can back up manually with **mongodump** from your PC, then keep the dump folder somewhere safe (e.g. external drive, cloud storage).

---

## 1. Install MongoDB Database Tools (one-time)

You need the tools that include `mongodump` and `mongorestore`.

**Windows:**

1. Download: https://www.mongodb.com/try/download/database-tools  
   Pick **Windows x86_64** (or ARM if you're on ARM), **msi** package → Download.
2. Run the MSI: double-click the downloaded file → Next through the steps (you can change the install folder if you want) → Finish.  
   The tools are installed in e.g. `C:\Program Files\MongoDB\Tools\100\bin` (the number may be different).
3. Add the tools to PATH (the MSI does not do this for you):
   - Open **Control Panel** → **System** → **Advanced system settings** → **Environment Variables**.
   - Under **System variables** (or **User variables**), select **Path** → **Edit** → **New**.
   - Add: `C:\Program Files\MongoDB\Tools\100\bin` (if your install path is different, use that `...\Tools\<version>\bin` folder).
   - OK out of all dialogs. **Close and reopen PowerShell** so `mongodump` is recognized.

**macOS (Homebrew):**

```bash
brew install mongodb-database-tools
```

**Linux (Ubuntu/Debian):**

```bash
# Follow https://www.mongodb.com/docs/database-tools/installation/installation-linux/
```

---

## 2. Run a backup (dump)

From a terminal, point `mongodump` at your Atlas cluster using the same connection string as your app (from `.env`).

**PowerShell (Windows):**

```powershell
# Optional: create a dated folder for this backup
$date = Get-Date -Format "yyyyMMdd"
$outDir = "C:\backups\mongodb_$date"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Use the SAME URI as in your .env (single quotes so & and ! are safe)
$env:MONGO_URI = 'mongodb+srv://YOUR_USER:YOUR_PASSWORD@iot-monitoring.ymn32jk.mongodb.net/iot_security?retryWrites=true&w=majority'

# Run mongodump (writes to the folder)
mongodump --uri=$env:MONGO_URI --out=$outDir
```

Replace `YOUR_USER` and `YOUR_PASSWORD` with your Atlas user and password. The dump will be in `C:\backups\mongodb_YYYYMMDD` (e.g. `iot_security` subfolder with `.bson` and metadata).

**Alternative: use .env**

If you don't want to paste the URI in the terminal, you can load it from `.env` and then run mongodump:

```powershell
cd c:\IoT-security-app-python
# Load first line that starts with MONGO_URI from .env (no quotes in .env for value)
$env:MONGO_URI = (Get-Content .env | Where-Object { $_ -match '^MONGO_URI=' }) -replace '^MONGO_URI=',''
$outDir = "C:\backups\mongodb_$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
mongodump --uri=$env:MONGO_URI --out=$outDir
```

**Bash (Linux/macOS):**

```bash
export MONGO_URI='mongodb+srv://user:pass@cluster.mongodb.net/iot_security?retryWrites=true&w=majority'
OUT_DIR="$HOME/backups/mongodb_$(date +%Y%m%d)"
mkdir -p "$OUT_DIR"
mongodump --uri="$MONGO_URI" --out="$OUT_DIR"
```

---

## 3. Store the backup

- Copy the dump folder (e.g. `C:\backups\mongodb_20260227`) to a safe place: external drive, OneDrive, Google Drive, etc.
- Do this regularly (e.g. weekly) so you always have a recent copy.

---

## 4. Restore from a backup (if needed)

Use **mongorestore** with the same cluster (or a new one). Only do this when you intend to overwrite or restore data.

```powershell
# PowerShell
$env:MONGO_URI = 'mongodb+srv://...'
mongorestore --uri=$env:MONGO_URI --drop "C:\backups\mongodb_20260227"
```

`--drop` drops existing collections before restoring. Omit it if you want to merge/restore only certain collections (see `mongorestore --help`).

---

## Quick reference

| Task        | Command / action |
|------------|-------------------|
| One-time   | Install [MongoDB Database Tools](https://www.mongodb.com/try/download/database-tools). |
| Backup     | `mongodump --uri=<MONGO_URI> --out=<folder>`. |
| Restore    | `mongorestore --uri=<MONGO_URI> [--drop] <dump_folder>`. |
| Schedule   | Run the backup script weekly (Task Scheduler on Windows, cron on Mac/Linux). |
