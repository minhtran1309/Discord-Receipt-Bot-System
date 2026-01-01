# Discord-Receipt-Bot-System

A Discord bot for processing grocery receipts, identifying items using AI, and tracking expenses in Google Sheets.

## Features

- **Receipt Processing**: Upload receipt images and extract items via OCR (Mistral API)
- **Smart Item Identification**: AI-powered guessing of abbreviated product names (OpenRouter)
- **Learning System**: Learns from your corrections for future accuracy
- **Expense Tracking**: Syncs data to Google Sheets for easy tracking
- **Spending Queries**: Ask the bot about your spending habits

## Quick Start

### Prerequisites

- Python 3.11+
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- Mistral API Key (for OCR)
- OpenRouter API Key (for item guessing)
- Google Cloud Service Account (for Sheets integration)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/receipt-bot.git
   cd receipt-bot
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Set up Google Sheets credentials:
   - Create a service account in Google Cloud Console
   - Download the JSON credentials file as `credentials.json`
   - Share your target spreadsheet with the service account email

6. Run the bot:
   ```bash
   python -m bot.main
   ```

## Commands

### Receipt Processing
| Command | Description |
|---------|-------------|
| `/receipt process` | Upload and process a receipt image |
| `/receipt list` | List all processed receipts |
| `/receipt show <filename>` | Display a specific receipt |
| `/receipt verify <filename>` | Mark receipt as verified |

### Item Identification
| Command | Description |
|---------|-------------|
| `/guess process <filename>` | Run AI guessing on receipt items |
| `/guess correct <raw> <store> <name>` | Manually correct an item |
| `/guess mappings` | View all learned corrections |

### Expense Tracking
| Command | Description |
|---------|-------------|
| `/clerk sync` | Sync verified receipts to Google Sheets |
| `/clerk spent <product>` | Query spending on a product |
| `/clerk monthly [YYYY-MM]` | Get monthly expense summary |

### Utility
| Command | Description |
|---------|-------------|
| `/process_full` | Full pipeline: OCR → Guess → Sync |
| `/ping` | Check bot status |

## Project Structure

```
receipt-bot/
├── bot/
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── cogs/             # Discord command modules
│   ├── services/         # API integrations
│   ├── models.py         # Data models
│   └── storage.py        # File operations
├── data/
│   ├── receipts/         # Processed receipts (JSON)
│   └── corrections.json  # Learned item mappings
├── tests/
├── .env.example
├── requirements.txt
├── CLAUDE.md             # Development guide for Claude Code
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

## Development

This project uses `CLAUDE.md` to guide AI-assisted development with Claude Code.

```bash
# Run tests
pytest tests/ -v

# Format code
black bot/ tests/
isort bot/ tests/

# Type checking
mypy bot/
```

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request