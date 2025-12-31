# Discord Receipt Bot System

A Discord bot for managing receipts, spending guesses, and financial tracking using Discord.py 2.x with slash commands.

## Features

- **Receipt Management**: Process, list, and view receipts
- **Spending Guesses**: Submit and track spending predictions
- **Financial Reports**: Generate spending reports and monthly summaries
- **Slash Commands**: Modern Discord slash command interface

## Project Structure

```
Discord-Receipt-Bot-System/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Entry point, loads cogs, syncs commands
│   ├── config.py        # Pydantic Settings loading from .env
│   ├── models.py        # Pydantic models for Receipt and ReceiptItem
│   ├── storage.py       # JSON file save/load functions
│   └── cogs/
│       ├── __init__.py
│       ├── receipt.py   # /receipt process, list, show commands
│       ├── guess.py     # /guess process, correct commands
│       └── clerk.py     # /clerk sync, spent, monthly commands
├── .env                 # Environment configuration (create from .env.example)
├── .env.example         # Example environment configuration
├── requirements.txt     # Python dependencies
└── README.md
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/minhtran1309/Discord-Receipt-Bot-System.git
   cd Discord-Receipt-Bot-System
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Discord bot token and guild ID:
     ```
     DISCORD_TOKEN=your_discord_bot_token_here
     GUILD_ID=your_guild_id_here
     DATA_DIR=./data
     ```

4. **Run the bot**
   ```bash
   python -m bot.main
   ```

## Commands

### Receipt Commands (`/receipt`)

- **`/receipt process`** - Process and add a new receipt
  - `items`: Items in format: `name:price:quantity, name:price:quantity, ...`
  - `notes`: Optional notes for the receipt
  - Example: `/receipt process items:"Coffee:3.50:2, Sandwich:8.99:1" notes:"Lunch"`

- **`/receipt list`** - List all receipts
  - `user`: Optional filter by user
  - Example: `/receipt list` or `/receipt list user:@JohnDoe`

- **`/receipt show`** - Show details of a specific receipt
  - `receipt_id`: The ID of the receipt to show
  - Example: `/receipt show receipt_id:abc123de`

### Guess Commands (`/guess`)

- **`/guess process`** - Submit a guess for monthly spending
  - `amount`: Your guess for the total spending amount
  - `month`: Optional month (YYYY-MM format, defaults to current month)
  - `category`: Optional category for the guess
  - Example: `/guess process amount:500.00 month:2024-01`

- **`/guess correct`** - Mark a guess as correct and set actual amount
  - `guess_id`: The ID of the guess to mark as correct
  - `actual_amount`: The actual spending amount
  - Example: `/guess correct guess_id:xyz789ab actual_amount:485.50`

### Clerk Commands (`/clerk`)

- **`/clerk sync`** - Sync slash commands with Discord
  - Requires admin permissions
  - Example: `/clerk sync`

- **`/clerk spent`** - Calculate total spending
  - `user`: Optional filter by user
  - `start_date`: Optional start date (YYYY-MM-DD)
  - `end_date`: Optional end date (YYYY-MM-DD)
  - Example: `/clerk spent` or `/clerk spent user:@JohnDoe start_date:2024-01-01`

- **`/clerk monthly`** - Get monthly spending report
  - `month`: Optional month (YYYY-MM format, defaults to current month)
  - Example: `/clerk monthly` or `/clerk monthly month:2024-01`

## Data Storage

All data is stored in JSON files in the `data/` directory:
- `data/receipts.json` - Receipt data
- `data/guesses.json` - Guess data

The data directory is created automatically on first run.

## Requirements

- Python 3.8+
- discord.py 2.0+
- pydantic 2.0+
- pydantic-settings 2.0+
- python-dotenv 1.0+

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token to your `.env` file
5. Enable the following Privileged Gateway Intents:
   - Server Members Intent
   - Message Content Intent
6. Go to OAuth2 → URL Generator
7. Select scopes: `bot`, `applications.commands`
8. Select bot permissions: `Send Messages`, `Embed Links`, `Read Message History`
9. Use the generated URL to invite the bot to your server
10. Get your server (guild) ID and add it to `.env`

## License

MIT License - See LICENSE file for details