# CLAUDE.md - Discord Receipt Bot System

## Project Overview

**Name**: Discord-Receipt-Bot-System

**Purpose**: A Discord bot for processing grocery receipts, identifying items using AI, and tracking expenses in Google Sheets.

**Status**: Active production deployment with CI/CD pipeline

**Repository**: https://github.com/minhtran1309/Discord-Receipt-Bot-System

**Tech Stack**: Python 3.11+, discord.py 2.x, Mistral OCR, OpenRouter AI, Google Sheets API

> **IMPORTANT INSTRUCTIONS FOR CLAUDE:**
> 1. At START of session → read `.claude/context/[current-branch].md`
> 2. BEFORE `/compact` → update the context file first
> 3. AFTER `/compact` → re-read the context file

## Features

- **Receipt Processing**: Upload receipt images and extract structured data via OCR (Mistral API + OpenRouter AI)
- **AI-Powered Extraction**: Automatically categorizes items and handles multi-language receipts
- **Purchase Analytics**: View store purchases by month/year with spending breakdowns
- **Expense Tracking**: Syncs data to Google Sheets for easy tracking with dual-sync system (prevents duplicates)
- **Budget Management**: Track eating out expenses with $100/month budget, surplus rolls to holiday fund
- **Monthly Expense Aggregation**: Auto-generates Excel formulas in Google Sheets for category totals
- **Spending Queries**: Ask the bot about your spending habits
- **Smart Alerts**: Get reminded about budget overspending when verifying grocery receipts

## Project Structure

```
receipt-bot/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration (Pydantic settings)
│   ├── cogs/                # Discord command modules
│   │   ├── receipt.py       # Receipt processing commands
│   │   └── clerk.py         # Expense tracking & budget commands
│   ├── services/            # API integrations
│   │   ├── ocr.py           # Mistral OCR service (with Qwen fallback)
│   │   ├── ai_extractor.py  # AI-powered data extraction (OpenRouter)
│   │   └── sheets.py        # Google Sheets integration (multi-tab support)
│   ├── models.py            # Data models (Receipt, ReceiptItem, BudgetEntry, etc.)
│   ├── storage.py           # Receipt file operations
│   └── budget_storage.py    # Budget data persistence
├── data/
│   ├── receipts/            # Processed receipts (JSON)
│   ├── budgets/             # Budget entries by month (JSON)
│   ├── items/               # Extracted items (TSV)
│   ├── ocr_cache/           # Cached OCR results
│   └── corrections.json     # Item name corrections
├── docs/
│   ├── INSTALLATION.md      # Installation guide (interactive script + manual)
│   ├── GOOGLE_SHEETS_SETUP.md  # Google Sheets & service account setup
│   ├── DEPLOYMENT.md        # GCP deployment & CI/CD pipeline
│   ├── GITHUB_ACTIONS_EXPLAINED.md  # Workflow explanation
│   ├── DATA_DIRECTORY_FIX.md  # Troubleshooting data directory issues
│   └── others...
├── scripts/
│   ├── deploy.sh            # GCP deployment script
│   ├── setup_systemd_services.sh  # Systemd service setup
│   ├── start_local_bot.sh   # Start local bot (stops GCP dev bot)
│   └── stop_local_bot.sh    # Stop local bot (restarts GCP dev bot)
├── tests/
├── .env.example             # Environment variable template
├── .env.production          # Production config (GCP)
├── .env.development         # Development config (GCP)
├── environment.yml          # Conda environment specification
├── requirements.txt         # Python dependencies
├── install.sh               # Interactive installation script
├── README.md                # Main documentation
└── CLAUDE.md                # This file
```

## Tech Stack

### Core Framework
- **Python 3.11+**: Required for latest async features and type hints
- **discord.py 2.x**: Discord bot framework with app_commands (slash commands)
- **Pydantic 2.x**: Data validation and settings management
- **httpx**: Async HTTP client for API calls

