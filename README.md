# Discord-Receipt-Bot-System

A Discord bot for processing grocery receipts, identifying items using AI, and tracking expenses in Google Sheets.

## Features

- **Receipt Processing**: Upload receipt images and extract structured data via OCR (Mistral API + OpenRouter AI)
- **AI-Powered Extraction**: Automatically categorizes items and handles multi-language receipts
- **Purchase Analytics**: View store purchases by month/year with spending breakdowns
- **Expense Tracking**: Syncs data to Google Sheets for easy tracking
- **Budget Management**: Track eating out expenses with $100/month budget, surplus rolls to holiday fund
- **Spending Queries**: Ask the bot about your spending habits
- **Smart Alerts**: Get reminded about budget overspending when verifying grocery receipts

## Quick Start

### Prerequisites

- Python 3.11+
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- Mistral API Key (for OCR text extraction)
- OpenRouter API Key (for AI-powered data extraction)
- Google Cloud Service Account (for Sheets integration)

### Installation

**Option 1: Interactive Installation (Recommended)**

Run the interactive installation script that will guide you through the entire setup:

```bash
./install.sh
```

The script will:
- Check Python installation
- Set up virtual environment
- Install dependencies
- Prompt for API keys
- Create `.env` configuration
- Set up data directories
- Test configuration

**Option 2: Manual Installation**

For manual installation steps, see [docs/INSTALLATION.md](docs/INSTALLATION.md)

Quick manual setup:

1. Clone and enter the repository:
   ```bash
   git clone https://github.com/minhtran1309/Discord-Receipt-Bot-System.git
   cd Discord-Receipt-Bot-System
   ```

2. Create virtual environment and install dependencies:
   ```bash
   python3 -m venv discord_env
   source discord_env/bin/activate
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Set up Google Sheets credentials and run:
   ```bash
   python -m bot.main
   ```

### Extended Installation: GCP Deployment with CI/CD

For production deployment on Google Cloud Platform with automated CI/CD pipelines:

1. **Set up GCP Compute Engine**:
   - Create a GCP project and Compute Engine VM instance
   - Install conda/miniconda on the server
   - Clone the repository to `/opt/discord-bot/app/`
   - Create `botuser` account for running the bot

2. **Create separate Discord bot applications**:
   - Create three Discord bot applications (Local, Dev, Production)
   - Get separate tokens for each environment
   - See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed steps

3. **Set up systemd services**:
   ```bash
   # On the GCP server, run:
   bash scripts/setup_systemd_services.sh
   ```
   This creates two systemd services:
   - `discord-bot.service` - Production bot
   - `discord-bot-dev.service` - Development bot

4. **Configure environment files on server**:
   - Create `.env.development` for dev bot (points to dev spreadsheet)
   - Create `.env.production` for prod bot (points to prod spreadsheet)
   - **Important**: Do not use inline comments in .env files (Pydantic parsing issue)

5. **Set up GitHub Actions secrets**:
   - `GCP_SA_KEY` - Service account key for GitHub Actions to access GCP
   - `GOOGLE_CREDENTIALS_DEV` - Base64-encoded Google Sheets credentials for dev
   - `GOOGLE_CREDENTIALS_PROD` - Base64-encoded Google Sheets credentials for prod

6. **Automated deployments**:
   - Push to `guess_feature` or `clerk_feature_dev` → Auto-deploys to dev server
   - Merge to `main` → Auto-deploys to production server
   - See [docs/GITHUB_ACTIONS_EXPLAINED.md](docs/GITHUB_ACTIONS_EXPLAINED.md) for workflow details

7. **Local development with bot switching**:
   ```bash
   # Start local bot (stops GCP dev bot automatically)
   bash scripts/start_local_bot.sh

   # Stop local bot (restarts GCP dev bot)
   bash scripts/stop_local_bot.sh
   ```

**Complete setup guide**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for comprehensive deployment instructions.

## Commands

### Receipt Processing
| Command | Description |
|---------|-------------|
| `/receipt process <image>` | Upload and process a receipt image with AI extraction |
| `/receipt list` | List all processed receipts |
| `/receipt show <filename>` | Display a specific receipt in readable TOON format |
| `/receipt verify <filename>` | Mark receipt as verified |
| `/receipt delete <filename>` | Delete a receipt |
| `/receipt correct_name <filename> <item_index> <new_name>` | Correct an item's name |
| `/receipt correct_price <filename> <item_index> <new_price>` | Correct an item's price |
| `/receipt correct_category <filename> <item_index> <new_category>` | Correct an item's category |
| `/receipt view_store <store> [period]` | View store purchases by month (YYYY-MM) or year (YYYY) with analytics |

### Expense Tracking & Budget Management
| Command | Description |
|---------|-------------|
| `/clerk sync` | Sync verified receipts to Google Sheets (prevents duplicates) |
| `/clerk status` | Check sync status of all receipts |
| `/clerk spent <product> [month]` | Query spending on a product (optional month filter) |
| `/clerk monthly [month]` | Get monthly expense summary (YYYY-MM format) |
| `/clerk report <start_date> <end_date>` | Generate expense report for date range (YYYY-MM-DD) |
| `/clerk special_treat <amount>` | Log eating out or takeaway drink expense (tracks $100/month budget) |
| `/clerk budget_status [month]` | Check eating out budget status (defaults to current month) |

### Utility
| Command | Description |
|---------|-------------|
| `/ping` | Check bot status |

## Project Structure

```
receipt-bot/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── cogs/                # Discord command modules
│   │   ├── receipt.py       # Receipt processing commands
│   │   └── clerk.py         # Expense tracking & budget commands
│   ├── services/            # API integrations
│   │   ├── ocr.py           # Mistral OCR service
│   │   ├── ai_extractor.py  # AI-powered data extraction
│   │   └── sheets.py        # Google Sheets integration (multi-tab support)
│   ├── models.py            # Data models (Receipt, BudgetEntry, etc.)
│   ├── storage.py           # Receipt file operations
│   └── budget_storage.py    # Budget data persistence
├── data/
│   ├── receipts/            # Processed receipts (JSON)
│   ├── budgets/             # Budget entries by month (JSON)
│   ├── items/               # Extracted items (TSV)
│   └── corrections.json     # Item name corrections
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Configuration

