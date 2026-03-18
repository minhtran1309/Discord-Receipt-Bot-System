# Branch Context: main (Branch Oversight Hub)

## Feature Summary
Main production branch for the Discord Receipt Bot System. This file serves as the **branch oversight hub** — tracking all active feature branches, their status, and development phase goals.

## Branching Strategy

```
main (production-ready, stable)
 └── develop (integration & testing, deploys to GCP dev)
      └── feature/* (individual features)
```

**Workflow:** `feature/* → develop → main`

See [DEVELOPMENT_WORKFLOW.md](file:///Users/minhtran/Git_Packages/Discord-Receipt-Bot-System/docs/DEVELOPMENT_WORKFLOW.md) for detailed instructions.

## Current Development Phase
**Phase**: New Development Phase (started 2026-03-18)
**Status**: Clean slate — Git Flow established with `develop` branch.

### Previous Phase Summary (Completed 2026-03-18)
All previous feature branches cleaned up:
- ✅ `guess_feature` → Merged via PR #27
- ✅ `installation_feature` → Merged via PR #26
- ✅ `clerk_feature_dev` → Merged via PR #28, remaining work archived
- ✅ `feature/complete-bot-with-improvements` → Fully merged
- 🗑️ `gcp_auto_deploy_feature`, `receipt_list_feature`, `total_expense_feature` → Archived

## Active Feature Branches

| Branch | Feature | Issue | Status | Created |
|--------|---------|-------|--------|---------|
| *No active branches* | — | — | — | — |

> Update this table when creating new feature branches.

## CI/CD Configuration

| Trigger | Action |
|---------|--------|
| Push to `feature/*` | Tests + deploy to GCP dev |
| Push to `develop` | Tests + deploy to GCP dev |
| PR to `develop` | Tests only (no deploy) |
| Push to `main` | ~~Production deploy~~ **DISABLED** |

## Branch Workflow Rules

### Creating a New Feature Branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/descriptive-name
cp .claude/context/_TEMPLATE.md .claude/context/feature_descriptive-name.md
```

### Merge Checklist
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Code formatted (`black bot/ tests/` + `isort bot/ tests/`)
- [ ] PR reviewed and approved
- [ ] Context file updated with final status
- [ ] After merge to develop: delete feature branch + context file
- [ ] After merge to main: close GitHub Issue

## Architecture Decisions Log

### 2026-03-18: Git Flow Branching Strategy
**Decision:** Adopt `feature/* → develop → main` workflow with GitHub Issues
**Reasoning:** Clean separation between development and production. Features tested on develop before reaching main.

### 2026-03-18: Production Deployment Disabled
**Decision:** Comment out production deploy workflow until further notice
**Reasoning:** Starting new development phase; production stays stable while new features are built and tested on develop.

## Session Log

### 2026-03-18
**Done:** Branch cleanup, created `develop` branch, set up Git Flow, updated CI/CD workflows, created DEVELOPMENT_WORKFLOW.md
**Next:** Begin feature development using the new workflow
**Note:** WIP changes stashed as "WIP changes before branch cleanup"

---
*Branch created: 2025-12-31*
*Last updated: 2026-03-18*