### AI & OCR Services
- **Mistral OCR API**: Receipt image text extraction
  - Model: `mistral-ocr-latest`
  - Fallback: OpenRouter `qwen/qwen3-vl-30b-a3b-instruct` (for 429 rate limits)
- **OpenRouter AI**: Structured data extraction
  - Model: `openai/gpt-4o-mini` (~$0.0003 per receipt)
  - 100% success rate on multi-language receipts

### Data Storage
- **Google Sheets API**: Expense tracking and aggregation
  - gspread + google-auth
  - Multi-sheet architecture (Sheet1, receipt_total, total_cost_monthly, expense sheets)
- **Local JSON**: Receipt storage with sync tracking
- **TSV files**: Item export for analysis

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking
- **conda**: Environment management (production)

## Discord Commands

### Receipt Processing (`/receipt`)

| Command | Description | Parameters |
|---------|-------------|------------|
| `/receipt process` | Upload and process a receipt image | `image: Attachment` |
| `/receipt list` | List all processed receipts | None |
| `/receipt show` | Display receipt in TOON format | `filename: str` |
| `/receipt verify` | Mark receipt as verified (includes budget alert) | `filename: str` |
| `/receipt delete` | Delete a receipt | `filename: str` |
| `/receipt correct_name` | Correct item name | `filename, item_index, new_name` |
| `/receipt correct_price` | Correct item price | `filename, item_index, new_price` |
| `/receipt correct_category` | Correct item category | `filename, item_index, new_category` |
| `/receipt view_store` | View store purchases by month/year with analytics | `store, period (YYYY-MM or YYYY)` |

### Expense Tracking & Budget (`/clerk`)

| Command | Description | Parameters |
|---------|-------------|------------|
| `/clerk sync` | Sync verified receipts to Google Sheets (3-step process) | None |
| `/clerk status` | Check sync status of all receipts | None |
| `/clerk spent` | Query spending on a product | `product, month (optional)` |
| `/clerk monthly` | Get monthly expense summary | `month (YYYY-MM, optional)` |
| `/clerk report` | Generate expense report | `start_date, end_date (YYYY-MM-DD)` |
| `/clerk special_treat` | Log eating out expense (tracks $100/month budget) | `amount` |
| `/clerk budget_status` | Check eating out budget status | `month (YYYY-MM, optional)` |
| `/clerk personal` | Log personal expense | `amount, description` |
| `/clerk utilities` | Log utilities expense | `amount, description` |
| `/clerk transport` | Log transport expense | `amount, description` |
| `/clerk extraordinary` | Log extraordinary expense | `amount, description` |

### Utility

| Command | Description |
|---------|-------------|
| `/ping` | Check bot status |

## Configuration

### Environment Variables

Required in `.env` file:

```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_server_id  # Optional: for faster command sync during dev

# Mistral OCR
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_OCR_MODEL=mistral-ocr-latest
FALLBACK_OCR_MODEL=qwen/qwen3-vl-30b-a3b-instruct

# OpenRouter (for AI extraction and guessing)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini

# Google Sheets
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SPREADSHEET_ID=your_google_spreadsheet_id

# Application Settings
CONFIDENCE_THRESHOLD=0.7  # AI confidence threshold
DATA_DIR=data  # Relative path (relative to WorkingDirectory)
LOG_LEVEL=INFO
BOT_NAME=Receipt Bot (Local)  # Bot instance identifier for tracking
```

### Multi-Environment Setup

The project supports three separate environments with distinct Discord bot applications:

1. **Local Development**:
   - Bot: "Receipt Bot (Local)"
   - Config: `.env` (local)
   - Purpose: Local testing on your machine

2. **GCP Development**:
   - Bot: "Receipt Bot (Dev)"
   - Config: `.env.development` (GCP server)
   - Service: `discord-bot-dev.service`
   - Deployment: Auto-deploys on push to `guess_feature` or `clerk_feature_dev` branches

