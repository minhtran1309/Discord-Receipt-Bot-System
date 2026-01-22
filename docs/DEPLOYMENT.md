# GCP Deployment & CI/CD Pipeline Setup

## Overview

This guide covers the complete setup for deploying the Discord Receipt Bot to Google Cloud Platform (GCP) with automated CI/CD pipelines using GitHub Actions.

## Current GCP Setup

- **GCP Project**: `GCP-discord-receipts-bot`
- **Compute Instance**: `discord-bot-server`
- **Zone**: `australia-southeast1-a`
- **Bot User**: `botuser`
- **Application Directory**: `/opt/discord-bot/app`
- **Log Directory**: `/var/log/discord-bot`
- **Miniconda**: `/opt/miniconda`

## Architecture

### Application Structure
- **Entry Point**: `python -m bot.main`
- **Python Version**: 3.11+
- **Framework**: discord.py 2.x with async/await
- **Dependencies**: Conda environment (environment.yml + requirements.txt)

### External APIs Required
1. Discord Bot API (token required)
2. Mistral OCR API (API key required)
3. OpenRouter AI API (API key required)
4. Google Sheets API (service account JSON required)

### Data Persistence
- **Receipts**: `data/receipts/*.json`
- **Items**: `data/items/*.tsv`
- **Corrections**: `data/corrections.json`

## Deployment Strategy

### Git-Based Deployment (Recommended)

The deployment uses git operations on the server for fast, atomic updates:

**How it works:**
1. Repository is cloned once on the server at `/opt/discord-bot/app/`
2. Deployments use `git fetch` + `git reset --hard origin/<branch>`
3. Only transfers changed files (git deltas)
4. GitHub Actions sends a small deployment script via SCP

**Benefits:**
- **50-250x faster** than copying entire codebase
- **Atomic updates** - consistent state guaranteed
- **Easy rollbacks** - use git commit hashes
- **Bandwidth efficient** - typical deployment < 5MB

### Separate Environment Approach (Recommended)

Use **three separate Discord bot applications** for complete environment isolation:

1. **Local Development Bot**:
   - Discord Application: "Receipt Bot (Local)"
   - Token: Stored in local `.env`
   - Guild: Your personal test server (set DISCORD_GUILD_ID for instant sync)
   - Spreadsheet: Local or development Google Sheet
   - Purpose: Local testing on your machine

2. **GCP Development Bot**:
   - Discord Application: "Receipt Bot (Dev)"
   - Token: Stored in `.env.development` on GCP server
   - Guild: Team test server (set DISCORD_GUILD_ID for instant sync)
   - Spreadsheet: Development Google Sheet
   - Service: `discord-bot-dev.service`

3. **GCP Production Bot**:
   - Discord Application: "Receipt Bot (Production)"
   - Token: Stored in `.env.production` on GCP server
   - Guild: All servers (leave DISCORD_GUILD_ID empty for global commands)
   - Spreadsheet: Production Google Sheet
   - Service: `discord-bot.service`

**Benefits**:
- **Complete isolation** - Local testing doesn't affect dev/production
- **Prevents accidents** - Can't accidentally impact production users
- **Security** - If local token leaks, production is safe
- **Fast development** - Instant command sync in test servers (guild-specific)
- **Independent rate limits** - Each bot has separate API quotas
- **Separate data storage** - Local vs `data-dev/` vs `data/`

**Important Notes**:
- **DISCORD_TOKEN**: Always use different tokens for each environment
- **DISCORD_GUILD_ID**:
  - Local/Dev: Set to test server ID (instant command registration)
  - Production: Leave empty (global commands, 1 hour sync time)
- You can use the same test server for local and dev, but separate servers are cleaner

## Discord Bot Setup

### Creating Separate Bot Applications

Before deploying, create three separate Discord bot applications:

**Step 1: Create Bot Applications**

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create three applications:
   - "Receipt Bot (Local)" - For local development
   - "Receipt Bot (Dev)" - For GCP development environment
   - "Receipt Bot (Production)" - For GCP production environment

**Step 2: Configure Each Bot**

For each application:
1. Go to **Bot** section
2. Click **Reset Token** and copy the token (save securely)
3. Enable these **Privileged Gateway Intents**:
   - Message Content Intent (if reading message content)
   - Server Members Intent (if needed)
4. Set **Bot Permissions**:
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands

**Step 3: Invite Bots to Servers**

