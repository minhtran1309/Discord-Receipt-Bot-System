# Google Sheets Setup Guide for Clerk Bot

This guide will walk you through setting up Google Sheets integration for the Discord Receipt Bot's Clerk functionality.

## Overview

You will need to obtain two pieces of information:
1. **GOOGLE_CREDENTIALS_PATH**: Path to a service account JSON credentials file
2. **GOOGLE_SPREADSHEET_ID**: The ID of your target Google Spreadsheet

---

## Part 1: Google Cloud Setup

### Step 1.1: Create a Google Cloud Project

1. Open your browser and go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. At the top of the page, click on the **project dropdown** (next to "Google Cloud")
4. In the modal that appears, click **"NEW PROJECT"** button (top right)
5. Fill in the project details:
   - **Project name**: `receipt-bot` (or choose your own name)
   - **Organization**: Leave as default (No organization)
   - **Location**: Leave as default
6. Click **"CREATE"**
7. Wait 10-30 seconds for the project to be created
8. Once created, click on the **project dropdown** again and select your new project

---

### Step 1.2: Enable Google Sheets API

1. In the Google Cloud Console, click the **hamburger menu** (☰) in the top-left corner
2. Navigate to **"APIs & Services"** → **"Library"**
3. In the search bar, type: `Google Sheets API`
4. Click on **"Google Sheets API"** from the search results
5. Click the blue **"ENABLE"** button
6. Wait for the API to be enabled (should take a few seconds)
7. You should see "API enabled" confirmation

---

### Step 1.3: Create a Service Account

A service account is a special type of Google account that represents your bot application.

1. In the left sidebar, navigate to **"APIs & Services"** → **"Credentials"**
2. At the top of the page, click **"+ CREATE CREDENTIALS"**
3. From the dropdown, select **"Service account"**
4. Fill in the service account details on **page 1**:
   - **Service account name**: `receipt-bot-service`
   - **Service account ID**: Will auto-generate as `receipt-bot-service` (you can customize if needed)
   - **Service account description**: `Service account for Discord receipt bot to access Google Sheets`
5. Click **"CREATE AND CONTINUE"**
6. On **page 2** ("Grant this service account access to project"):
   - **Skip this step** - click **"CONTINUE"** without selecting any roles
7. On **page 3** ("Grant users access to this service account"):
   - **Skip this step** - click **"DONE"**
8. You should now see your service account listed on the Credentials page

---

### Step 1.4: Create and Download Service Account Key (JSON)

1. On the **Credentials** page, scroll down to **"Service Accounts"** section
2. Click on the **service account email** you just created
   - Example: `receipt-bot-service@your-project-id.iam.gserviceaccount.com`
3. Click on the **"KEYS"** tab at the top
4. Click **"ADD KEY"** → **"Create new key"**
5. In the modal that appears:
   - Select **"JSON"** as the key type
   - Click **"CREATE"**
6. A JSON file will automatically download to your computer
   - Example filename: `receipt-bot-abc123-1234567890ab.json`
7. **IMPORTANT**: Keep this file secure - it contains sensitive credentials

---

### Step 1.5: Move and Rename the Credentials File

1. Locate the downloaded JSON file (usually in your `Downloads` folder)
2. Rename the file to `credentials.json`
3. Move it to your Discord bot project root directory:

**Option A - Using File Manager (GUI):**
- Drag and drop the file to: `/Users/minhtran/Git_Packages/Discord-Receipt-Bot-System/`

**Option B - Using Terminal:**
```bash
# Replace 'receipt-bot-abc123-1234567890ab.json' with your actual filename
mv ~/Downloads/receipt-bot-abc123-1234567890ab.json /Users/minhtran/Git_Packages/Discord-Receipt-Bot-System/credentials.json
```

4. Verify the file is in the correct location:
```bash
ls -la /Users/minhtran/Git_Packages/Discord-Receipt-Bot-System/credentials.json
```

You should see the file listed.

---

### Step 1.6: Verify credentials.json Format

Open the `credentials.json` file to verify it looks correct. It should have this structure:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "1234567890abcdef...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BA...\n-----END PRIVATE KEY-----\n",
  "client_email": "receipt-bot-service@your-project-id.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/receipt-bot-service%40your-project-id.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

**Important fields to note:**
- `client_email`: You'll need this email address in Part 2
- `private_key`: Must start with `-----BEGIN PRIVATE KEY-----`

---

## Part 2: Google Sheets Setup

### Step 2.1: Create a New Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click the **"+ Blank"** button to create a new spreadsheet
3. Click on **"Untitled spreadsheet"** at the top-left
4. Rename it to: `Receipt Bot - Expenses` (or any name you prefer)