3. **GCP Production**:
   - Bot: "Receipt Bot (Production)"
   - Config: `.env.production` (GCP server)
   - Service: `discord-bot.service`
   - Deployment: Auto-deploys on merge to `main` branch

**Important**: Do not use inline comments in `.env` files (Pydantic parsing issue).

## Key Architecture Decisions

### 1. AI-Powered Extraction (100% Success Rate)

**Two-step approach**:
1. **Mistral OCR** → Extracts raw markdown text from receipt images
2. **AI Extractor** → Parses OCR text into structured data using OpenRouter

**Capabilities**:
- Multi-line item name combination
- Multi-language support (Chinese, Korean, etc.)
- Unit extraction (kg, g, L, ml) separated from item names
- Automatic categorization (Produce, Meat, Dairy, Bakery, etc.)
- Discount handling (free promotional items supported)

**Cost**: ~$0.0003 per receipt (negligible)

### 2. Three-Sheet Google Sheets Architecture

**Sheet 1: `Sheet1`** (Individual Items)
- Structure: `[Date, Store, Item, Qty, Unit, Price, Category, SKU, Signature]`
- Purpose: Detailed item-level tracking

**Sheet 2: `receipt_total`** (Receipt Totals)
- Structure: `[receipt_file_name, total_price, submitted_by, sync_status]`
- Purpose: Receipt-level totals for formula references

**Sheet 3: `total_cost_monthly`** (Monthly Aggregation)
- Structure: `[Category, 2026-01, 2026-02, ...]` (categories as rows, months as columns)
- Purpose: Auto-generated formulas for monthly category totals
- Formula format: `=receipt_total!B2+receipt_total!B3+...` (additive, not SUM)

**Expense Sheets**: `personal`, `utilities`, `transport`, `extraordinary`, `eat_out_2026`
- Structure: `[Date, Time, Amount, Category, Month, submitted_by]`
- Purpose: Track non-receipt expenses

### 3. Additive Formula Generation

**Strategy**: Dynamic formula building using cell references

**Example**:
```
Shopping expenses for 2026-01:
=receipt_total!B2+receipt_total!B3+receipt_total!B5

Personal expenses for 2026-01:
=personal!C2+personal!C4+personal!C7
```

**Formula Management Methods** (`bot/services/sheets.py`):
- `parse_formula()`: Extract cell references from formula
- `append_to_formula()`: Append new cell reference
- `build_formula()`: Build formula from cell references
- `rebuild_formula_from_sheet()`: Read from Google Sheets (source of truth) and rebuild complete formula
- `find_or_create_category_row()`: Auto-create category rows
- `find_or_create_month_column()`: Auto-create month columns
- `update_formula_cell()`: Update formula by appending reference
- `sync_receipt_totals()`: Sync totals to receipt_total sheet
- `update_shopping_expenses_formulas()`: Update formulas in total_cost_monthly

### 4. Google Sheets as Source of Truth

**Philosophy**: Bot reads from Google Sheets to rebuild formulas, ensuring formulas include ALL data regardless of source (bot, manual entry, other integrations).

**Implementation**: `rebuild_formula_from_sheet()` method reads all rows for a specific month and generates complete formula from scratch.

### 5. Dual-Sync System (Prevents Duplicates)

**Problem**: Running `/clerk sync` multiple times would create duplicate entries in Google Sheets.

**Solution**: Local sync tracking using `synced_to_sheets` boolean field in receipt JSON files.

**Workflow**:
1. Filter receipts where `verified=True` AND `synced_to_sheets=False`
2. Sync only unsynced receipts to Google Sheets
3. Mark receipts as `synced_to_sheets=True` after successful sync
4. Show detailed statistics (newly synced, already synced, total verified)

**Benefits**:
- ✅ Prevents duplicate data
- ✅ Fast and efficient (no extra API calls)
- ✅ Clear visibility with `/clerk status` command
- ✅ Incremental syncing (only new verified receipts)
- ✅ Works offline for status checking

