# Restore and retention (Python backup)

When you use scripts/backup_manual.py, backups are JSON files in C:\backups\mongodb_YYYYMMDD_HHMM (or BACKUP_BASE_DIR).

## Restore (if you lose the DB)

1. Copy the latest backup folder to a safe place.
2. Create a new MongoDB cluster (or use a test DB) and set its MONGO_URI.
3. Load data: read each .json file from the backup folder and insert into the target DB (same collection names). Use pymongo or MongoDB Compass to import each JSON into the matching collection.
4. Point the app at the restored DB and confirm login, devices, alerts, settings work.

## Retention (recommended)

- Keep: Last 4 weekly backups (about 1 month).
- Location: e.g. C:\backups plus a monthly copy to OneDrive or external drive.
- Prune: Once a month, delete folders in C:\backups older than 4 weeks.

Write your chosen policy in one sentence in the runbook or here.
