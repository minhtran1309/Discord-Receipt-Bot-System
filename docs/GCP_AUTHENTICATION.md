# GCP Authentication for GitHub Actions

## Overview

This document explains how GitHub Actions authenticates with Google Cloud Platform (GCP) to deploy the Discord Receipt Bot to GCP Compute Engine instances.

## Problem Statement

When GitHub Actions tries to deploy to GCP, it needs two separate sets of credentials:

1. **GCP Compute Engine Access**: To SSH into the VM, transfer files, and execute commands
2. **Google Sheets Access**: To allow the bot application to read/write spreadsheet data

Initially, the workflow was incorrectly using Google Sheets credentials (`GOOGLE_CREDENTIALS_DEV/PROD`) for GCP Compute Engine authentication, which caused the following error:

```
ERROR: (gcloud.compute.scp) Could not fetch resource:
 - Required 'compute.instances.get' permission for 'projects/gcp-discord-receipt-bot/zones/australia-southeast1-a/instances/discord-bot-server'
```

## Solution: Separate Authentication Credentials

### 1. GCP_SA_KEY - For Compute Engine Access

**Purpose**: Authenticates GitHub Actions to access GCP Compute Engine resources (VMs, SSH, file transfers)

**What it is**: A service account key for `github-actions@gcp-discord-receipt-bot.iam.gserviceaccount.com`

**Permissions granted** (via `scripts/gcp_permission.sh`):
- `roles/compute.instanceAdmin.v1` - Manage VM instances
- `roles/iam.serviceAccountUser` - Act as service account
- `roles/compute.osLogin` - SSH access to VMs
- `roles/compute.viewer` - View compute resources

**Where it's used in workflows**:

#### Development Workflow (`.github/workflows/deploy-development.yml`)

```yaml
# Line 48-51: Authenticate to Google Cloud for Compute Engine operations
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}  # ← Uses GCP_SA_KEY

# Line 53-54: Set up gcloud CLI with authenticated credentials
- name: Set up Cloud SDK
  uses: google-github-actions/setup-gcloud@v2

# Lines 95-106: Uses authenticated gcloud to transfer files and SSH
- gcloud compute scp /tmp/credentials-dev-base64.txt botuser@${{ env.GCP_INSTANCE }}:/tmp/
- gcloud compute scp deploy-dev.sh botuser@${{ env.GCP_INSTANCE }}:/tmp/deploy-dev.sh
- gcloud compute ssh botuser@${{ env.GCP_INSTANCE }} --command="..."
```

#### Production Workflow (`.github/workflows/deploy-production.yml`)

```yaml
# Line 56-59: Authenticate to Google Cloud for Compute Engine operations
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}  # ← Uses GCP_SA_KEY

# Line 61-62: Set up gcloud CLI with authenticated credentials
- name: Set up Cloud SDK
  uses: google-github-actions/setup-gcloud@v2

# Lines 102-113: Uses authenticated gcloud to transfer files and SSH
- gcloud compute scp /tmp/credentials-prod-base64.txt botuser@${{ env.GCP_INSTANCE }}:/tmp/
- gcloud compute scp deploy.sh botuser@${{ env.GCP_INSTANCE }}:/tmp/deploy.sh
- gcloud compute ssh botuser@${{ env.GCP_INSTANCE }} --command="..."
```

### 2. GOOGLE_CREDENTIALS_DEV / GOOGLE_CREDENTIALS_PROD - For Google Sheets Access

**Purpose**: Authenticates the Discord bot application to access Google Sheets API

**What they are**: Base64-encoded service account keys for the bot to read/write spreadsheet data

**Where they're used in workflows**:

```yaml
# Lines 94-97 (development) / Lines 101-104 (production)
# Transfer encoded Google Sheets credentials to server
echo "${{ secrets.GOOGLE_CREDENTIALS_DEV }}" > /tmp/credentials-dev-base64.txt
gcloud compute scp /tmp/credentials-dev-base64.txt botuser@${{ env.GCP_INSTANCE }}:/tmp/
```

**On the server** (inside deployment script):

```bash
# Lines 71-78: Decode and install Google Sheets credentials
if [ -f /tmp/credentials-dev-base64.txt ]; then
  echo "📦 Installing development Google credentials..."
  mkdir -p /opt/discord-bot/app/credentials
  base64 -d /tmp/credentials-dev-base64.txt > /opt/discord-bot/app/credentials/credentials.development.json
  chmod 600 /opt/discord-bot/app/credentials/credentials.development.json
  rm /tmp/credentials-dev-base64.txt
  echo "✅ Google credentials installed"
fi
```

The bot application then reads these credentials from `/opt/discord-bot/app/credentials/credentials.{environment}.json` to access Google Sheets.

## Workflow Authentication Flow

Here's the complete authentication flow:

```
┌─────────────────────────────────────────────────────────────┐
│ GitHub Actions Workflow                                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 1. Authenticate to Google Cloud                              │
│    ├─ Uses: GCP_SA_KEY secret                               │
│    └─ Grants: gcloud CLI access to Compute Engine          │
│                                                               │
│ 2. Transfer Google Sheets credentials to server              │
│    ├─ Uses: GOOGLE_CREDENTIALS_DEV/PROD secret             │
│    ├─ Command: gcloud compute scp (authenticated via step 1)│
│    └─ Destination: /tmp/credentials-*-base64.txt           │
│                                                               │
│ 3. Transfer deployment script to server                      │
│    ├─ Command: gcloud compute scp (authenticated via step 1)│
│    └─ Destination: /tmp/deploy-dev.sh                       │
│                                                               │
│ 4. Execute deployment script on server                       │
│    ├─ Command: gcloud compute ssh (authenticated via step 1)│
│    └─ Script: /tmp/deploy-dev.sh                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ GCP Server (discord-bot-server)                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Deployment Script (deploy-dev.sh) runs:                      │
│                                                               │
│ 1. Pull latest code from git                                 │
│    └─ git reset --hard origin/branch                         │
│                                                               │
│ 2. Install Google Sheets credentials                         │
│    ├─ Decode: base64 -d /tmp/credentials-dev-base64.txt     │
│    └─ Install: → credentials/credentials.development.json   │
│                                                               │
│ 3. Update conda environment                                  │
│    └─ conda env update -f environment.yml                    │
│                                                               │
│ 4. Restart bot service                                       │
│    └─ sudo systemctl restart discord-bot-dev.service        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Discord Bot Application                                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Bot reads Google Sheets credentials:                         │
│    ├─ Path: credentials/credentials.development.json        │
│    └─ Uses: To read/write Google Sheets data                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### Step 1: Create GCP Service Account Key

Run the provided script to generate the service account key:

```bash
bash scripts/create_gcp_sa_key.sh
```

This creates `github-actions-key.json` with the service account credentials.

### Step 2: Grant GCP Permissions

Grant the necessary IAM roles to the service account:

```bash
bash scripts/gcp_permission.sh
```

This grants:
- Compute Instance Admin (manage VMs)
- Service Account User (act as service account)
- Compute OS Login (SSH access)
- Compute Viewer (view resources)

### Step 3: Add GitHub Secret

1. Copy the contents of `github-actions-key.json`
2. Go to GitHub: **Repository Settings → Secrets and variables → Actions**
3. Create new secret:
   - **Name**: `GCP_SA_KEY`
   - **Value**: [Paste entire JSON contents]

### Step 4: Clean Up

Delete the local key file for security:

```bash
rm github-actions-key.json
```

## Security Considerations

### Why Separate Credentials?

1. **Principle of Least Privilege**: Each credential has only the permissions it needs
   - `GCP_SA_KEY`: Only Compute Engine access (no Sheets access)
   - `GOOGLE_CREDENTIALS_*`: Only Google Sheets access (no Compute access)

2. **Credential Rotation**: Can rotate each credential independently without affecting the other

3. **Audit Trail**: Separate service accounts provide clear audit logs for different operations

### Credential Storage

- **GitHub Secrets**: Encrypted at rest, only accessible to workflow runs
- **GCP Server**: Credentials stored with `chmod 600` (owner read/write only)
- **Never Committed**: All credential files are in `.gitignore`

## Troubleshooting

### Error: "Required 'compute.instances.get' permission"

**Cause**: Workflow is using wrong credentials for GCP authentication

**Solution**: Verify workflow uses `GCP_SA_KEY` (not `GOOGLE_CREDENTIALS_*`) for the "Authenticate to Google Cloud" step

### Error: "Permission denied (publickey)"

**Cause**: Service account lacks `compute.osLogin` role

**Solution**: Re-run `scripts/gcp_permission.sh` to grant OS Login role

### Error: "Failed to create service account key"

**Cause**: May have reached key limit (10 keys per service account)

**Solution**: Delete old unused keys:

```bash
gcloud iam service-accounts keys list --iam-account=github-actions@gcp-discord-receipt-bot.iam.gserviceaccount.com
gcloud iam service-accounts keys delete KEY_ID --iam-account=github-actions@gcp-discord-receipt-bot.iam.gserviceaccount.com
```

## Summary

| Secret Name | Purpose | Used By | Permissions |
|-------------|---------|---------|-------------|
| `GCP_SA_KEY` | GCP Compute Engine access | GitHub Actions workflow | Compute Instance Admin, OS Login, Viewer |
| `GOOGLE_CREDENTIALS_DEV` | Google Sheets access (dev) | Discord bot application | Sheets API read/write |
| `GOOGLE_CREDENTIALS_PROD` | Google Sheets access (prod) | Discord bot application | Sheets API read/write |

**Key Takeaway**: `GCP_SA_KEY` is for GitHub Actions to access GCP infrastructure, while `GOOGLE_CREDENTIALS_*` are for the bot application to access Google Sheets data.
