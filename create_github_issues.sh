#!/bin/bash

# Discord Receipt Bot - GitHub Issues Creation Script
# Run this after authenticating with: gh auth login

set -e  # Exit on error

echo "=========================================="
echo "Creating GitHub Milestones and Issues"
echo "=========================================="
echo ""

# Repository
REPO="minhtran1309/Discord-Receipt-Bot-System"

# Check if authenticated
if ! gh auth status > /dev/null 2>&1; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "Please run: gh auth login"
    exit 1
fi

echo "✓ Authenticated with GitHub"
echo ""

# Create Milestones
echo "Creating Milestones..."
echo ""

gh api repos/$REPO/milestones \
    -f title="M1: Core Infrastructure" \
    -f description="Basic bot infrastructure and receipt processing" \
    -f state="open" 2>/dev/null || echo "  Milestone M1 may already exist"

gh api repos/$REPO/milestones \
    -f title="M2: Item Guessing" \
    -f description="AI-powered item name identification" \
    -f state="open" 2>/dev/null || echo "  Milestone M2 may already exist"

gh api repos/$REPO/milestones \
    -f title="M3: Clerk Bot" \
    -f description="Expense tracking and Google Sheets integration" \
    -f state="open" 2>/dev/null || echo "  Milestone M3 may already exist"

gh api repos/$REPO/milestones \
    -f title="M4: Integration" \
    -f description="Integration, testing, and deployment" \
    -f state="open" 2>/dev/null || echo "  Milestone M4 may already exist"

echo "✓ Milestones created"
echo ""

# Create Issues for remaining features
echo "Creating Issues..."
echo ""

# M1: Enhancement Issue
echo "1. Receipt Parsing Logic Enhancement..."
gh issue create \
  --repo $REPO \
  --title "Receipt Parsing Logic Enhancement" \
  --label "enhancement,parsing,priority: medium" \
  --milestone "M1: Core Infrastructure" \
  --body "## Description
Enhance receipt parsing to handle various receipt formats from different stores.