### 6. OCR Caching

**Purpose**: Avoid redundant API calls for the same receipt image

**Implementation**: Store OCR results in `data/ocr_cache/{filename}_ocr.txt`

**Benefits**:
- Faster re-processing
- Cost savings on API calls
- Offline testing capability

### 7. Bot Signature Column

**Purpose**: Track which bot instance synced each row in Google Sheets

**Configuration**: Set via `BOT_NAME` environment variable

**Use Cases**:
- Debugging in multi-environment setups
- Auditing data sources (local/dev/prod)
- Identifying which bot submitted data

## Installation

### Quick Installation (Interactive Script)

**Recommended for new users**:

```bash
./install.sh
```

The script will:
1. Check for Conda/Miniconda (offers to install if missing)
2. Check for Python 3.11+ installation
3. Set up virtual environment (Conda or venv)
4. Install all dependencies
5. Prompt for API keys and configuration
6. Create `.env` file
7. Set up data directory structure
8. Optionally test configuration
9. Create `start.sh` script for easy bot launching

### Manual Installation

**Prerequisites**:
- Python 3.11+
- pip (Python package installer)
- Git

**Steps**:

```bash
# 1. Clone repository
git clone https://github.com/minhtran1309/Discord-Receipt-Bot-System.git
cd Discord-Receipt-Bot-System

# 2. Create virtual environment
python3 -m venv discord_env
source discord_env/bin/activate  # On Windows: discord_env\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Set up Google Sheets (see Google Sheets Setup section)

# 6. Create data directories
mkdir -p data/receipts data/items data/budgets data/ocr_cache
echo "{}" > data/corrections.json

# 7. Run the bot
python -m bot.main
```

## Google Sheets Setup

### Part 1: Google Cloud Setup

**Step 1: Create Google Cloud Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: `receipt-bot`
3. Enable Google Sheets API
4. Create service account: `receipt-bot-service`
5. Download service account JSON credentials

**Step 2: Move Credentials**
```bash
mv ~/Downloads/receipt-bot-*.json credentials.json
# Move to project root
```

### Part 2: Google Sheets Setup

**Step 1: Create Spreadsheet**
1. Create new Google Sheet: "Receipt Bot - Expenses"
2. Add header row: `[Date, Store, Item, Quantity, Unit, Price, Category, SKU, Signature]`

**Step 2: Share with Service Account (CRITICAL)**
1. Click "Share" button
2. Paste service account email (from `credentials.json` → `client_email`)
3. Set permission to "Editor"
4. Uncheck "Notify people"
5. Click "Share"

**Step 3: Get Spreadsheet ID**
- Copy from URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`

**Step 4: Update .env**
```bash
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
```

### Part 3: Multi-Sheet Setup

Create additional sheets for expense tracking and aggregation:

1. **receipt_total**: `[receipt_file_name, total_price, submitted_by, sync_status]`
2. **total_cost_monthly**: `[Category, 2026-01, 2026-02, ...]`
3. **personal**: `[Date, Time, Amount, Category, Month, submitted_by]`
4. **utilities**: `[Date, Time, Amount, Category, Month, submitted_by]`
5. **transport**: `[Date, Time, Amount, Category, Month, submitted_by]`
6. **extraordinary**: `[Date, Time, Amount, Category, Month, submitted_by]`
7. **eat_out_2026**: `[Date, Time, Amount, Category, Month]`

**See**: [docs/GOOGLE_SHEETS_SETUP.md](docs/GOOGLE_SHEETS_SETUP.md) for detailed step-by-step instructions.

## GCP Deployment

### Architecture

**GCP Project**: `GCP-discord-receipts-bot`
**Compute Instance**: `discord-bot-server` (australia-southeast1-a)
**Application Directory**: `/opt/discord-bot/app`
**Bot User**: `botuser`
**Environment Manager**: Conda (Miniconda)

### Deployment Strategy: Git-Based Deployment

**How it works**:
1. Repository cloned once on server at `/opt/discord-bot/app/`
2. Deployments use `git fetch` + `git reset --hard origin/<branch>`
3. Only transfers changed files (git deltas)
4. GitHub Actions sends deployment script via SCP

**Benefits**:
- **50-250x faster** than copying entire codebase
- **Atomic updates** - consistent state guaranteed
- **Easy rollbacks** - use git commit hashes
- **Bandwidth efficient** - typical deployment < 5MB

### Systemd Services

**Production Service**: `discord-bot.service`
- Config: `.env.production`
- Auto-starts on boot
- Restart policy: Always with 10s delay

**Development Service**: `discord-bot-dev.service`
- Config: `.env.development`
- Auto-starts on boot
- Used for feature branch testing

**Setup**:
```bash
# Run setup script
bash scripts/setup_systemd_services.sh

