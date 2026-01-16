# GitHub Actions Workflows Explained

## Overview

This document explains the GitHub Actions workflows configured for the Discord Receipt Bot, specifically the two "Deploy to Development Environment" workflows you see in the Actions tab.

## What are GitHub Actions?

**GitHub Actions** is a CI/CD (Continuous Integration/Continuous Deployment) automation platform built into GitHub. It automatically runs tasks when certain events happen in your repository (like pushing code or creating pull requests).

## The Two Development Workflows

When you look at the **Actions** tab in GitHub, you see two workflows with similar names but different triggers:

### 1. Deploy to Development Environment (push)

**Trigger**: Automatically runs when you **push commits** to specific branches

**File**: `.github/workflows/deploy-development.yml`

**When it runs**:
```yaml
on:
  push:
    branches: [ develop, guess_feature, clerk_feature_dev ]
```

This means the workflow runs automatically whenever you push commits to:
- `develop` branch
- `guess_feature` branch
- `clerk_feature_dev` branch

**What it does**:

1. **Test Stage** (runs first):
   - Checks out your code
   - Sets up Python 3.11
   - Installs all dependencies from `requirements.txt`
   - Runs pytest tests (failures are allowed for dev, won't block deployment)

2. **Deploy Stage** (runs after tests):
   - Authenticates to Google Cloud using `GCP_SA_KEY` secret
   - Transfers base64-encoded Google Sheets credentials (`GOOGLE_CREDENTIALS_DEV`) to the server
   - SSHs into the GCP server (`discord-bot-server`)
   - Runs a deployment script on the server that:
     - Pulls the latest code using `git fetch` and `git reset --hard`
     - Decodes and installs Google Sheets credentials
     - Updates the conda environment
     - Restarts the `discord-bot-dev.service` systemd service
   - Verifies the service started successfully

**Example scenario**:
```bash
# On your local machine
git add .
git commit -m "Add new feature"
git push origin guess_feature  # ← This triggers the workflow!
```

Within seconds, GitHub Actions will:
- Run your tests
- Deploy your code to the GCP development server
- Restart the development bot
- Show you the results in the Actions tab

---

### 2. Deploy to Development Environment (pull_request)

**Trigger**: Automatically runs when you **create or update a pull request** to the `main` branch

**File**: Same file `.github/workflows/deploy-development.yml`

**When it runs**:
```yaml
on:
  pull_request:
    branches: [ main ]
```

This means the workflow runs automatically whenever you:
- Create a new pull request targeting the `main` branch
- Push new commits to an existing pull request

**What it does**:

**IMPORTANT**: This workflow **ONLY runs tests**, it does **NOT deploy** to the server!

1. **Test Stage**:
   - Checks out the code from your pull request
   - Sets up Python 3.11
   - Installs all dependencies
   - Runs pytest tests
   - Reports success/failure on the pull request page

2. **NO Deploy Stage**: The deploy stage is skipped because this is just a pull request review

**Example scenario**:
```bash
# On your local machine (on guess_feature branch)
git push origin guess_feature

# On GitHub website
# Create pull request: guess_feature → main
```

GitHub Actions will:
- Run tests on the pull request code
- Show a green checkmark ✅ or red X ❌ on the pull request
- Help you verify the code works before merging to main
- **Does NOT deploy or change anything on the server**

---

## Key Differences

| Aspect | Push Workflow | Pull Request Workflow |
|--------|--------------|----------------------|
| **Trigger** | Push to `develop`, `guess_feature`, `clerk_feature_dev` | Create/update PR to `main` |
| **Purpose** | Deploy to development server | Test code before merging |
| **Runs tests** | ✅ Yes (failures allowed) | ✅ Yes (strict) |
| **Deploys to GCP** | ✅ Yes | ❌ No |
| **Restarts bot** | ✅ Yes | ❌ No |
| **Use case** | Automatic deployment for testing | Pre-merge code validation |

---

## Production Workflow (for comparison)

**File**: `.github/workflows/deploy-production.yml`

**Trigger**: Push to `main` branch or manual trigger

**What it does**:
1. **Strict testing** (pytest, black, isort, mypy) - must pass!
2. **Deploys to production server** using `discord-bot.service`
3. **Uses production credentials** (`GOOGLE_CREDENTIALS_PROD`)
4. **No test failures allowed** - deployment is blocked if tests fail

---

## Complete Workflow Flow

Here's how the workflows work together in a typical development cycle:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Local Development                                             │
│    - Edit code on guess_feature branch                          │
│    - Commit changes                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Push to Development Branch                                    │
│    git push origin guess_feature                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. GitHub Actions: Deploy to Development (push)                 │
│    ✅ Run tests (failures allowed)                               │
│    ✅ Deploy to GCP dev server                                   │
│    ✅ Restart discord-bot-dev.service                            │
│    ✅ Bot updates automatically!                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Test Bot on Development Server                               │
│    - Bot is running with your new code                          │
│    - Test commands in Discord test server                       │
│    - Verify everything works                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Create Pull Request to Main                                  │
│    - On GitHub: Create PR from guess_feature → main            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. GitHub Actions: Deploy to Development (pull_request)         │
│    ✅ Run tests (strict validation)                              │
│    ❌ NO deployment (just testing)                               │
│    ✅ Green checkmark shows on PR if tests pass                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Merge Pull Request                                           │
│    - Click "Merge" button on GitHub                             │
│    - guess_feature code is now in main branch                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. GitHub Actions: Deploy to Production                         │
│    ✅ Run strict tests (pytest, black, isort, mypy)              │
│    ✅ Deploy to GCP production server                            │
│    ✅ Restart discord-bot.service                                │
│    ✅ Production bot updates!                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Two Development Workflows?

**Q: Why does the same workflow file create two different workflow runs?**

**A**: It's one file with two triggers:

```yaml
on:
  push:                          # ← Trigger 1: Deploy on push
    branches: [ develop, guess_feature, clerk_feature_dev ]
  pull_request:                  # ← Trigger 2: Test on PR
    branches: [ main ]
```

GitHub treats these as separate workflow runs because they serve different purposes:

1. **Push trigger**: "You pushed code to a dev branch, let's deploy it to the dev server"
2. **Pull request trigger**: "You want to merge to main, let's test it first"

---

## Workflow Secrets

Both workflows require these GitHub Secrets (configured in Repository Settings → Secrets):

### Required for Both:
- `GCP_SA_KEY`: Service account key for GitHub Actions to access GCP Compute Engine
- `GOOGLE_CREDENTIALS_DEV`: Base64-encoded Google Sheets credentials for development

### Required for Production:
- `GOOGLE_CREDENTIALS_PROD`: Base64-encoded Google Sheets credentials for production

---

## How to View Workflow Results

1. Go to your GitHub repository
2. Click the **Actions** tab
3. You'll see a list of workflow runs:
   - **Green checkmark** ✅ = Success
   - **Red X** ❌ = Failed
   - **Yellow circle** 🟡 = Running
4. Click on any run to see detailed logs

---

## Common Questions

### Q: Why did the workflow run twice after I pushed?

**A**: If you pushed to `guess_feature` AND have an open pull request to `main`, both workflows will run:
- One for the push (deploys to dev)
- One for the pull request (tests only)

### Q: Can I manually trigger a deployment?

**A**: Yes! The production workflow supports manual triggers:
1. Go to Actions tab
2. Select "Deploy to Production (GCP)"
3. Click "Run workflow" button

The development workflow doesn't support manual triggers (only push/PR).

### Q: What if the deployment fails?

**A**: The workflow will:
1. Show a red X ❌ in the Actions tab
2. Display detailed error logs
3. NOT restart the bot (old version keeps running)
4. Send you a notification email

### Q: How long does deployment take?

**A**: Typical deployment times:
- **Test stage**: 1-2 minutes (install dependencies, run tests)
- **Deploy stage**: 30-60 seconds (transfer files, restart service)
- **Total**: 2-3 minutes from push to bot restart

### Q: Can I skip the workflow?

**A**: Yes, add `[skip ci]` to your commit message:
```bash
git commit -m "Update README [skip ci]"
```

This is useful for documentation-only changes that don't need deployment.

---

## Troubleshooting

### Workflow fails with "Permission denied"
- **Cause**: `GCP_SA_KEY` secret is missing or invalid
- **Fix**: Re-run `scripts/create_gcp_sa_key.sh` and update the GitHub secret

### Workflow fails with "Unit discord-bot-dev.service not found"
- **Cause**: Systemd service not created on the server
- **Fix**: SSH into the server and run `bash scripts/setup_systemd_services.sh`

### Tests pass but deployment fails
- **Cause**: Service failed to start (check bot code errors)
- **Fix**: Check logs with `sudo journalctl -u discord-bot-dev.service -n 50`

### Workflow doesn't trigger at all
- **Cause**: Pushed to wrong branch or workflow file has syntax error
- **Fix**: Verify branch name matches trigger configuration

---

## Best Practices

1. **Always push to development branches first** (`guess_feature`, not `main`)
2. **Test the bot on dev server** before creating a pull request
3. **Create pull requests** to get automatic test validation
4. **Only merge to main** when dev testing is complete
5. **Monitor the Actions tab** for deployment status
6. **Check bot logs** after deployment to verify startup

---

## Summary

- **Push to dev branch** → Deploys to dev server automatically
- **Create PR to main** → Runs tests only (no deployment)
- **Merge to main** → Deploys to production server automatically
- All workflows run automatically, no manual intervention needed
- View results in the **Actions** tab on GitHub