For each bot, generate an invite URL:
1. Go to **OAuth2 > URL Generator**
2. Select scopes: `bot`, `applications.commands`
3. Select bot permissions (same as above)
4. Copy the generated URL and invite to appropriate servers:
   - **Local Bot**: Your personal test server
   - **Dev Bot**: Team test server
   - **Production Bot**: Production servers (or leave for later)

**Step 4: Get Guild IDs (for test servers)**

1. Enable Discord Developer Mode: Settings > Advanced > Developer Mode
2. Right-click your test server > Copy Server ID
3. Save for `DISCORD_GUILD_ID` in environment files

## GCP Server Setup

### Step 0: Initial Repository Setup (One-Time)

**IMPORTANT**: Before running any deployment, the repository must be cloned on the server.

SSH into your GCP server:

```bash
gcloud compute ssh discord-bot-server --zone=australia-southeast1-a
```

Clone the repository:

```bash
# Switch to botuser
sudo su - botuser

# Navigate to application directory (create if needed)
sudo mkdir -p /opt/discord-bot/app
sudo chown -R botuser:botuser /opt/discord-bot
cd /opt/discord-bot/app

# Clone repository
git clone https://github.com/YOUR_USERNAME/Discord-Receipt-Bot-System.git .

# Verify clone
ls -la
git status
```

Create the conda environment setup script:

```bash
sudo -u botuser bash << 'EOF'
cd /opt/discord-bot/app
/opt/miniconda/bin/conda init bash
source ~/.bashrc
/opt/miniconda/bin/conda env create -f environment.yml
EOF
```

Verify installation:

```bash
sudo -u botuser bash << 'EOF'
source /opt/miniconda/etc/profile.d/conda.sh
conda activate discord-bot
python --version
python -c "import discord; print(discord.__version__)"
EOF
```

### Step 2: Environment Configuration

**⚠️ IMPORTANT**: Do not add inline comments after values in `.env` files! Pydantic will include the entire line as the value, causing parsing errors.

**Example of INCORRECT format**:
```bash
DISCORD_TOKEN=your_token_here  # This comment will break it!
```

**Example of CORRECT format**:
```bash
# Comment on its own line
DISCORD_TOKEN=your_token_here
```

---

Create production environment file:

```bash
sudo nano /opt/discord-bot/app/.env.production
```

```bash
# Discord
DISCORD_TOKEN=<production_token>
# Leave DISCORD_GUILD_ID empty for global commands
DISCORD_GUILD_ID=

# APIs
MISTRAL_API_KEY=<production_key>
OPENROUTER_API_KEY=<production_key>

# Google Sheets
GOOGLE_CREDENTIALS_PATH=/opt/discord-bot/app/credentials/credentials.production.json
GOOGLE_SPREADSHEET_ID=<production_sheet_id>

# App Settings
CONFIDENCE_THRESHOLD=0.7
DATA_DIR=data
LOG_LEVEL=INFO
BOT_NAME=Receipt Bot (Production)
```

Create development environment file:

```bash
sudo nano /opt/discord-bot/app/.env.development
```

```bash
# Discord - use separate dev bot token
DISCORD_TOKEN=<development_token>
# Set DISCORD_GUILD_ID to your test server ID for faster command sync
DISCORD_GUILD_ID=<your_test_server_id>

# APIs
MISTRAL_API_KEY=<dev_key_or_same>
OPENROUTER_API_KEY=<dev_key_or_same>

# Google Sheets - separate dev spreadsheet
GOOGLE_CREDENTIALS_PATH=/opt/discord-bot/app/credentials/credentials.development.json
GOOGLE_SPREADSHEET_ID=<development_sheet_id>

# App Settings
CONFIDENCE_THRESHOLD=0.7
DATA_DIR=data
LOG_LEVEL=DEBUG
BOT_NAME=Receipt Bot (Dev)
```

Set proper permissions:

```bash
sudo chmod 600 /opt/discord-bot/app/.env.production
sudo chmod 600 /opt/discord-bot/app/.env.development
sudo chown botuser:botuser /opt/discord-bot/app/.env.*
```

Create credentials directory:

```bash
sudo mkdir -p /opt/discord-bot/app/credentials
sudo chmod 700 /opt/discord-bot/app/credentials
sudo chown botuser:botuser /opt/discord-bot/app/credentials
```

Upload credentials files (from local machine):