---

### Step 2.2: Set Up the Spreadsheet Header Row

Click on cell **A1** and enter the following headers across the first row:

| A1 | B1 | C1 | D1 | E1 | F1 | G1 | H1 |
|----|----|----|----|----|----|----|-----|
| Date | Store | Item | Quantity | Unit | Price | Category | SKU |

**Optional: Format the header row**
1. Select row 1 (click on the row number "1")
2. Make it **bold** (Ctrl/Cmd + B)
3. Add a background color (Format → Fill color)
4. Freeze the header row (View → Freeze → 1 row)

---

### Step 2.3: Get the Spreadsheet ID

1. Look at the **URL** in your browser's address bar
2. The URL format is:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit#gid=0
   ```

3. The **Spreadsheet ID** is the long string between `/d/` and `/edit`

**Example:**
```
URL: https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t/edit

Spreadsheet ID: 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t
```

4. **Copy this ID** - you'll need it for your `.env` file

---

### Step 2.4: Share the Spreadsheet with Service Account ⚠️ CRITICAL

**This is the most important step!** Without this, the bot cannot access your spreadsheet.

1. Click the **"Share"** button in the top-right corner of Google Sheets
2. In the "Add people and groups" field, paste your **service account email**
   - Find this in your `credentials.json` file under the `"client_email"` field
   - Example: `receipt-bot-service@receipt-bot-123456.iam.gserviceaccount.com`
3. Click in the email field and the email should appear as a chip/tag
4. Make sure the permission dropdown is set to **"Editor"** (not Viewer)
5. **IMPORTANT**: **Uncheck** "Notify people"
   - The service account doesn't need email notifications
6. Click **"Share"** or **"Send"**
7. You should see the service account email listed under "People with access"

**Verification:**
- The service account email should appear in the sharing list
- Permission should be "Editor"
- If you see "Awaiting access approval", something went wrong - remove and re-add the email

---

## Part 3: Configure Your Bot

### Step 3.1: Update the .env File

1. Open your `.env` file in the project root directory
2. Find or add these two lines:

```bash
# Google Sheets Configuration
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t
```

3. Replace the `GOOGLE_SPREADSHEET_ID` value with **your actual Spreadsheet ID** from Step 2.3

**Example .env file:**
```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id

# Mistral OCR
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_OCR_MODEL=mistral-ocr-latest

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini

# Google Sheets
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t

# Application Settings
CONFIDENCE_THRESHOLD=0.7
DATA_DIR=data
LOG_LEVEL=INFO
```

4. Save the `.env` file

---

### Step 3.2: Verify credentials.json is Ignored by Git

The `credentials.json` file contains sensitive information and should **NEVER** be committed to git.

1. Check your `.gitignore` file:
```bash
cat .gitignore | grep credentials.json
```

You should see:
```
# Google credentials
credentials.json
*.json
```

2. Verify git is ignoring it:
```bash
git status
```

The `credentials.json` file should **NOT** appear in the output. If it does, it means it's being tracked by git - this is dangerous!

---

## Part 4: Test the Setup

### Step 4.1: Install Python Dependencies

Make sure you have the required packages:

```bash
pip install gspread google-auth
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

---

### Step 4.2: Start the Bot

```bash
python -m bot.main
```

You should see output like:
```
2025-01-06 10:30:00 INFO     Bot is ready!
2025-01-06 10:30:00 INFO     Logged in as: YourBotName#1234
```

---

### Step 4.3: Test the Clerk Sync Command

1. **First, process and verify a receipt:**
   - In Discord: `/receipt process` (upload a receipt image)
   - Wait for processing to complete
   - In Discord: `/receipt verify <filename>` (use the filename from the previous step)

2. **Sync to Google Sheets:**
   - In Discord: `/clerk sync`
   - You should see: "Sync Complete - Synced X verified receipts to Google Sheets"

3. **Check your Google Sheet:**
   - Open your spreadsheet
   - You should see data populated in the rows below the header
   - Example:
     ```
     Date       | Store      | Item           | Quantity | Unit | Price | Category | SKU
     2026-01-03 | Woolworths | Fresh Milk 2L  | 1        | ea   | 4.50  | Dairy    |
     2026-01-03 | Woolworths | White Bread    | 1        | ea   | 2.80  | Bakery   |
     ```

---

## Troubleshooting

### ❌ Error: "credentials.json not found"

**Cause:** The bot can't find the credentials file.

**Solution:**
1. Check the file exists:
   ```bash
   ls -la credentials.json
   ```
2. Verify the path in `.env`:
   ```bash
   cat .env | grep GOOGLE_CREDENTIALS_PATH
   ```
