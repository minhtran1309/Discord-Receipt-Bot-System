# GCP Deployment & CI/CD Pipeline Setup

## Overview

This guide covers the complete setup for deploying the Discord Receipt Bot to Google Cloud Platform (GCP) with automated CI/CD pipelines using GitHub Actions.

## Current GCP Setup

- **GCP Project**: `GCP-discord-receipts-bot`
- **Compute Instance**: `discord-bot-server`
- **Zone**: `australia-southeast1-a`
- **Bot User**: `botuser`
- **Application Directory**: `/opt/discord-bot`
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

### Separate Environment Approach (Recommended)

Use two separate Discord bot applications:

1. **Production Bot**:
   - Discord Application: "Receipt Bot (Production)"
   - Token: Stored in `.env.production`
   - Guild: All servers (leave DISCORD_GUILD_ID empty)
   - Spreadsheet: Production Google Sheet
   - Service: `discord-bot.service`

2. **Development Bot**:
   - Discord Application: "Receipt Bot (Development)"
   - Token: Stored in `.env.development`
   - Guild: Your test server only (set DISCORD_GUILD_ID for instant sync)
   - Spreadsheet: Development Google Sheet
   - Service: `discord-bot-dev.service`

**Benefits**:
- Complete isolation between environments
- Test new features safely without affecting production
- Instant command sync in development (guild-specific)
- Separate data storage (`data/` vs `data-dev/`)
- Both services run simultaneously on same GCP server

## GCP Server Setup

### Step 1: Conda Environment Setup

SSH into your GCP server:

```bash
gcloud compute ssh discord-bot-server --zone=australia-southeast1-a
```

Create the conda environment setup script:

```bash
sudo -u botuser bash << 'EOF'
cd /opt/discord-bot
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

Create production environment file:

```bash
sudo nano /opt/discord-bot/.env.production
```

```bash
# Discord
DISCORD_TOKEN=<production_token>
DISCORD_GUILD_ID=  # Leave empty for global commands

# APIs
MISTRAL_API_KEY=<production_key>
OPENROUTER_API_KEY=<production_key>

# Google Sheets
GOOGLE_CREDENTIALS_PATH=/opt/discord-bot/credentials/credentials.production.json
GOOGLE_SPREADSHEET_ID=<production_sheet_id>

# App Settings
CONFIDENCE_THRESHOLD=0.7
DATA_DIR=/opt/discord-bot/data
LOG_LEVEL=INFO
```

Create development environment file:

```bash
sudo nano /opt/discord-bot/.env.development
```

```bash
# Discord (use separate dev bot token)
DISCORD_TOKEN=<development_token>
DISCORD_GUILD_ID=<your_test_server_id>  # Faster command sync

# APIs
MISTRAL_API_KEY=<dev_key_or_same>
OPENROUTER_API_KEY=<dev_key_or_same>

# Google Sheets (separate dev spreadsheet)
GOOGLE_CREDENTIALS_PATH=/opt/discord-bot/credentials/credentials.development.json
GOOGLE_SPREADSHEET_ID=<development_sheet_id>

# App Settings
CONFIDENCE_THRESHOLD=0.7
DATA_DIR=/opt/discord-bot/data-dev
LOG_LEVEL=DEBUG
```

Set proper permissions:

```bash
sudo chmod 600 /opt/discord-bot/.env.production
sudo chmod 600 /opt/discord-bot/.env.development
sudo chown botuser:botuser /opt/discord-bot/.env.*
```

Create credentials directory:

```bash
sudo mkdir -p /opt/discord-bot/credentials
sudo chmod 700 /opt/discord-bot/credentials
sudo chown botuser:botuser /opt/discord-bot/credentials
```

Upload credentials files (from local machine):

```bash
gcloud compute scp credentials.production.json discord-bot-server:/tmp/ --zone=australia-southeast1-a
gcloud compute scp credentials.development.json discord-bot-server:/tmp/ --zone=australia-southeast1-a

# Then on server:
sudo mv /tmp/credentials.production.json /opt/discord-bot/credentials/
sudo mv /tmp/credentials.development.json /opt/discord-bot/credentials/
sudo chmod 600 /opt/discord-bot/credentials/*.json
sudo chown botuser:botuser /opt/discord-bot/credentials/*.json
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
WorkingDirectory=/opt/discord-bot

# Environment
Environment="PATH=/opt/miniconda/envs/discord-bot/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/discord-bot/.env

# Execution
ExecStart=/opt/miniconda/envs/discord-bot/bin/python -m bot.main
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
WorkingDirectory=/opt/discord-bot

Environment="PATH=/opt/miniconda/envs/discord-bot/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/discord-bot/.env.development

ExecStart=/opt/miniconda/envs/discord-bot/bin/python -m bot.main

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
sudo ln -sf /opt/discord-bot/.env.production /opt/discord-bot/.env

# OR Development
sudo ln -sf /opt/discord-bot/.env.development /opt/discord-bot/.env
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

Add the following secret:

- **Name**: `GCP_SA_KEY`
- **Value**: Contents of `github-actions-key.json`

### Step 3: Workflow Files

The repository includes two workflow files:

1. **`.github/workflows/deploy-production.yml`**
   - Triggers on push to `main` branch
   - Runs tests (pytest, black, isort, mypy)
   - Deploys to production environment
   - Restarts `discord-bot.service`

2. **`.github/workflows/deploy-development.yml`**
   - Triggers on push to `develop`, `guess_feature`, `clerk_feature_dev` branches
   - Runs tests (failures allowed for dev)
   - Deploys to development environment
   - Restarts `discord-bot-dev.service`

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
cd /opt/discord-bot
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