```bash
gcloud compute scp credentials.production.json discord-bot-server:/tmp/ --zone=australia-southeast1-a
gcloud compute scp credentials.development.json discord-bot-server:/tmp/ --zone=australia-southeast1-a

# Then on server:
sudo mv /tmp/credentials.production.json /opt/discord-bot/app/credentials/
sudo mv /tmp/credentials.development.json /opt/discord-bot/app/credentials/
sudo chmod 600 /opt/discord-bot/app/credentials/*.json
sudo chown botuser:botuser /opt/discord-bot/app/credentials/*.json
```

### Step 3: Systemd Service Configuration

Create production service:

```bash
sudo nano /etc/systemd/system/discord-bot.service
```

```ini
[Unit]
Description=Discord Receipt Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/discord-bot/app

# Environment
Environment="PATH=/home/botuser/.conda/envs/discord_env/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/discord-bot/app/.env.production

# Execution
ExecStart=/home/botuser/.conda/envs/discord_env/bin/python -m bot.main
ExecReload=/bin/kill -HUP $MAINPID

# Restart policy
Restart=always
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/discord-bot/data /var/log/discord-bot

# Resource limits
LimitNOFILE=4096
MemoryMax=1G

[Install]
WantedBy=multi-user.target
```

Create development service:

```bash
sudo nano /etc/systemd/system/discord-bot-dev.service
```

```ini
[Unit]
Description=Discord Receipt Bot (Development)
After=network.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/opt/discord-bot/app

Environment="PATH=/home/botuser/.conda/envs/discord_env/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/discord-bot/app/.env.development

ExecStart=/home/botuser/.conda/envs/discord_env/bin/python -m bot.main

Restart=always
RestartSec=10s

StandardOutput=journal
StandardError=journal
SyslogIdentifier=discord-bot-dev

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable discord-bot.service
sudo systemctl enable discord-bot-dev.service

# Start services
sudo systemctl start discord-bot.service
sudo systemctl start discord-bot-dev.service

# Check status
sudo systemctl status discord-bot.service
sudo systemctl status discord-bot-dev.service
```

Set environment symlink (for manual deployment):

```bash
# Production (default)
sudo ln -sf /opt/discord-bot/app/.env.production /opt/discord-bot/app/.env

# OR Development
sudo ln -sf /opt/discord-bot/app/.env.development /opt/discord-bot/app/.env
```

### Step 4: Configure Sudo Permissions for Deployment

Grant botuser permissions to restart services (required for CI/CD):

```bash
sudo nano /etc/sudoers.d/botuser-discord-bot
```

Add:

```
botuser ALL=(ALL) NOPASSWD: /bin/systemctl restart discord-bot.service
botuser ALL=(ALL) NOPASSWD: /bin/systemctl restart discord-bot-dev.service
botuser ALL=(ALL) NOPASSWD: /bin/systemctl status discord-bot.service
botuser ALL=(ALL) NOPASSWD: /bin/systemctl status discord-bot-dev.service
botuser ALL=(ALL) NOPASSWD: /bin/systemctl is-active discord-bot.service
botuser ALL=(ALL) NOPASSWD: /bin/systemctl is-active discord-bot-dev.service
botuser ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u discord-bot.service *
botuser ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u discord-bot-dev.service *
```

Set proper permissions:

```bash
sudo chmod 440 /etc/sudoers.d/botuser-discord-bot
sudo visudo -c  # Verify syntax
```

## GitHub Actions CI/CD Setup

### Step 1: Create GCP Service Account

Create service account for GitHub Actions:

```bash
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions Deployment"

# Grant necessary permissions
gcloud projects add-iam-policy-binding GCP-discord-receipts-bot \
    --member="serviceAccount:github-actions@GCP-discord-receipts-bot.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding GCP-discord-receipts-bot \
    --member="serviceAccount:github-actions@GCP-discord-receipts-bot.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@GCP-discord-receipts-bot.iam.gserviceaccount.com

# Display contents (copy to GitHub Secrets)
cat github-actions-key.json
```

### Step 2: Configure GitHub Secrets

Go to: **Repository Settings > Secrets and variables > Actions**

Add the following secrets:

**GCP Service Account Key:**
- **Name**: `GCP_SA_KEY`
- **Value**: Contents of `github-actions-key.json`

**Google Credentials (Base64 Encoded):**

First, encode your credentials files:
```bash
# For development credentials
base64 -i credentials-dev.json | tr -d '\n' > credentials-dev-base64.txt

# For production credentials
base64 -i credentials-prod.json | tr -d '\n' > credentials-prod-base64.txt
```