# Enable and start services
sudo systemctl enable discord-bot.service
sudo systemctl enable discord-bot-dev.service
sudo systemctl start discord-bot.service
sudo systemctl start discord-bot-dev.service
```

### CI/CD Pipeline (GitHub Actions)

**Workflow Files**:

1. **`.github/workflows/deploy-production.yml`** ⚠️ **DISABLED**
   - Production deployment is currently stalled (commented out since 2026-03-18)
   - Will be re-enabled when instructed

2. **`.github/workflows/deploy-development.yml`**
   - Trigger: Push to `develop` or `feature/**` branches
   - Steps:
     1. Run tests (failures allowed for dev)
     2. Deploy to GCP development server
     3. Install Google credentials (base64 decoded)
     4. Restart `discord-bot-dev.service`
   - Pull Request Mode: PRs to `develop` run tests only (no deployment)

**GitHub Secrets Required**:
- `GCP_SA_KEY`: Service account key for GitHub Actions to access GCP
- `GOOGLE_CREDENTIALS_DEV`: Base64-encoded Google Sheets credentials for dev
- `GOOGLE_CREDENTIALS_PROD`: Base64-encoded Google Sheets credentials for prod

**Deployment Flow**:
```
Push to feature/* → GitHub Actions → Test → Deploy to Dev → Restart discord-bot-dev.service
Merge to develop  → GitHub Actions → Test → Deploy to Dev → Restart discord-bot-dev.service
Merge to main     → No auto-deploy (production workflow disabled)
```

**See**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/DEVELOPMENT_WORKFLOW.md](docs/DEVELOPMENT_WORKFLOW.md), and [docs/GITHUB_ACTIONS_EXPLAINED.md](docs/GITHUB_ACTIONS_EXPLAINED.md) for complete setup.

## Development Workflow

### Common Commands

```bash
# Local Development
python -m bot.main                     # Run bot locally
source discord_env/bin/activate        # Activate venv
conda activate discord-bot             # Activate conda env

# Testing
pytest tests/ -v                       # Run tests
pytest tests/ -v --cov=bot            # Run tests with coverage

# Code Formatting
black bot/ tests/                      # Format code
isort bot/ tests/                      # Sort imports
mypy bot/                              # Type checking

# GCP Deployment (Manual)
bash scripts/deploy.sh production      # Deploy to production
bash scripts/deploy.sh development     # Deploy to development

# Service Management (GCP Server)
sudo systemctl status discord-bot.service           # Check production status
sudo systemctl status discord-bot-dev.service       # Check dev status
sudo journalctl -u discord-bot.service -f          # View production logs
sudo journalctl -u discord-bot-dev.service -f      # View dev logs
sudo systemctl restart discord-bot.service         # Restart production
sudo systemctl restart discord-bot-dev.service     # Restart dev

# Local/Dev Bot Switching
bash scripts/start_local_bot.sh        # Start local bot (stops GCP dev bot)
bash scripts/stop_local_bot.sh         # Stop local bot (restarts GCP dev bot)
```

### Typical Feature Development

```bash
# 1. Create GitHub Issue describing the feature

# 2. Create feature branch from develop
git checkout develop && git pull origin develop
git checkout -b feature/new-feature

# 3. Create context file for AI assistant
cp .claude/context/_TEMPLATE.md .claude/context/feature_new-feature.md

# 4. Develop locally
python -m bot.main

# 5. Push feature branch (auto-deploys to GCP dev)
git push origin feature/new-feature

# 6. Test on GCP dev server
# Monitor logs: sudo journalctl -u discord-bot-dev.service -f

# 7. Create PR: feature/* → develop
# GitHub Actions runs tests, merge after review

# 8. Test on develop (auto-deploys to GCP dev)
git checkout develop && git pull origin develop

# 9. Release: Create PR: develop → main
# Close related GitHub Issues after merge
```

**See**: [docs/DEVELOPMENT_WORKFLOW.md](docs/DEVELOPMENT_WORKFLOW.md) for detailed instructions.

## Data Models

### Receipt Model

```python
class Receipt(BaseModel):
    id: str                        # UUID
    filename: str                  # YYYY-MM-DD_HHMM_store.json
    store: str                     # Store name
    datetime: datetime             # Receipt date/time
    processed_at: datetime         # Processing timestamp
    verified: bool = False         # User verified?
    synced_to_sheets: bool = False # Synced to Google Sheets?
    raw_ocr_text: str             # Original OCR output
    items: list[ReceiptItem]      # List of items
    total: float                   # Total amount
    subtotal: float               # Subtotal before tax
    tax: float                    # Tax amount
    discount_total: float = 0.0   # Total discounts
    payment_method: str = "Card"  # Payment method
```

### ReceiptItem Model

```python
class ReceiptItem(BaseModel):
    raw_name: str                 # Original name from receipt
    quantity: int                 # Item quantity
    unit: str = "ea"             # Unit (ea, kg, g, L, ml, etc.)
    price: float                  # Item price (0.0 for free items)
    discount: float = 0.0        # Discount amount
    sku: str | None = None       # Stock keeping unit
    category: str                # Category (Produce, Meat, Dairy, etc.)
    guessed_name: str | None     # AI-guessed full name
    confidence: float = 1.0      # AI confidence (0.0-1.0)
    confirmed_name: str | None   # User-confirmed name
    needs_review: bool = False   # Flag for manual review
```

### BudgetEntry Model

```python
class BudgetEntry(BaseModel):
    id: str                      # UUID
    date: datetime              # Entry date
    amount: float               # Amount spent
    description: str = ""       # Optional description
    month: str                  # Month in YYYY-MM format
    created_at: datetime        # Timestamp
```

## API Integrations

### Mistral OCR API

**Purpose**: Extract raw markdown text from receipt images

**Endpoint**: https://api.mistral.ai/v1/ocr

**Model**: `mistral-ocr-latest`

**Fallback**: OpenRouter `qwen/qwen3-vl-30b-a3b-instruct` (for 429 rate limit errors)

**Input**: Base64-encoded image (JPEG, PNG, HEIC)

**Output**: Raw markdown text

**Service**: `bot/services/ocr.py`

### OpenRouter AI (Structured Extraction)

**Purpose**: Parse OCR text into structured receipt data

**Endpoint**: https://openrouter.ai/api/v1/chat/completions

**Model**: `openai/gpt-4o-mini` ($0.15/$0.60 per 1M tokens)

**Success Rate**: 100% (tested with 4/4 receipts)

**Capabilities**:
- Multi-line item combination
- Multi-language support
- Unit extraction
- Category classification
- Discount handling
- Metadata extraction (store, date, time, payment method)

**Service**: `bot/services/ai_extractor.py`

## Troubleshooting

### Common Issues

**Bot doesn't respond to commands**:
- Verify bot has both `bot` and `applications.commands` scopes
- Check DISCORD_TOKEN is correct
- For global commands, wait up to 1 hour for sync
- For instant sync, set DISCORD_GUILD_ID to test server ID

**OCR fails with 429 error**:
- Expected behavior - bot automatically falls back to OpenRouter vision model
- No action required

**Google Sheets sync fails**:
1. Verify `credentials.json` exists and is valid
2. Check service account has Editor access to spreadsheet
3. Verify `GOOGLE_SPREADSHEET_ID` is correct
4. Ensure Google Sheets API is enabled in GCP

**/clerk sync not finding receipts**:
1. Check `DATA_DIR=data` in `.env` (use relative path, not absolute)
2. Verify receipts exist in `data/receipts/`
3. Check file permissions: `sudo chown -R botuser:botuser /opt/discord-bot/app/data`
4. **See**: [docs/DATA_DIRECTORY_FIX.md](docs/DATA_DIRECTORY_FIX.md)