3. Use absolute path if needed:
   ```bash
   GOOGLE_CREDENTIALS_PATH=/Users/minhtran/Git_Packages/Discord-Receipt-Bot-System/credentials.json
   ```

---

### ❌ Error: "Permission denied" or "403 Forbidden"

**Cause:** The service account doesn't have access to the spreadsheet.

**Solution:**
1. Open your Google Sheet
2. Click **Share** button
3. Verify the service account email is listed with **Editor** permissions
4. If not listed, add it again (see Step 2.4)
5. Double-check the email matches exactly with `client_email` in `credentials.json`

---

### ❌ Error: "API has not been used in project before"

**Cause:** Google Sheets API is not enabled for your project.

**Solution:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Library**
4. Search for "Google Sheets API"
5. Click **ENABLE**
6. Wait a few minutes for the change to propagate
7. Try running `/clerk sync` again

---

### ❌ Error: "Invalid credentials"

**Cause:** The credentials.json file is corrupted or invalid.

**Solution:**
1. Go back to Google Cloud Console
2. Delete the old key (in Service Account → Keys tab)
3. Create a new key (see Step 1.4)
4. Download and replace `credentials.json`
5. Restart the bot

---

### ❌ Error: "Spreadsheet not found"

**Cause:** The Spreadsheet ID is incorrect.

**Solution:**
1. Open your Google Sheet in browser
2. Copy the ID from the URL (see Step 2.3)
3. Update `GOOGLE_SPREADSHEET_ID` in `.env`
4. Restart the bot

---

## Security Best Practices

### 🔒 Protect Your Credentials

1. **Never commit credentials.json to git**
   - Already in `.gitignore` ✓
   - Verify with: `git status` (should not show credentials.json)

2. **Never share credentials.json**
   - Don't email it
   - Don't upload to cloud storage
   - Don't paste contents in chat/forums

3. **Keep credentials.json secure**
   - Store only on your local machine
   - Use file permissions to restrict access:
     ```bash
     chmod 600 credentials.json
     ```

4. **Rotate keys if compromised**
   - If you accidentally expose credentials.json:
     1. Go to Google Cloud Console
     2. Revoke the old key immediately
     3. Create a new key
     4. Update your bot

---

### 🔒 Spreadsheet Access Control

1. **Don't share spreadsheet publicly**
   - Keep sharing settings to "Restricted"
   - Only share with specific people you trust

2. **Service account has Editor permissions**
   - The bot can read, write, modify, and delete data
   - Be cautious about what commands you run

3. **Monitor spreadsheet activity**
   - Use Google Sheets version history to track changes
   - File → Version history → See version history

---

## Next Steps

Once your setup is complete, you can use all Clerk bot commands:

### Available Commands

| Command | Description |
|---------|-------------|
| `/clerk sync` | Sync all verified receipts to Google Sheets |
| `/clerk spent <product> [month]` | Query total spending on a product |
| `/clerk monthly [YYYY-MM]` | Get monthly expense summary |
| `/clerk report <start> <end>` | Generate expense report for date range |

### Example Workflow

1. Process receipts: `/receipt process` (upload images)
2. Verify receipts: `/receipt verify <filename>`
3. Sync to Google Sheets: `/clerk sync`
4. Query spending: `/clerk spent milk`
5. Monthly summary: `/clerk monthly 2026-01`
6. Generate report: `/clerk report 2026-01-01 2026-01-31`

---

## Summary Checklist

Before using the Clerk bot, verify you've completed all steps:

- [ ] Created Google Cloud project
- [ ] Enabled Google Sheets API
- [ ] Created service account
- [ ] Downloaded credentials.json
- [ ] Moved credentials.json to project root
- [ ] Created Google Spreadsheet
- [ ] Added header row to spreadsheet
- [ ] Copied Spreadsheet ID from URL
- [ ] Shared spreadsheet with service account email (Editor permissions)
- [ ] Updated GOOGLE_CREDENTIALS_PATH in .env
- [ ] Updated GOOGLE_SPREADSHEET_ID in .env
- [ ] Verified credentials.json is in .gitignore
- [ ] Tested `/clerk sync` command successfully

---

## Additional Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [gspread Python Library Docs](https://docs.gspread.org/)
- [Service Account Authentication](https://cloud.google.com/iam/docs/service-accounts)

---

**Need Help?**

If you encounter issues not covered in this guide:
1. Check the bot logs for detailed error messages
2. Verify all steps in the checklist above
3. Review the troubleshooting section
4. Check that all API keys in `.env` are valid

---

*Last Updated: January 6, 2026*