Then add these secrets:
- **Name**: `GOOGLE_CREDENTIALS_DEV`
- **Value**: Contents of `credentials-dev-base64.txt`

- **Name**: `GOOGLE_CREDENTIALS_PROD`
- **Value**: Contents of `credentials-prod-base64.txt`

**Security Note**: Base64 encoding is used to safely transfer the JSON credentials through GitHub Actions without newline/formatting issues. The credentials are decoded and installed securely on the server during deployment.

### Step 3: Workflow Files

The repository includes two workflow files:

1. **`.github/workflows/deploy-production.yml`**
   - Triggers on push to `main` branch
   - Runs tests (pytest, black, isort, mypy)
   - Decodes and installs `GOOGLE_CREDENTIALS_PROD` to server
   - Deploys to production environment
   - Restarts `discord-bot.service`

2. **`.github/workflows/deploy-development.yml`**
   - Triggers on push to **ANY branch except `main`** (uses `branches-ignore`)
   - Triggers on pull requests targeting `main` (tests only, no deployment)
   - Runs tests (failures allowed for dev)
   - Decodes and installs `GOOGLE_CREDENTIALS_DEV` to server
   - Deploys to development environment
   - Restarts `discord-bot-dev.service`

### Workflow Trigger Behavior

The development workflow uses this trigger configuration:

```yaml
on:
  push:
    branches-ignore:
      - main  # Deploy to dev for ANY branch except main
  pull_request:
    branches: [ main ]
```

**What happens in each scenario:**

| Action | Branch | Dev Workflow | Prod Workflow |
|--------|--------|--------------|---------------|
| Push | `feature-branch` | ✅ Tests + Deploy | ❌ |
| Push | `any-new-branch` | ✅ Tests + Deploy | ❌ |
| Push | `main` | ❌ | ✅ Tests + Deploy |
| PR created | → `main` | ✅ Tests only | ❌ |
| PR merged | → `main` | ❌ | ✅ Tests + Deploy |

**Detailed Scenarios:**

1. **Push to feature branch** (e.g., `git push origin my-feature`):
   - Dev workflow triggers because `my-feature` ≠ `main`
   - Tests run → Deploy to dev server → Restart `discord-bot-dev.service`

2. **Create Pull Request to `main`**:
   - Dev workflow triggers for `pull_request` event
   - Tests run only (deployment skipped via `if: github.event_name == 'push'`)
   - This validates code before merge without affecting dev server

3. **Merge PR to `main`**:
   - Creates a push event to `main`
   - Dev workflow **skips** (because of `branches-ignore: [main]`)
   - Production workflow **triggers** (because of `push: branches: [main]`)
   - Tests run → Deploy to prod server → Restart `discord-bot.service`

**How Credentials are Deployed:**

Both workflows automatically handle Google credentials deployment:
1. **GitHub Action** reads the base64-encoded secret (e.g., `GOOGLE_CREDENTIALS_PROD`)
2. Transfers the encoded credentials to the GCP server via `gcloud compute scp`
3. **Deployment script** on the server:
   - Decodes the base64 string back to JSON
   - Saves to `/opt/discord-bot/app/credentials/credentials.{environment}.json`
   - Sets secure permissions (`chmod 600`)
   - Removes the temporary base64 file
4. The bot service reads the credentials from the installed location

This approach ensures:
- ✅ **Secure transfer** - Credentials never exposed in logs
- ✅ **Automatic updates** - New credentials deployed on every push
- ✅ **Environment isolation** - Dev and prod use separate credential files
- ✅ **No manual steps** - Fully automated deployment

## Deployment Script

The deployment script (`scripts/deploy.sh`) handles:

1. **Backup**: Creates timestamped backup before deployment
2. **Service Stop**: Stops appropriate service (production or dev)
3. **Code Sync**: Uses rsync to sync code (excludes data, credentials)
4. **Permissions**: Sets correct ownership and permissions
5. **Environment Update**: Updates conda environment and pip packages
6. **Symlink**: Sets correct environment file
7. **Service Start**: Starts and enables service
8. **Verification**: Checks service status after deployment

Usage:

```bash
# Production deployment
sudo bash /path/to/deploy.sh production

# Development deployment
sudo bash /path/to/deploy.sh development
```

## Manual Deployment CLI Commands

When you need to deploy manually (bypassing GitHub Actions), use these commands:

### GitHub CLI - Trigger Workflow Manually

```bash
# Trigger production deployment workflow
gh workflow run "Deploy to Production (GCP)"

# Trigger development deployment workflow
gh workflow run "Deploy to Development (GCP)"

# Check workflow run status
gh run list --workflow="Deploy to Production (GCP)" --limit 5
```

### gcloud CLI - Deploy Directly on Server

**Production Deployment:**

```bash
gcloud compute ssh botuser@discord-bot-server --zone=australia-southeast1-a --command="cd /opt/discord-bot/app && git fetch origin main && git reset --hard origin/main && source /opt/miniconda/etc/profile.d/conda.sh && conda activate discord_env && pip install -r requirements.txt --quiet && sudo systemctl restart discord-bot.service && sudo systemctl status discord-bot.service"
```

**Development Deployment:**

```bash
# Replace <BRANCH_NAME> with your branch name
gcloud compute ssh botuser@discord-bot-server --zone=australia-southeast1-a --command="cd /opt/discord-bot/app && git fetch origin <BRANCH_NAME> && git reset --hard origin/<BRANCH_NAME> && source /opt/miniconda/etc/profile.d/conda.sh && conda activate discord_env && pip install -r requirements.txt --quiet && sudo systemctl restart discord-bot-dev.service && sudo systemctl status discord-bot-dev.service"
```

**Note:** These commands pull the latest code from the specified branch, install dependencies, and restart the service. Use this when GitHub Actions is unavailable or for emergency deployments.

## Monitoring

### Service Management

```bash
# Check service status
sudo systemctl status discord-bot.service
sudo systemctl status discord-bot-dev.service

# View real-time logs
sudo journalctl -u discord-bot.service -f
sudo journalctl -u discord-bot-dev.service -f

# View logs from last hour
sudo journalctl -u discord-bot.service --since "1 hour ago"

# Restart service
sudo systemctl restart discord-bot.service
sudo systemctl restart discord-bot-dev.service
```

### Monitoring Script

Use the monitoring script for quick health checks:

```bash
sudo bash /opt/discord-bot/scripts/monitor.sh
```

This shows:
- Service status
- Resource usage (CPU, memory)
- Disk usage
- Recent errors from logs

### Resource Monitoring

```bash
# Check resource usage
ps aux | grep "python -m bot.main"
top -u botuser

# Check disk space
df -h /opt/discord-bot/data
du -sh /opt/discord-bot/data/*

# Network connections
sudo netstat -tulpn | grep python
```

## Development Workflow

### Scenario: Testing New Feature

**Step 1: Local Development**

```bash
# Create feature branch
git checkout -b feature/new-feature

# Use development environment locally
cp .env.example .env
# Edit .env with development bot token

# Test locally
python -m bot.main
```

**Step 2: Deploy to Development Environment**

```bash
# Push to trigger dev deployment
git push origin feature/new-feature

# GitHub Actions automatically:
# 1. Runs tests
# 2. Deploys to discord-bot-dev.service
# 3. Uses .env.development configuration

# Monitor deployment
gcloud compute ssh discord-bot-server --zone=australia-southeast1-a
sudo journalctl -u discord-bot-dev.service -f
```

**Step 3: Production Deployment**

```bash
# After testing, merge to main
git checkout main
git merge feature/new-feature
git push origin main

# GitHub Actions automatically:
# 1. Runs tests
# 2. Deploys to discord-bot.service
# 3. Uses .env.production configuration
```

## Rollback Procedures

### Option 1: Restore from Backup

```bash
# SSH to server
gcloud compute ssh discord-bot-server --zone=australia-southeast1-a

# Stop service
sudo systemctl stop discord-bot.service

# Restore from backup
cd /opt/discord-bot/backups
BACKUP=$(ls -t discord-bot-*.tar.gz | head -1)
sudo tar -xzf $BACKUP -C /opt/discord-bot

# Restart service
sudo systemctl start discord-bot.service
```

### Option 2: Git Revert

```bash
# On local machine
git revert <commit-hash>
git push origin main

# GitHub Actions will auto-deploy previous version
```

## Troubleshooting

### Service Fails to Start

```bash
# Check logs
sudo journalctl -u discord-bot.service -n 100

# Common causes:
# - Missing .env file
# - Invalid credentials.json
# - Wrong file permissions
# - Conda environment not activated
```

### Bot Connects but Commands Don't Work