**Permission errors on GCP**:
```bash
sudo chown -R botuser:botuser /opt/discord-bot/app/data
sudo chmod -R 755 /opt/discord-bot/app/data
sudo systemctl restart discord-bot-dev.service
```

**Duplicate data in Google Sheets**:
1. Run migration script: `python migrate_sync_status.py`
2. Choose option 2 (mark as SYNCED) if already synced
3. Manually delete duplicate rows if needed

## File Naming Conventions

- **Receipt files**: `{YYYY-MM-DD}_{HHMM}_{store_lowercase}.json`
- **Python files**: snake_case
- **Shell scripts**: kebab-case
- **Models**: PascalCase class names

## Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for public methods
- Max line length: 100 characters
- Use `async`/`await` consistently for I/O operations

## Security Best Practices

1. **Never commit secrets**:
   - `.env*` files in .gitignore
   - `credentials.json` in .gitignore
   - Use GitHub Secrets for CI/CD

2. **Use separate bot tokens**:
   - Different tokens for local/dev/production
   - Prevents accidental production impact

3. **Limit service account permissions**:
   - Only grant necessary IAM roles
   - Separate service accounts for CI/CD vs bot runtime

4. **Restrict file permissions**:
   ```bash
   chmod 600 .env.production
   chmod 700 credentials/
   ```

