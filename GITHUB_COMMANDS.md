# GitHub CLI Commands Reference

This file contains all the GitHub CLI commands used to set up the project.

## Authentication

```bash
# Login to GitHub CLI
gh auth login

# Check authentication status
gh auth status
```

## Create Labels

```bash
# Enhancement label
gh label create "enhancement" \
  --color "a2eeef" \
  --description "New feature or request" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Parsing label
gh label create "parsing" \
  --color "d4c5f9" \
  --description "Related to parsing logic" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Priority: High
gh label create "priority: high" \
  --color "d93f0b" \
  --description "High priority" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Priority: Medium
gh label create "priority: medium" \
  --color "fbca04" \
  --description "Medium priority" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# UX label
gh label create "ux" \
  --color "c5def5" \
  --description "User experience" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Data label
gh label create "data" \
  --color "bfdadc" \
  --description "Data related" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Feature label
gh label create "feature" \
  --color "84b6eb" \
  --description "New feature" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Integration label
gh label create "integration" \
  --color "5319e7" \
  --description "Integration work" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Quality label
gh label create "quality" \
  --color "e99695" \
  --description "Code quality improvement" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Infrastructure label
gh label create "infrastructure" \
  --color "1d76db" \
  --description "Infrastructure and deployment" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Testing label
gh label create "testing" \
  --color "c2e0c6" \
  --description "Testing related" \
  --repo minhtran1309/Discord-Receipt-Bot-System
```

## Create Milestones

```bash
# M1: Core Infrastructure
gh api repos/minhtran1309/Discord-Receipt-Bot-System/milestones \
  -f title="M1: Core Infrastructure" \
  -f description="Basic bot infrastructure and receipt processing" \
  -f state="open"

# M2: Item Guessing
gh api repos/minhtran1309/Discord-Receipt-Bot-System/milestones \
  -f title="M2: Item Guessing" \
  -f description="AI-powered item name identification" \
  -f state="open"

# M3: Clerk Bot
gh api repos/minhtran1309/Discord-Receipt-Bot-System/milestones \
  -f title="M3: Clerk Bot" \
  -f description="Expense tracking and Google Sheets integration" \
  -f state="open"

# M4: Integration
gh api repos/minhtran1309/Discord-Receipt-Bot-System/milestones \
  -f title="M4: Integration" \
  -f description="Integration, testing, and deployment" \
  -f state="open"
```

## View Project Status

```bash
# List all milestones
gh api repos/minhtran1309/Discord-Receipt-Bot-System/milestones

# List all issues
gh issue list --repo minhtran1309/Discord-Receipt-Bot-System

# List issues by milestone
gh issue list --milestone "M1: Core Infrastructure" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# View specific issue
gh issue view 5 --repo minhtran1309/Discord-Receipt-Bot-System

# List all labels
gh label list --repo minhtran1309/Discord-Receipt-Bot-System
```

## Working with Issues

```bash
# Create a new issue
gh issue create \
  --repo minhtran1309/Discord-Receipt-Bot-System \
  --title "Issue Title" \
  --body "Issue description" \
  --label "feature,priority: high" \
  --milestone "M4: Integration"

# Close an issue
gh issue close 1 --repo minhtran1309/Discord-Receipt-Bot-System

# Reopen an issue
gh issue reopen 1 --repo minhtran1309/Discord-Receipt-Bot-System

# Add labels to an issue
gh issue edit 1 --add-label "bug" \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Assign issue to yourself
gh issue edit 1 --add-assignee @me \
  --repo minhtran1309/Discord-Receipt-Bot-System
```

## Working with Pull Requests

```bash
# Create a PR from current branch
gh pr create \
  --title "Feature: Add full pipeline command" \
  --body "Implements issue #5" \
  --base main \
  --head feature/full-pipeline

# List all PRs
gh pr list --repo minhtran1309/Discord-Receipt-Bot-System

# View PR details
gh pr view 1 --repo minhtran1309/Discord-Receipt-Bot-System

# Merge a PR
gh pr merge 1 --squash --delete-branch \
  --repo minhtran1309/Discord-Receipt-Bot-System

# Check out a PR locally
gh pr checkout 1
```