```bash
# Verify Discord token
sudo -u botuser bash
source /opt/miniconda/etc/profile.d/conda.sh
conda activate discord-bot
cd /opt/discord-bot
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DISCORD_TOKEN')[:20])"

# Note: Commands take up to 1 hour to register globally
# Set DISCORD_GUILD_ID for instant registration in test server
```

### GitHub Actions Deployment Fails

```
# Check GitHub Actions logs
# Common issues:
# - GCP_SA_KEY not configured
# - Service account lacks permissions
# - SSH key issues
# - Network connectivity

# Debug deployment script locally:
bash scripts/deploy.sh development
```

### Pull Request Deployment Error: "fatal: couldn't find remote ref merge"

**Symptom**: Pull requests fail with error `fatal: couldn't find remote ref merge` during deployment.

**Cause**: GitHub Actions tries to deploy on pull request events, but `GITHUB_REF` for PRs is `refs/pull/123/merge` which doesn't exist as a remote branch.

**Solution**: This has been fixed in the workflow. Pull requests now only run tests without attempting deployment. The workflow uses `if: github.event_name == 'push'` to skip deployment for PRs.

**Verification**:
- Push events (to `guess_feature` or `clerk_feature_dev`) → Tests + Deployment
- Pull requests (to `main`) → Tests only (no deployment)

### Data Directory / /clerk sync Failures

**Symptom**: `/clerk sync` command fails, or receipts are not found even though they were processed.

**Causes**:
1. Data directory path mismatch between bot code and systemd configuration
2. Incorrect permissions on data directory
3. Wrong `DATA_DIR` in `.env` file

**Solution**:

1. **Verify data directory location**:
   ```bash
   # On GCP server
   ls -la /opt/discord-bot/app/data/receipts/
   ls -la /opt/discord-bot/app/data/items/
   ```

2. **Check .env configuration**:
   ```bash
   # Should use relative path (relative to WorkingDirectory)
   DATA_DIR=data

   # NOT absolute path like:
   # DATA_DIR=/opt/discord-bot/data  ❌ WRONG
   ```

3. **Re-run systemd setup** (fixes ReadWritePaths):
   ```bash
   cd /opt/discord-bot/app
   git pull origin guess_feature
   bash scripts/setup_systemd_services.sh
   sudo systemctl daemon-reload
   sudo systemctl restart discord-bot-dev.service
   ```

4. **Fix permissions**:
   ```bash
   sudo chown -R botuser:botuser /opt/discord-bot/app/data
   sudo chmod -R 755 /opt/discord-bot/app/data
   ```

**See also**: [docs/DATA_DIRECTORY_FIX.md](DATA_DIRECTORY_FIX.md) for complete troubleshooting guide.

## Security Best Practices

1. **Never commit secrets**:
   - Add `.env*` to .gitignore
   - Add `credentials/*.json` to .gitignore
   - Use GitHub Secrets or GCP Secret Manager

2. **Use separate bot tokens**:
   - Different token for production vs development
   - Prevents accidental production impact during testing

3. **Limit service account permissions**:
   - Only grant necessary IAM roles
   - Use separate service accounts for CI/CD vs bot runtime

4. **Restrict file permissions**:
   ```bash
   chmod 600 .env.production
   chmod 700 credentials/
   ```

5. **Regular secret rotation**:
   - Rotate Discord bot tokens quarterly
   - Rotate API keys annually
   - Rotate Google service account keys annually

## Verification Tests

### Test 1: Service Health

```bash
sudo systemctl status discord-bot.service
# Should show "active (running)"
```

### Test 2: Bot Responsiveness

```
# In Discord server
/receipt list
# Should respond with list of receipts
```

### Test 3: Log Monitoring

```bash
sudo journalctl -u discord-bot.service --since "5 minutes ago"
# Should show bot startup and command activity
```

### Test 4: API Connectivity

```bash
# Check if bot can reach external APIs
sudo -u botuser bash
cd /opt/discord-bot/app
source /opt/miniconda/etc/profile.d/conda.sh
conda activate discord-bot
python -c "import httpx; print(httpx.get('https://api.mistral.ai').status_code)"
```

### Test 5: Data Persistence

```
# Upload receipt via /receipt process
# SSH to server and verify file exists:
ls -lh /opt/discord-bot/data/receipts/
```

## Additional Resources

- [Discord Bot Token Guide](https://discord.com/developers/docs/getting-started)
- [GCP Compute Engine Documentation](https://cloud.google.com/compute/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