## Current State
Basic regex-based parsing exists in \`bot/cogs/receipt.py\`

## Tasks
- [ ] Support multiple date formats (MM/DD/YY, YYYY-MM-DD, DD-MM-YYYY)
- [ ] Handle multi-line item names
- [ ] Detect and parse tax, subtotal, discounts
- [ ] Add support for itemized receipts vs. summary receipts
- [ ] Test with receipts from: Walmart, Costco, Target, local stores

## Files
- \`bot/cogs/receipt.py\` - \`_parse_receipt()\` method

## Acceptance Criteria
- Can parse receipts from at least 5 different stores
- Correctly extracts items, prices, and totals
- Handles edge cases (multi-line items, special characters)"

# M2: Enhancement Issue
echo "2. User Correction Flow Enhancement..."
gh issue create \
  --repo $REPO \
  --title "User Correction Flow Enhancement" \
  --label "enhancement,ux,priority: medium" \
  --milestone "M2: Item Guessing" \
  --body "## Description
Improve user experience when correcting low-confidence item guesses.

## Current State
Basic \`/guess correct\` command exists but requires manual input

## Tasks
- [ ] Add interactive buttons for approve/reject after \`/guess process\`
- [ ] Show items needing review with action buttons
- [ ] Add modal forms for batch corrections
- [ ] Highlight low-confidence items in receipt display
- [ ] Add quick-correct suggestions

## Files
- \`bot/cogs/guess.py\`

## Acceptance Criteria
- Users can click buttons to approve/reject guesses
- Low-confidence items are clearly marked
- Correction process takes fewer steps"

# M3: Enhancement Issue
echo "3. Data Aggregation Functions Enhancement..."
gh issue create \
  --repo $REPO \
  --title "Data Aggregation Functions Enhancement" \
  --label "enhancement,data,priority: medium" \
  --milestone "M3: Clerk Bot" \
  --body "## Description
Add more sophisticated data aggregation and query capabilities.

## Current State
Basic queries exist in \`bot/cogs/clerk.py\`

## Tasks
- [ ] Add category-based spending analysis
- [ ] Implement store comparison features
- [ ] Add price trend tracking for common items
- [ ] Create weekly/monthly/yearly aggregations
- [ ] Add export to CSV feature
- [ ] Generate spending charts/graphs

## Files
- \`bot/cogs/clerk.py\`
- \`bot/storage.py\`

## Acceptance Criteria
- Users can query spending by category
- Can compare prices across stores
- Can export data to CSV"

# M4: New Feature Issues
echo "4. Full Pipeline Command..."
gh issue create \
  --repo $REPO \
  --title "Full Pipeline Command" \
  --label "feature,integration,priority: high" \
  --milestone "M4: Integration" \
  --body "## Description
Implement a single command that runs the complete pipeline: OCR → Guess → Verify → Sync

## Tasks
- [ ] Create \`/process_full\` command
- [ ] Handle image upload
- [ ] Run OCR via Mistral API
- [ ] Parse receipt data
- [ ] Run AI guessing on all items
- [ ] Show review interface for low-confidence items
- [ ] Mark as verified after user review
- [ ] Sync to Google Sheets
- [ ] Provide progress updates during processing

## Files to Create/Modify
- \`bot/cogs/pipeline.py\` (new)
- \`bot/main.py\` (add cog)

## Acceptance Criteria
- Single command processes receipt end-to-end
- User sees progress updates
- Can review and correct items before sync
- Data appears in Google Sheets"

echo "5. Error Handling Improvements..."
gh issue create \
  --repo $REPO \
  --title "Error Handling Improvements" \
  --label "bug,quality,priority: medium" \
  --milestone "M4: Integration" \
  --body "## Description
Implement comprehensive error handling across all services.

## Current State
Basic try/catch blocks exist but error messages are generic

## Tasks
- [ ] Add detailed error messages for API failures
- [ ] Implement retry logic with exponential backoff
- [ ] Add rate limit handling for APIs
- [ ] Create user-friendly error messages
- [ ] Add error logging with context
- [ ] Handle network timeouts gracefully
- [ ] Add validation for user inputs

## Files
- All \`bot/services/*.py\`
- All \`bot/cogs/*.py\`

## Acceptance Criteria
- All API calls have retry logic
- Users see helpful error messages
- Errors are logged with context
- Bot doesn't crash on API failures"

echo "6. Response Formatting Enhancement..."
gh issue create \
  --repo $REPO \
  --title "Response Formatting Enhancement" \
  --label "enhancement,ux,priority: medium" \
  --milestone "M4: Integration" \
  --body "## Description
Improve Discord embed formatting and user feedback.

## Current State
Basic embeds exist but could be more polished

## Tasks
- [ ] Add color coding (green=success, yellow=warning, red=error)
- [ ] Include thumbnails and images in embeds
- [ ] Add progress indicators for long operations
- [ ] Use emoji for better visual feedback
- [ ] Implement pagination for long lists
- [ ] Add confirmation dialogs for destructive actions
- [ ] Create help command with examples

## Files
- All \`bot/cogs/*.py\`

## Acceptance Criteria
- Embeds use consistent color scheme
- Long lists are paginated
- Users get confirmation before deletions
- Help command shows usage examples"

echo "7. Documentation Update..."
gh issue create \
  --repo $REPO \
  --title "Documentation Update" \
  --label "documentation,priority: medium" \
  --milestone "M4: Integration" \
  --body "## Description
Complete documentation for users and developers.

## Current State
- ✅ README.md exists
- ✅ CLAUDE.md exists
- ✅ DISCORD_SETUP.md exists

## Tasks
- [ ] Add API documentation with examples
- [ ] Create user guide with screenshots
- [ ] Add troubleshooting section
- [ ] Document deployment options (Docker, systemd, cloud)
- [ ] Add contribution guidelines
- [ ] Create changelog
- [ ] Add code comments and docstrings
- [ ] Generate API reference docs

## Files to Create/Update
- \`docs/API.md\`
- \`docs/USER_GUIDE.md\`
- \`docs/DEPLOYMENT.md\`
- \`docs/CONTRIBUTING.md\`
- \`CHANGELOG.md\`

## Acceptance Criteria
- New users can set up bot from docs alone
- All commands documented with examples
- Deployment guides for 3+ platforms"

echo "8. Deployment Setup..."
gh issue create \
  --repo $REPO \
  --title "Deployment Setup" \
  --label "infrastructure,priority: high" \
  --milestone "M4: Integration" \
  --body "## Description
Set up deployment configurations for various platforms.

## Tasks
- [ ] Create Dockerfile for containerized deployment
- [ ] Add docker-compose.yml for easy local setup
- [ ] Create systemd service file
- [ ] Add Railway/Render deployment config
- [ ] Create Heroku Procfile
- [ ] Add environment variable templates for each platform
- [ ] Document deployment process for each option
- [ ] Add health check endpoint

## Files to Create
- \`Dockerfile\`
- \`docker-compose.yml\`
- \`receipt-bot.service\` (systemd)
- \`railway.json\`
- \`Procfile\`
- \`docs/DEPLOYMENT.md\`

## Acceptance Criteria
- Bot can be deployed via Docker in <5 minutes
- Deployment guides for 3+ platforms
- All configs tested and working"

echo "9. Comprehensive Testing..."
gh issue create \
  --repo $REPO \
  --title "Comprehensive Testing" \
  --label "testing,priority: medium" \
  --milestone "M4: Integration" \
  --body "## Description
Implement comprehensive test suite.

## Current State
Basic test files exist but minimal coverage

## Tasks
- [ ] Add unit tests for all services
- [ ] Add integration tests for workflows
- [ ] Mock external API calls (Mistral, OpenRouter, Google Sheets)
- [ ] Test error scenarios
- [ ] Add fixtures for test data
- [ ] Set up CI/CD with GitHub Actions
- [ ] Add code coverage reporting
- [ ] Test Discord command interactions

## Files
- Expand \`tests/test_*.py\`
- Create \`tests/fixtures/*.json\`
- Create \`.github/workflows/test.yml\`
- Add \`conftest.py\`

## Acceptance Criteria
- Test coverage >80%
- CI/CD pipeline runs on all PRs
- All external APIs mocked in tests
- Integration tests for main workflows"

echo ""
echo "=========================================="
echo "✓ All issues created successfully!"
echo "=========================================="
echo ""
echo "View issues at:"
echo "https://github.com/$REPO/issues"
echo ""
echo "Next steps:"
echo "1. Review issues and milestones"
echo "2. Pick an issue to work on"
echo "3. Create a feature branch"
echo "4. Submit a PR when done"