## Project Workflow

```bash
# 1. Pick an issue
gh issue list --repo minhtran1309/Discord-Receipt-Bot-System

# 2. Create a feature branch
git checkout -b feature/issue-5-full-pipeline

# 3. Make changes and commit
git add .
git commit -m "Add full pipeline command

Closes #5"

# 4. Push branch
git push -u origin feature/issue-5-full-pipeline

# 5. Create PR
gh pr create --fill

# 6. After review and merge, delete local branch
git checkout main
git pull
git branch -d feature/issue-5-full-pipeline
```

## Useful Shortcuts

```bash
# View project in browser
gh repo view minhtran1309/Discord-Receipt-Bot-System --web

# View issues in browser
gh issue view 5 --web

# View PR in browser
gh pr view 1 --web

# Clone repository
gh repo clone minhtran1309/Discord-Receipt-Bot-System

# Fork repository
gh repo fork minhtran1309/Discord-Receipt-Bot-System
```

## Issue Templates

### Create a Bug Report Issue
```bash
gh issue create \
  --title "Bug: Command fails with error" \
  --body "## Description
Error occurs when...

## Steps to Reproduce
1. Run \`/receipt process\`
2. Upload image
3. See error

## Expected Behavior
Should process receipt

## Actual Behavior
Throws exception

## Environment
- OS: macOS
- Python: 3.11
- discord.py: 2.6.4

## Error Message
\`\`\`
Error text here
\`\`\`" \
  --label "bug,priority: high"
```

### Create a Feature Request Issue
```bash
gh issue create \
  --title "Feature: Add receipt categories" \
  --body "## Description
Add ability to categorize receipts

## Use Case
Users want to track groceries vs household items

## Proposed Solution
- Add category field to Receipt model
- Add /category command
- Filter by category in reports

## Alternatives
Could use tags instead" \
  --label "feature,enhancement" \
  --milestone "M4: Integration"
```

## GitHub Actions (Future)

```bash
# View workflow runs
gh run list --repo minhtran1309/Discord-Receipt-Bot-System

# View specific run
gh run view 123456

# Re-run failed workflow
gh run rerun 123456

# Watch a workflow run
gh run watch
```

## Tips & Tricks

```bash
# Set default repository (run in project directory)
gh repo set-default minhtran1309/Discord-Receipt-Bot-System

# After setting default, commands become shorter:
gh issue list
gh pr list
gh issue create

# Use aliases
gh alias set issues 'issue list --label "priority: high"'
gh issues

# View help for any command
gh issue --help
gh pr create --help
```

## Cleanup Commands

```bash
# Delete a label
gh label delete "old-label" --yes

# Close all issues with specific label
gh issue list --label "wontfix" --json number --jq '.[].number' | \
  xargs -I {} gh issue close {}

# Delete a milestone (via API)
gh api repos/minhtran1309/Discord-Receipt-Bot-System/milestones/1 -X DELETE
```

## Project Statistics

```bash
# Count open issues
gh issue list --state open --json number --jq '. | length'

# Count issues by label
gh issue list --label "bug" --json number --jq '. | length'

# List contributors
gh api repos/minhtran1309/Discord-Receipt-Bot-System/contributors

# View repository stats
gh repo view minhtran1309/Discord-Receipt-Bot-System
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `gh auth login` | Authenticate with GitHub |
| `gh issue list` | List all issues |
| `gh issue create` | Create a new issue |
| `gh issue view N` | View issue details |
| `gh issue close N` | Close an issue |
| `gh pr create` | Create a pull request |
| `gh pr list` | List all PRs |
| `gh pr merge N` | Merge a PR |
| `gh repo view --web` | Open repo in browser |
| `gh label list` | List all labels |
| `gh milestone list` | List milestones (via API) |

---

## Links

- **Repository**: https://github.com/minhtran1309/Discord-Receipt-Bot-System
- **Issues**: https://github.com/minhtran1309/Discord-Receipt-Bot-System/issues
- **Milestones**: https://github.com/minhtran1309/Discord-Receipt-Bot-System/milestones
- **GitHub CLI Docs**: https://cli.github.com/manual/
