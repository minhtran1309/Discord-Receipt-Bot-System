# Data Directory Configuration Fix

## Problem Summary

The bot's data storage directory configuration needs to be aligned between:
1. The application code (uses relative path `data/`)
2. The systemd service security settings
3. The actual runtime directory on GCP

## Current Behavior

- **Bot application**: Stores data in `/opt/discord-bot/app/data/` (relative to working directory)
  - Receipts: `/opt/discord-bot/app/data/receipts/`
  - Items: `/opt/discord-bot/app/data/items/`
  - Budgets: `/opt/discord-bot/app/data/budgets/`
  - Corrections: `/opt/discord-bot/app/data/corrections.json`

- **Systemd services**: Previously configured with wrong path `/opt/discord-bot/data`

## Solution Applied

### 1. Updated Systemd Service Files

The `scripts/setup_systemd_services.sh` has been updated to use the correct data directory path:

**Production service** (`discord-bot.service`):
```ini
ReadWritePaths=/opt/discord-bot/app/data /var/log/discord-bot
```

**Development service** (`discord-bot-dev.service`):
```ini
ReadWritePaths=/opt/discord-bot/app/data
```

### 2. Re-run Setup Script on GCP Server

To apply the fix, SSH into the GCP server and re-run the setup script:

```bash
# SSH into GCP server
gcloud compute ssh botuser@discord-bot-server --zone=australia-southeast1-a

# Navigate to app directory
cd /opt/discord-bot/app

# Pull latest changes
git pull origin guess_feature

# Re-run systemd setup (this will update the service files)
bash scripts/setup_systemd_services.sh

# Restart services to apply changes
sudo systemctl daemon-reload
sudo systemctl restart discord-bot-dev.service

# Verify the service is running
sudo systemctl status discord-bot-dev.service

# Check if data directory permissions are correct
ls -la /opt/discord-bot/app/data/
```

### 3. Verify Data Directory Structure

The data directory should have these subdirectories:

```bash
/opt/discord-bot/app/data/
├── receipts/         # Processed receipt JSON files
├── items/            # Extracted items in TSV format
├── budgets/          # Budget entries organized by month
│   ├── 2026-01/
│   ├── 2026-02/
│   └── ...
└── corrections.json  # Item name correction mappings
```

If any directories are missing, create them:

```bash
mkdir -p /opt/discord-bot/app/data/{receipts,items,budgets}
chown -R botuser:botuser /opt/discord-bot/app/data
chmod -R 755 /opt/discord-bot/app/data
```

## Environment Configuration

The `.env.development` and `.env.production` files use relative paths by default:

```bash
# This is correct - relative to WorkingDirectory (/opt/discord-bot/app)
DATA_DIR=data
```

**Alternative: Use absolute paths** (if you prefer explicit configuration):

```bash
# Absolute path (optional)
DATA_DIR=/opt/discord-bot/app/data
```

Both approaches work, but relative paths are simpler since the systemd `WorkingDirectory` is already set to `/opt/discord-bot/app`.

## Testing the Fix

After applying the fix, test the `/clerk sync` command:

1. **Process a receipt** (if you don't have any):
   ```
   /receipt process [attach an image]
   ```

2. **Verify the receipt**:
   ```
   /receipt verify <filename>
   ```

3. **Check receipt files exist**:
   ```bash
   # On GCP server
   ls -la /opt/discord-bot/app/data/receipts/
   ls -la /opt/discord-bot/app/data/items/
   ```

4. **Sync to Google Sheets**:
   ```
   /clerk sync
   ```

5. **Verify no permission errors** in logs:
   ```bash
   # On GCP server
   sudo journalctl -u discord-bot-dev.service -n 50 --no-pager
   ```

## Common Issues

### Issue 1: Permission Denied Errors

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: '/opt/discord-bot/app/data/receipts/...'
```

**Fix**:
```bash
# On GCP server
sudo chown -R botuser:botuser /opt/discord-bot/app/data
sudo chmod -R 755 /opt/discord-bot/app/data
```

### Issue 2: Receipts Not Found by /clerk sync

**Symptom**: `/clerk sync` says "No verified receipts to sync" but receipts exist

**Diagnosis**:
```bash
# Check if receipts are in the correct location
ls -la /opt/discord-bot/app/data/receipts/
```

**Fix**: Receipts should be in `/opt/discord-bot/app/data/receipts/`, not `/opt/discord-bot/data/receipts/`

### Issue 3: SELinux or AppArmor Blocking Access

**Symptom**: Permission errors even with correct ownership

**Fix**:
```bash
# Check for SELinux denials
sudo ausearch -m avc -ts recent

# Check for AppArmor denials (if applicable)
sudo journalctl | grep audit | grep DENIED

# If necessary, adjust SELinux contexts
sudo chcon -R -t usr_t /opt/discord-bot/app/data
```

## Rollback Plan

If the changes cause issues, you can rollback:

```bash
# On GCP server
cd /opt/discord-bot/app
git fetch origin
git reset --hard origin/main  # or previous commit hash

# Re-run old setup script
bash scripts/setup_systemd_services.sh

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart discord-bot-dev.service
```

## Summary

- ✅ Systemd service files updated with correct data path
- ✅ Both production and development services configured
- ✅ Security hardening (ReadWritePaths) properly set
- ✅ Instructions provided for applying fix on GCP server
- ✅ Testing procedure documented
