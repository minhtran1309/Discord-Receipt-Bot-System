# Discord Bot Setup Guide

This guide will walk you through setting up your Discord bot and adding it to your personal Discord server.

## Step 1: Create a Discord Bot Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** in the top right
3. Enter a name for your bot (e.g., "Receipt Bot")
4. Click **"Create"**

## Step 2: Configure Bot Settings

### 2.1 Create the Bot User

1. In the left sidebar, click **"Bot"**
2. Click **"Add Bot"** (or **"Reset Token"** if the bot already exists)
3. Confirm by clicking **"Yes, do it!"**

### 2.2 Get Your Bot Token

1. Under the bot's username, click **"Reset Token"**
2. Click **"Yes, do it!"** to confirm
3. Click **"Copy"** to copy your bot token
4. **⚠️ IMPORTANT:** Save this token securely - you'll need it for your `.env` file
5. **Never share your bot token publicly!**

### 2.3 Enable Privileged Gateway Intents

Scroll down to **"Privileged Gateway Intents"** and enable:

- ✅ **Presence Intent** (optional, for presence updates)
- ✅ **Server Members Intent** (optional, for member information)
- ✅ **Message Content Intent** (**REQUIRED** for this bot)

Click **"Save Changes"** at the bottom.

## Step 3: Configure OAuth2 Permissions

### 3.1 Set Bot Permissions

1. In the left sidebar, click **"OAuth2"** → **"URL Generator"**
2. Under **"Scopes"**, check:
   - ✅ `bot`
   - ✅ `applications.commands` (for slash commands)

3. Under **"Bot Permissions"**, check:
   - ✅ **Send Messages**
   - ✅ **Embed Links**
   - ✅ **Attach Files**
   - ✅ **Read Message History**
   - ✅ **Use Slash Commands**

### 3.2 Generate Invite Link

1. Scroll down to **"Generated URL"** at the bottom
2. Click **"Copy"** to copy the invite URL
3. Save this URL - you'll use it to add the bot to your server

## Step 4: Add Bot to Your Discord Server

1. Open the invite URL you copied in step 3.2 in a web browser
2. Select your server from the dropdown menu
3. Click **"Continue"**
4. Review the permissions and click **"Authorize"**
5. Complete the CAPTCHA if prompted
6. The bot should now appear in your server's member list (offline until you run it)

## Step 5: Get Your Server (Guild) ID

This is needed for faster slash command sync during development.

### 5.1 Enable Developer Mode in Discord

1. Open Discord
2. Click the ⚙️ **Settings** icon (bottom left)
3. Go to **"Advanced"** (under "App Settings")
4. Enable **"Developer Mode"**
5. Click **"ESC"** to close settings

### 5.2 Copy Your Server ID

1. Right-click on your server icon (in the left sidebar)
2. Click **"Copy Server ID"**
3. Save this ID - you'll need it for your `.env` file

## Step 6: Configure Your `.env` File

1. Navigate to your project directory
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your favorite text editor:
   ```bash
   # Discord Configuration
   DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
   DISCORD_GUILD_ID=YOUR_SERVER_ID_HERE

   # Mistral OCR API
   MISTRAL_API_KEY=your_mistral_api_key_here
   MISTRAL_OCR_ENDPOINT=https://api.mistral.ai/v1/ocr

   # OpenRouter API
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_MODEL=mistralai/mistral-7b-instruct

   # Google Sheets
   GOOGLE_CREDENTIALS_PATH=credentials.json
   GOOGLE_SPREADSHEET_ID=your_google_spreadsheet_id_here

   # Application Settings
   CONFIDENCE_THRESHOLD=0.7
   DATA_DIR=data
   LOG_LEVEL=INFO
   ```

4. Replace:
   - `YOUR_BOT_TOKEN_HERE` with the token from step 2.2
   - `YOUR_SERVER_ID_HERE` with the server ID from step 5.2

## Step 7: Get API Keys

### 7.1 Mistral API Key (for OCR)

