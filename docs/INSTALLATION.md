# Installation Guide

This guide will help you install and configure the Discord Receipt Bot on your local machine or server.

## Quick Installation (Interactive)

The easiest way to install the bot is using the interactive installation script:

```bash
./install.sh
```

This script will:
1. Check for Conda/Miniconda installation (optional)
   - Offers to install Miniconda if not present
   - Supports both Conda and Python venv environments
2. Check for Python 3.11+ installation
3. Set up a virtual environment (Conda or venv)
4. Install all dependencies
5. Prompt you for API keys and configuration
6. Create the `.env` configuration file
7. Set up the data directory structure
8. Optionally test your configuration
9. Create a start script for easy bot launching

### Conda vs Python venv

The script supports both environment management systems:

**Conda/Miniconda** (Recommended for production):
- Better package management and dependency resolution
- Easier environment management across projects
- Used in GCP deployment setup
- The script can install Miniconda automatically

**Python venv** (Simpler for local development):
- Built into Python, no extra installation needed
- Lightweight and straightforward
- Perfect for single-project setups

## Manual Installation

If you prefer to set up the bot manually, follow these steps:

### Prerequisites

- **Python 3.11 or higher**
- **pip** (Python package installer)
- **Git** (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/minhtran1309/Discord-Receipt-Bot-System.git
cd Discord-Receipt-Bot-System
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv discord_env
source discord_env/bin/activate  # On Windows: discord_env\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and fill in your configuration:

```bash
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=  # Optional: your server ID for faster sync

# Mistral OCR API
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_OCR_MODEL=mistral-ocr-latest

# OpenRouter API (for AI extraction and item guessing)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Google Sheets
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SPREADSHEET_ID=your_google_spreadsheet_id_here

# Application Settings
CONFIDENCE_THRESHOLD=0.7
DATA_DIR=data
LOG_LEVEL=INFO
BOT_NAME=Receipt Bot (Local)
```

### Step 5: Set Up Google Sheets

1. Create a Google Cloud Platform service account
2. Enable the Google Sheets API
3. Download the credentials JSON file
4. Place it at `credentials.json` (or the path specified in `GOOGLE_CREDENTIALS_PATH`)
5. Share your Google Spreadsheet with the service account email

For detailed instructions, see [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md)

### Step 6: Create Data Directory

```bash
mkdir -p data/receipts data/items
echo "{}" > data/corrections.json
```

### Step 7: Run the Bot

```bash
python -m bot.main
```

## Getting API Keys

### Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Click "Reset Token" to get your bot token
5. Enable these privileged gateway intents:
   - Message Content Intent

### Mistral API Key

1. Go to [Mistral AI Platform](https://console.mistral.ai/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key

### OpenRouter API Key

1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up or log in
3. Navigate to Keys
4. Create a new API key

### Google Spreadsheet ID

The Spreadsheet ID is in the URL of your Google Sheet:

```
https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
```

## Inviting the Bot to Your Discord Server

Use this URL template (replace `YOUR_CLIENT_ID` with your bot's client ID):

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2147485696&scope=bot%20applications.commands
```

**Required Permissions:**
- `bot` scope
- `applications.commands` scope (for slash commands)
- Send Messages
- Embed Links
- Attach Files
- Read Message History

## Verification

After installation, test the bot:

1. In Discord, try `/ping` to check if the bot responds
2. Try `/receipt process` and attach a receipt image
3. Check `/clerk status` to verify Google Sheets connection

## Troubleshooting

### Bot doesn't respond to commands

**Solution**: Make sure you invited the bot with both `bot` and `applications.commands` scopes.

### OCR fails with 401 error

**Solution**: Check your `MISTRAL_API_KEY` in the `.env` file.

### Google Sheets sync fails

**Solution**:
1. Verify `credentials.json` exists and is valid
2. Check that the service account email has edit access to the spreadsheet
3. Verify `GOOGLE_SPREADSHEET_ID` is correct

### Python version error

**Solution**: The bot requires Python 3.11 or higher. Check your version:

```bash
python3 --version
```

If you have an older version, install Python 3.11+:

**macOS:**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3.11
```

### Virtual environment activation fails

**macOS/Linux:**
```bash
source discord_env/bin/activate
```

**Windows:**
```bash
discord_env\Scripts\activate
```

## Updating the Bot

To update to the latest version:

```bash
git pull origin main
source discord_env/bin/activate  # Activate venv
pip install --upgrade -r requirements.txt
```

## Uninstallation

To remove the bot:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf discord_env

# Remove data directory (optional - contains your receipt data)
# rm -rf data

# Remove configuration
rm .env

# Remove the repository
cd ..
rm -rf Discord-Receipt-Bot-System
```

## Next Steps

- Read the [User Guide](../README.md) to learn about available commands
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment options
- Check [CLAUDE.md](../CLAUDE.md) for technical architecture details