See `.env.example` for all configuration options:

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Your Discord bot token |
| `MISTRAL_API_KEY` | Mistral API key for OCR |
| `OPENROUTER_API_KEY` | OpenRouter API key for AI |
| `GOOGLE_SPREADSHEET_ID` | Target Google Sheet ID |
| `CONFIDENCE_THRESHOLD` | AI confidence threshold (default: 0.7) |

## How It Works

### Receipt Processing
1. **Upload Receipt**: Use `/receipt process` with an image attachment (JPEG, PNG, HEIC)
2. **OCR Extraction**: Mistral OCR extracts raw text from the receipt
3. **AI Processing**: OpenRouter (GPT-4o-mini) parses the text into structured data:
   - Combines multi-line items
   - Extracts units (kg, g, L, ml) separately
   - Categorizes items (Produce, Meat, Dairy, etc.)
   - Preserves multi-language text (Chinese, Korean, etc.)
4. **Storage**: Saves receipt as JSON and items as TSV
5. **Verification**: Mark receipt as verified with `/receipt verify` (includes budget alert if overspent)
6. **Sync**: Export verified receipts to Google Sheets with `/clerk sync` (prevents duplicates)

### Budget Management
1. **Log Expense**: Use `/clerk special_treat 15.50` to log eating out or takeaway expenses
2. **Dual Tracking**: Saves locally to `data/budgets/{month}/` and syncs to Google Sheets `eat_out_2026` tab
3. **Budget Monitoring**: Tracks $100/month budget, shows remaining amount instantly
4. **Surplus Tracking**: Unused budget from Jan-Oct rolls over to Nov/Dec for holiday shopping
5. **Smart Alerts**: Get reminded about overspending when verifying grocery receipts
6. **Analytics**: View budget status with `/clerk budget_status` for current or any specific month

## Development

```bash
# Run tests
pytest tests/ -v

# Format code
black bot/ tests/
isort bot/ tests/

# Type checking
mypy bot/
```

## Troubleshooting

### Mistral OCR Rate Limiting (429 Error)
If you encounter "Provider returned error, code: 429", the bot will automatically fall back to OpenRouter's vision model (`qwen/qwen3-vl-30b-a3b-instruct`). This is expected during high load and does not require any action from you.

### Free Promotional Items
Receipts with free items (buy X get Y free promotions) are now supported. Free items will be marked for review with lower confidence (50%) to ensure accuracy. Use the `/receipt correct_name` command if you need to update the item name.

### GCP Deployment: Pull Request Errors
If you see "fatal: couldn't find remote ref merge" when creating pull requests, this is expected behavior. Pull requests only run tests and do not trigger deployments. Only pushes to `guess_feature` or `clerk_feature_dev` branches will deploy to the dev server.

### /clerk sync Not Finding Receipts
If `/clerk sync` reports no receipts even though you've processed them:

1. **Check data directory configuration** in your `.env` file:
   ```bash
   DATA_DIR=data  # ✅ Correct (relative path)
   # NOT: DATA_DIR=/opt/discord-bot/data  # ❌ Wrong
   ```

2. **Verify receipts exist** in the correct location:
   - Local: `data/receipts/`
   - GCP: `/opt/discord-bot/app/data/receipts/`

3. **For GCP deployments**, see [docs/DATA_DIRECTORY_FIX.md](docs/DATA_DIRECTORY_FIX.md) for detailed troubleshooting steps.

### Permission Issues on GCP
If you encounter permission errors when processing receipts on GCP:
```bash
# SSH into GCP server
sudo chown -R botuser:botuser /opt/discord-bot/app/data
sudo chmod -R 755 /opt/discord-bot/app/data
sudo systemctl restart discord-bot-dev.service
```

## License

MIT License - See LICENSE file for details.