5. **Regular secret rotation**:
   - Rotate Discord bot tokens quarterly
   - Rotate API keys annually
   - Rotate Google service account keys annually

## Development Milestones

### Completed Milestones ✅

1. **Core Infrastructure** (87.5%):
   - Project setup, config management, bot skeleton
   - Data models, JSON storage, OCR integration
   - Receipt commands implementation
   - ✅ Receipt parsing for multiple store formats

2. **Item Guessing** (100%):
   - OpenRouter integration
   - Corrections cache system
   - Guess commands (currently deactivated - AI extraction replaced it)

3. **Clerk Bot** (100%):
   - Google Sheets integration
   - Receipt sync with dual-sync system
   - Data aggregation functions
   - Clerk commands
   - Monthly expense aggregation with formulas
   - Budget tracking ($100/month for eating out)
   - 4 new expense commands (personal, utilities, transport, extraordinary)

4. **Installation & Deployment** (100%):
   - Interactive installation script (install.sh)
   - Conda/venv support
   - GCP deployment with systemd services
   - GitHub Actions CI/CD pipeline
   - Comprehensive documentation

### Active Development

- **New Development Phase** (started 2026-03-18)
  - All previous feature branches cleaned up and merged/archived
  - Branch oversight tracked in `.claude/context/main.md`
  - See context file for active branches and workflow rules

## Resources

- [Discord Bot Token Guide](https://discord.com/developers/docs/getting-started)
- [Mistral AI Platform](https://console.mistral.ai/)
- [OpenRouter](https://openrouter.ai/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [gspread Python Library](https://docs.gspread.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

*Last Updated: January 20, 2026*
*Project Status: Active Production Deployment*
