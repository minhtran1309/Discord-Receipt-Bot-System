# Deployment Issues Fixed - Summary

## Date: 2026-01-16

This document summarizes the two major deployment issues that were identified and fixed.

---

## Issue 1: Pull Request Deployment Failure

### Problem
When creating pull requests to `main` branch, GitHub Actions failed with error:
```
=== Starting deployment to development ===
fatal: couldn't find remote ref merge
Error: Process completed with exit code 128.
```

### Root Cause
The deployment workflow attempted to deploy on pull request events. The deployment script extracted the branch name from `GITHUB_REF`:
- For push events: `GITHUB_REF = refs/heads/guess_feature` → extracts `guess_feature` ✅
- For pull requests: `GITHUB_REF = refs/pull/123/merge` → extracts `merge` ❌

The `merge` ref doesn't exist as a remote branch, causing `git fetch origin merge` to fail.

### Solution
Added conditional deployment in `.github/workflows/deploy-development.yml`:

```yaml
deploy:
  name: Deploy to Development Environment
  needs: test
  runs-on: ubuntu-latest
  # Only deploy on push events, not pull requests
  if: github.event_name == 'push'
```

**Result**:
- ✅ Push to `guess_feature` or `clerk_feature_dev` → Tests + Deployment
- ✅ Pull request to `main` → Tests only (no deployment)

---

## Issue 2: Data Directory Mismatch (/clerk sync failures)

### Problem
After deploying to GCP and running `/clerk sync`, the command failed to find receipts even though they were successfully processed with `/receipt process`.

### Root Cause
**Mismatch between application runtime and systemd configuration:**

1. **Application code** (`bot/config.py`):
   - Uses relative path: `data_dir: str = "data"`
   - With `WorkingDirectory=/opt/discord-bot/app`, this becomes:
   - Actual storage: `/opt/discord-bot/app/data/`

2. **Systemd service files** (before fix):
   - `ReadWritePaths=/opt/discord-bot/data` ❌ Wrong path
   - Bot couldn't write to the directory due to security restrictions

3. **Documentation** (before fix):
   - Showed absolute paths in examples: `DATA_DIR=/opt/discord-bot/data` ❌ Misleading

### Solution

#### 1. Fixed systemd service configurations (`scripts/setup_systemd_services.sh`):

**Production service** (`discord-bot.service`):
```ini
ReadWritePaths=/opt/discord-bot/app/data /var/log/discord-bot
```

**Development service** (`discord-bot-dev.service`):
```ini
ReadWritePaths=/opt/discord-bot/app/data
```

#### 2. Fixed documentation (`docs/DEPLOYMENT.md`):

Changed from:
```bash
DATA_DIR=/opt/discord-bot/data  # ❌ Wrong
```

To:
```bash
DATA_DIR=data  # ✅ Correct (relative to WorkingDirectory)
```

#### 3. Created comprehensive fix guide (`docs/DATA_DIRECTORY_FIX.md`)

---

## Files Changed

### Commit 1: Core fixes (cd244bc)
- `.github/workflows/deploy-development.yml` - Skip deployment on pull_request events
- `scripts/setup_systemd_services.sh` - Correct data directory paths
- `docs/DEPLOYMENT.md` - Fix DATA_DIR examples
- `docs/DATA_DIRECTORY_FIX.md` - New comprehensive fix guide

### Commit 2: Documentation updates (acdb4da)
- `docs/DEPLOYMENT.md` - Added troubleshooting sections
- `README.md` - Added troubleshooting sections

---

## Action Required on GCP Server

To apply the data directory fix on the GCP server:

```bash
# 1. SSH into GCP server
gcloud compute ssh botuser@discord-bot-server --zone=australia-southeast1-a

# 2. Navigate to app directory
cd /opt/discord-bot/app

# 3. Pull latest changes (includes fixes)
git pull origin guess_feature

# 4. Re-run systemd setup (updates service files)
bash scripts/setup_systemd_services.sh

# 5. Reload systemd and restart service
sudo systemctl daemon-reload
sudo systemctl restart discord-bot-dev.service

# 6. Verify service is running
sudo systemctl status discord-bot-dev.service

# 7. Check data directory exists and has correct permissions
ls -la /opt/discord-bot/app/data/
sudo chown -R botuser:botuser /opt/discord-bot/app/data
sudo chmod -R 755 /opt/discord-bot/app/data

# 8. Verify .env file uses correct path
grep DATA_DIR /opt/discord-bot/app/.env.development
# Should show: DATA_DIR=data
```

---

## Testing the Fixes

### Test 1: Pull Request Workflow
1. Create a pull request from `guess_feature` to `main`
2. ✅ Expected: Tests run, but deployment is skipped
3. ✅ Expected: No "fatal: couldn't find remote ref merge" error

### Test 2: Data Directory Access
1. Process a receipt: `/receipt process [image]`
2. Verify it: `/receipt verify <filename>`
3. Sync to sheets: `/clerk sync`
4. ✅ Expected: Receipts sync successfully without errors

### Test 3: Check Service Logs
```bash
# On GCP server
sudo journalctl -u discord-bot-dev.service -n 50 --no-pager
```
✅ Expected: No permission denied errors for `/opt/discord-bot/app/data`

---

## Status

- ✅ **Issue 1 (PR deployment)**: Fixed in workflow, no server action needed
- ⚠️ **Issue 2 (Data directory)**: Fixed in code, **requires server action** (run setup script)

---

## Documentation References

- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Main deployment guide (updated)
- [docs/DATA_DIRECTORY_FIX.md](docs/DATA_DIRECTORY_FIX.md) - Detailed data directory troubleshooting
- [docs/GITHUB_ACTIONS_EXPLAINED.md](docs/GITHUB_ACTIONS_EXPLAINED.md) - Workflow explanation
- [README.md](README.md) - Quick troubleshooting guide (updated)

---

## Key Learnings

1. **GitHub Actions `GITHUB_REF` behavior**:
   - Push: `refs/heads/<branch>`
   - Pull request: `refs/pull/<number>/merge`
   - Use `if: github.event_name == 'push'` to conditionally deploy

2. **Systemd ReadWritePaths**:
   - Must match actual runtime paths
   - Critical for security-hardened services with `ProtectSystem=strict`

3. **Relative vs Absolute paths**:
   - Prefer relative paths in application config for portability
   - Document the `WorkingDirectory` context clearly
   - Use absolute paths only when necessary (e.g., credentials)

4. **Environment configuration**:
   - Avoid inline comments in `.env` files (Pydantic parsing issue)
   - Document correct format prominently in setup guides