1. Go to [Mistral AI](https://console.mistral.ai/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy it to your `.env` file as `MISTRAL_API_KEY`

### 7.2 OpenRouter API Key (for AI Item Guessing)

1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up or log in
3. Go to [Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Copy it to your `.env` file as `OPENROUTER_API_KEY`

### 7.3 Google Sheets Setup

#### Create a Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create a service account:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Enter a name (e.g., "receipt-bot-sheets")
   - Click "Create and Continue"
   - Skip optional steps, click "Done"
5. Generate a JSON key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Click "Create"
   - A JSON file will download - save it as `credentials.json` in your project root

#### Create and Share a Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Add column headers in the first row:
   ```
   Date | Store | Item | Quantity | Price | Category
   ```
4. Copy the spreadsheet ID from the URL:
   - URL format: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the `SPREADSHEET_ID` part
   - Paste it in your `.env` file as `GOOGLE_SPREADSHEET_ID`
5. Share the spreadsheet with your service account:
   - Click the "Share" button
   - Open your `credentials.json` file
   - Find the `client_email` field (looks like: `name@project.iam.gserviceaccount.com`)
   - Add this email to your spreadsheet with "Editor" permissions

## Step 8: Run Your Bot

1. Activate your conda environment:
   ```bash
   conda activate discord_env
   ```

2. Run the bot:
   ```bash
   python -m bot.main
   ```

3. You should see output like:
   ```
   Logged in as YourBotName (ID: ...)
   Connected to 1 guilds
   Commands synced to guild YOUR_GUILD_ID
   ```

4. In Discord, type `/` in any channel to see your bot's slash commands!

## Available Commands

Once your bot is running, you can use these slash commands:

### Receipt Commands
- `/receipt process` - Upload and process a receipt image
- `/receipt list` - List all processed receipts
- `/receipt show <filename>` - Display a specific receipt
- `/receipt verify <filename>` - Mark receipt as verified
- `/receipt delete <filename>` - Delete a receipt

### AI Guessing Commands
- `/guess process <filename>` - Run AI guessing on receipt items
- `/guess correct <raw> <store> <name>` - Manually correct an item
- `/guess mappings` - View all learned corrections
- `/guess clear <raw> <store>` - Clear a specific correction

### Expense Tracking Commands
- `/clerk sync` - Sync verified receipts to Google Sheets
- `/clerk spent <product> [month]` - Query spending on a product
- `/clerk monthly [YYYY-MM]` - Get monthly expense summary
- `/clerk report <start_date> <end_date>` - Generate expense report

## Troubleshooting

### Bot appears offline
- Make sure the bot is running (`python -m bot.main`)
- Check that your `DISCORD_TOKEN` in `.env` is correct

### Slash commands don't appear
- Wait a few minutes (global commands can take up to 1 hour)
- If using `DISCORD_GUILD_ID`, commands should appear immediately
- Try kicking and re-inviting the bot
- Make sure `applications.commands` scope was enabled when inviting

### Bot doesn't respond to commands
- Check the console/terminal for error messages
- Verify all API keys in `.env` are correct
- Check that the bot has proper permissions in your server

### "Missing Permissions" error
- Right-click the bot in your server's member list
- Make sure it has the necessary role permissions
- Re-invite the bot with the correct permissions using the OAuth2 URL

### API errors (OCR/OpenRouter/Google Sheets)
- Verify API keys are correct in `.env`
- Check that you have credits/quota for paid APIs
- For Google Sheets: ensure service account email has Editor access to the spreadsheet

## Production Deployment (Optional)

For running the bot 24/7, consider:

- **VPS Hosting**: DigitalOcean, Linode, AWS EC2
- **Cloud Platforms**: Heroku, Railway, Render
- **Process Management**: Use `systemd`, `pm2`, or `screen` to keep bot running
- **Monitoring**: Set up logging and error tracking

### Example: Running with systemd on Linux

Create a service file `/etc/systemd/system/receipt-bot.service`:

```ini
[Unit]
Description=Discord Receipt Bot
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/Discord-Receipt-Bot-System
Environment="PATH=/home/yourusername/miniforge3/envs/discord_env/bin"
ExecStart=/home/yourusername/miniforge3/envs/discord_env/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl enable receipt-bot
sudo systemctl start receipt-bot
sudo systemctl status receipt-bot
```

## Security Best Practices

1. ✅ Never commit `.env` or `credentials.json` to version control
2. ✅ Keep your bot token secret
3. ✅ Regularly rotate API keys
4. ✅ Use environment variables for all sensitive data
5. ✅ Limit bot permissions to only what's needed
6. ✅ Regularly update dependencies for security patches

## Need Help?

If you encounter issues:
1. Check the console output for error messages
2. Verify all configuration in `.env`
3. Review the [discord.py documentation](https://discordpy.readthedocs.io/)
4. Check the logs in your terminal

---

**Happy receipt tracking! 📝💰**
