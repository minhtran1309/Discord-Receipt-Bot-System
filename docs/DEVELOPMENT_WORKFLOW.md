# Development Workflow

> **Last Updated:** 2026-03-18

This document describes the Git branching strategy, CI/CD pipeline, and development workflow for the Discord Receipt Bot System.

---

## Branch Structure

```
main (production-ready, stable)
 └── develop (integration branch, deployed to GCP dev)
      ├── feature/receipt-export
      ├── feature/multi-currency
      └── feature/...
```

| Branch | Purpose | Deploys To |
|--------|---------|-----------|
| `main` | Production-ready code | ~~Production~~ (currently disabled) |
| `develop` | Integration & testing | GCP Development server |
| `feature/*` | Individual feature work | GCP Development server |

---

## Feature Development Workflow

### Step 1: Create a GitHub Issue

**Option A: Via GitHub Web UI**

1. Go to **GitHub → Issues → New Issue**
2. Use a clear, descriptive title (e.g., "Add receipt export to CSV")
3. Include:
   - **What**: Description of the feature
   - **Why**: Business reason or user need
   - **Acceptance Criteria**: What "done" looks like
4. Assign labels (e.g., `enhancement`, `bug`, `refactor`)
5. Assign yourself

**Option B: Via GitHub CLI (`gh`)**

```bash
# Create an issue interactively
gh issue create

# Create an issue with all details inline
gh issue create \
  --title "Add receipt export to CSV" \
  --body "**What:** Export receipts as CSV files
**Why:** Users need to import data into Excel
**Acceptance Criteria:** /receipt export command generates a downloadable CSV" \
  --label "enhancement" \
  --assignee "@me"

# List open issues
gh issue list

# View a specific issue
gh issue view 42
```

> **Tip:** Install GitHub CLI with `brew install gh` and authenticate with `gh auth login`.

### Step 2: Create a Feature Branch

Always branch from `develop`:

```bash
# Make sure develop is up to date
git checkout develop
git pull origin develop

# Create feature branch (use issue number for traceability)
git checkout -b feature/short-description
# Examples:
#   feature/receipt-export
#   feature/42-multi-currency-support
#   fix/ocr-timeout-handling
```

### Step 3: Create a Context File

Create a context file for the AI assistant to track progress:

```bash
cp .claude/context/_TEMPLATE.md .claude/context/feature_short-description.md
```

Edit the file with your feature details. See `.claude/PROMPTS.md` for session prompts.

### Step 4: Develop & Push

```bash
# Work on your feature...
git add .
git commit -m "feat: add receipt export functionality (#42)"

# Push to trigger CI/CD (auto-deploys to dev server)
git push origin feature/short-description
```

**Commit message conventions:**
- `feat:` — New feature
- `fix:` — Bug fix
- `refactor:` — Code restructuring
- `docs:` — Documentation changes
- `test:` — Test additions/changes
- Include issue number: `(#42)`

### Step 5: Create a Pull Request to `develop`

1. Go to **GitHub → Pull Requests → New Pull Request**
2. Set **base**: `develop` ← **compare**: `feature/short-description`
3. Title: `feat: Add receipt export (#42)`
4. Description: Reference the issue with `Closes #42` or `Fixes #42`
5. Request a review (if working with others)
6. Ensure CI tests pass

### Step 6: Merge to `develop`

After PR approval:
1. **Squash and merge** (recommended) or **Merge commit**
2. Delete the feature branch on GitHub
3. Delete local feature branch:
   ```bash
   git checkout develop
   git pull origin develop
   git branch -d feature/short-description
   ```
4. Delete the context file for the feature branch

### Step 7: Test on Development Server

The merge to `develop` triggers auto-deployment to the GCP dev server.

1. Test your feature on the dev Discord bot
2. Monitor logs: `sudo journalctl -u discord-bot-dev.service -f`
3. Verify it works well with other components

### Step 8: Merge to `main` (Release)

Once `develop` is stable and tested:

1. Create a PR: **base**: `main` ← **compare**: `develop`
2. Title: `Release: [version or description]`
3. List all features/fixes being released
4. Merge after review
5. Update and close related GitHub Issues

---

## CI/CD Pipeline

### Development Deployment

**Trigger:** Push to `develop` or `feature/*` branches

```
Push to feature/* or develop
    → GitHub Actions: Run tests
    → Deploy to GCP dev server
    → Restart discord-bot-dev.service
```

- Tests are non-blocking (failures logged but deployment continues)
- PRs to `develop` run tests only (no deployment)

### Production Deployment

> ⚠️ **Currently disabled** (as of 2026-03-18). Production deployment workflow is commented out in `.github/workflows/deploy-production.yml`.

When re-enabled, merges to `main` will auto-deploy to the GCP production server with strict test requirements.

---

## Quick Reference

```bash
# Start new feature
git checkout develop && git pull origin develop
git checkout -b feature/my-feature

# Save progress
git add . && git commit -m "feat: description (#issue)"
git push origin feature/my-feature

# After PR merged to develop
git checkout develop && git pull origin develop
git branch -d feature/my-feature

# Release to main
# Create PR: develop → main on GitHub
```

---

## Branch Naming Convention

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New functionality | `feature/receipt-export` |
| `fix/` | Bug fixes | `fix/ocr-timeout` |
| `refactor/` | Code improvements | `refactor/sheets-service` |
| `docs/` | Documentation | `docs/api-reference` |

> **Tip:** Include the issue number for traceability: `feature/42-receipt-export`
