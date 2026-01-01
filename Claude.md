# CLAUDE.md - Discord Receipt Bot System

## Project Overview

This is a Discord bot system for processing grocery receipts, identifying items, and tracking expenses. The system consists of three functional modules (cogs) within a single Discord bot:

1. **Receipt Bot**: OCR processing of receipt images using Mistral OCR API
2. **Guessing Bot**: AI-powered item name identification using OpenRouter API
3. **Clerk Bot**: Expense aggregation and Google Sheets synchronization

## Tech Stack

- **Language**: Python 3.11+
- **Discord Framework**: discord.py 2.x with app_commands (slash commands)
- **HTTP Client**: httpx (async)
- **Google Sheets**: gspread + google-auth
- **Data Storage**: JSON files (MVP), SQLite (future)
- **Config Management**: python-dotenv + pydantic-settings

## Project Structure

```
receipt-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py                  # Entry point, bot initialization
│   ├── config.py                # Settings and environment loading
│   ├── cogs/
│   │   ├── __init__.py
│   │   ├── receipt.py           # /receipt commands - OCR processing
│   │   ├── guess.py             # /guess commands - item identification
│   │   └── clerk.py             # /clerk commands - aggregation & sheets
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr.py               # Mistral OCR API integration
│   │   ├── guesser.py           # OpenRouter API integration
│   │   └── sheets.py            # Google Sheets operations
│   ├── models.py                # Pydantic data models
│   └── storage.py               # JSON file operations
├── data/
│   ├── receipts/                # Processed receipt JSON files
│   └── corrections.json         # Item name mappings from user corrections
├── tests/
│   ├── __init__.py
│   ├── test_ocr.py
│   ├── test_guesser.py
│   └── test_storage.py
├── .env.example                 # Template for environment variables
├── .gitignore
├── requirements.txt
├── README.md
└── CLAUDE.md                    # This file
```

## Data Models

### Receipt Data Structure (JSON)

```json
{
  "id": "uuid-string",
  "filename": "2024-01-15_1430_walmart.json",
  "store": "Walmart",
  "datetime": "2024-01-15T14:30:00",
  "processed_at": "2024-01-15T15:00:00",
  "verified": false,
  "raw_ocr_text": "original OCR output...",
  "items": [
    {
      "raw_name": "GV MLK 2%",
      "quantity": 1,
      "unit": "ea",
      "price": 3.49,
      "guessed_name": "Great Value Milk 2%",
      "confidence": 0.92,
      "confirmed_name": null
    }
  ],
  "total": 45.67
}
```

### Corrections Data Structure (corrections.json)

```json
{
  "GV MLK 2%|Walmart": "Great Value Milk 2%",
  "BNS CHKN BRST|Costco": "Boneless Chicken Breast"
}
```

## API Integrations

### Mistral OCR API

- **Purpose**: Extract text from receipt images
- **Endpoint**: Provided by user at runtime (store in config)
- **Input**: Base64 encoded image or image URL
- **Output**: Structured text or raw OCR text
- **Service file**: `bot/services/ocr.py`

Example integration pattern:
```python
async def process_image(self, image_bytes: bytes) -> str:
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    response = await self.client.post(
        self.endpoint,
        headers={"Authorization": f"Bearer {self.api_key}"},
        json={"image": base64_image, "model": "mistral-ocr"}
    )
    return response.json()["text"]
```

### OpenRouter API

- **Purpose**: Guess full product names from abbreviated receipt text
- **Endpoint**: https://openrouter.ai/api/v1/chat/completions
- **Models**: Use cost-effective models like `mistralai/mistral-7b-instruct` or `anthropic/claude-3-haiku`
- **Service file**: `bot/services/guesser.py`

Example prompt structure:
```
You are a grocery item identifier. Given an abbreviated item name from a store receipt, 
guess the full product name.

Store: {store_name}
Abbreviated name: {raw_name}

Respond in JSON format only:
{"product_name": "Full Product Name", "confidence": 0.85}
```

### Google Sheets API

- **Purpose**: Sync expense data to a spreadsheet
- **Auth**: Service account with JSON credentials
- **Library**: gspread
- **Service file**: `bot/services/sheets.py`

Expected spreadsheet columns:
| Date | Store | Item | Quantity | Price | Category |
|------|-------|------|----------|-------|----------|

## Discord Commands

### Receipt Commands (`/receipt`)

| Command | Description | Parameters |
|---------|-------------|------------|
| `/receipt process` | Upload and OCR a receipt image | `image: Attachment` |
| `/receipt list` | List all processed receipts | None |
| `/receipt show` | Display a specific receipt | `filename: str` |
| `/receipt delete` | Delete a receipt | `filename: str` |
| `/receipt verify` | Mark receipt as verified | `filename: str` |

### Guess Commands (`/guess`)

| Command | Description | Parameters |
|---------|-------------|------------|
| `/guess process` | Run AI guessing on a receipt | `filename: str` |
| `/guess correct` | Manually correct an item name | `raw_name: str, store: str, actual_name: str` |
| `/guess mappings` | Show all learned corrections | None |
| `/guess clear` | Clear a specific mapping | `raw_name: str, store: str` |

### Clerk Commands (`/clerk`)

| Command | Description | Parameters |
|---------|-------------|------------|
| `/clerk sync` | Sync all verified receipts to Google Sheets | None |
| `/clerk spent` | Query spending on a product | `product: str, month: Optional[str]` |
| `/clerk monthly` | Get monthly expense summary | `month: Optional[str]` (YYYY-MM format) |
| `/clerk report` | Generate expense report | `start_date: str, end_date: str` |

### Utility Commands

| Command | Description |
|---------|-------------|
| `/ping` | Check bot responsiveness |
| `/help` | Show available commands |
| `/process_full` | Full pipeline: OCR → Guess → Sync |

## Environment Variables

Required in `.env` file:

```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_server_id  # Optional: for faster command sync during dev

# Mistral OCR
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_OCR_ENDPOINT=https://api.mistral.ai/v1/ocr  # Or custom endpoint

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=mistralai/mistral-7b-instruct  # Or preferred model

# Google Sheets
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id

# Application Settings
CONFIDENCE_THRESHOLD=0.7  # Below this, ask user for correction
DATA_DIR=data
LOG_LEVEL=INFO
```

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot locally
python -m bot.main

# Run with auto-reload (development)
# Use watchdog or similar if needed

# Run tests
pytest tests/ -v

# Format code
black bot/ tests/
isort bot/ tests/

# Type checking
mypy bot/
```

## Key Implementation Notes

### Receipt Parsing Strategy

The OCR output varies by store. Implement flexible parsing:

1. Look for common patterns: date formats, currency symbols, "TOTAL"
2. Items usually follow pattern: `ITEM_NAME    QTY    PRICE`
3. Store name often at top of receipt
4. Handle multi-line item names

```python
def parse_receipt(ocr_text: str) -> dict:
    lines = ocr_text.strip().split('\n')
    # First few lines usually contain store name
    # Look for date patterns: MM/DD/YY, YYYY-MM-DD, etc.
    # Items section between header and total
    # Total line contains "TOTAL", "SUBTOTAL", etc.
```

### Confidence Threshold Logic

```python
CONFIDENCE_THRESHOLD = 0.7

async def process_item(item: dict, corrections: dict) -> dict:
    key = f"{item['raw_name']}|{store}"
    
    # Check corrections first
    if key in corrections:
        item['guessed_name'] = corrections[key]
        item['confidence'] = 1.0
        return item
    
    # Call AI
    result = await guesser.guess(item['raw_name'], store)
    item['guessed_name'] = result['product_name']
    item['confidence'] = result['confidence']
    
    # Flag for user review if low confidence
    if result['confidence'] < CONFIDENCE_THRESHOLD:
        item['needs_review'] = True
    
    return item
```

### Error Handling Patterns

```python
# Always wrap API calls
try:
    result = await self.ocr_service.process(image_bytes)
except httpx.HTTPError as e:
    await interaction.followup.send(f"OCR service error: {e}")
    return
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    await interaction.followup.send("An unexpected error occurred. Please try again.")
    return
```

### Discord Interaction Patterns

```python
# Always defer for long operations
@app_commands.command()
async def process(self, interaction: discord.Interaction, image: discord.Attachment):
    await interaction.response.defer()  # Gives 15 minutes instead of 3 seconds
    
    # ... long operation ...
    
    await interaction.followup.send("Done!")

# Use embeds for rich formatting
embed = discord.Embed(title="Receipt Processed", color=0x00ff00)
embed.add_field(name="Store", value=receipt['store'])
embed.add_field(name="Total", value=f"${receipt['total']:.2f}")
await interaction.followup.send(embed=embed)
```

## Testing Guidelines

### Unit Tests

```python
# tests/test_storage.py
def test_save_and_load_receipt():
    receipt = {"store": "Test", "items": [], "datetime": "2024-01-01"}
    filename = save_receipt(receipt)
    loaded = load_receipt(filename)
    assert loaded["store"] == "Test"

# tests/test_guesser.py
@pytest.mark.asyncio
async def test_guess_with_correction():
    guesser = ItemGuesser(api_key="test")
    guesser.corrections = {"GV MLK|Walmart": "Great Value Milk"}
    result = await guesser.guess("GV MLK", "Walmart")
    assert result["confidence"] == 1.0
```

### Integration Tests

```python
# Test full flow with mock APIs
@pytest.mark.asyncio
async def test_full_receipt_flow():
    # Mock OCR response
    # Mock OpenRouter response
    # Verify receipt saved correctly
    # Verify corrections updated
```

## Common Issues and Solutions

### Issue: Slash commands not appearing
- **Solution**: Ensure `bot.tree.sync()` is called in `on_ready`
- For guild-specific sync (faster): `bot.tree.sync(guild=discord.Object(id=GUILD_ID))`

### Issue: OCR returning garbled text
- **Solution**: Preprocess image (resize, increase contrast) before sending to API
- Consider using Pillow for image preprocessing

### Issue: Rate limiting from APIs
- **Solution**: Implement exponential backoff
- Cache corrections aggressively
- Batch API calls where possible

### Issue: Google Sheets auth failing
- **Solution**: Ensure service account has editor access to spreadsheet
- Check credentials.json path is correct
- Verify GOOGLE_SPREADSHEET_ID is the ID from the URL, not the full URL

## Development Milestones

### Milestone 1: Core Infrastructure ✅
**Goal**: Establish basic bot infrastructure and receipt processing capabilities

- [x] **Project Setup** - Directory structure, git, dependencies
- [x] **Configuration Management** - Environment variables with pydantic-settings
- [x] **Discord Bot Skeleton** - Bot initialization, command tree setup
- [x] **Data Models** - Pydantic models for Receipt, ReceiptItem, GuessResult
- [x] **JSON Storage Layer** - CRUD operations for receipts and corrections
- [x] **Mistral OCR Service Integration** - Async OCR API client
- [x] **Receipt Parsing Logic** - Basic parsing of OCR text into structured data
- [x] **Receipt Commands Implementation** - `/receipt process`, `list`, `show`, `verify`, `delete`

**Status**: 7/8 Complete (87.5%)
**Remaining**: Receipt parsing enhancement for multiple store formats

### Milestone 2: Item Guessing ✅
**Goal**: AI-powered item name identification with learning system

- [x] **OpenRouter Service Integration** - AI API client with prompt engineering
- [x] **Corrections Cache System** - Store and retrieve user corrections
- [x] **Guess Commands Implementation** - `/guess process`, `correct`, `mappings`, `clear`
- [x] **User Correction Flow** - Basic correction workflow

**Status**: 4/4 Complete (100%)
**Enhancement Opportunity**: Interactive buttons/modals for better UX

### Milestone 3: Clerk Bot ✅
**Goal**: Expense aggregation and Google Sheets synchronization

- [x] **Google Sheets Service Setup** - gspread integration with service account
- [x] **Receipt Data Sync to Sheets** - Batch sync of verified receipts
- [x] **Data Aggregation Functions** - Basic spending queries
- [x] **Clerk Commands Implementation** - `/clerk sync`, `spent`, `monthly`, `report`

**Status**: 4/4 Complete (100%)
**Enhancement Opportunity**: Advanced analytics and visualizations

### Milestone 4: Integration & Polish ⚠️
**Goal**: Full pipeline integration, testing, and production readiness

- [ ] **Full Pipeline Command** - `/process_full` for OCR → Guess → Verify → Sync
- [ ] **Error Handling Improvements** - Comprehensive error handling and retry logic
- [ ] **Response Formatting** - Enhanced embeds, pagination, confirmations
- [ ] **Documentation Update** - Complete API docs, user guide, deployment guide
- [ ] **Deployment Setup** - Docker, systemd, cloud platform configs
- [ ] **Comprehensive Testing** - Unit tests, integration tests, mocks, CI/CD

**Status**: 0/6 Complete (0%)
**Priority**: HIGH - Required for production deployment

## Feature Development Tracker

### Current Sprint Focus
1. **Full Pipeline Command** (HIGH PRIORITY)
   - Single command for complete workflow
   - Progress indicators during processing
   - Interactive review for low-confidence items

2. **Error Handling** (HIGH PRIORITY)
   - Retry logic with exponential backoff
   - Rate limit handling
   - User-friendly error messages

3. **Deployment Setup** (HIGH PRIORITY)
   - Dockerization
   - Cloud platform deployment guides

### Backlog (Medium Priority)
- Receipt parsing enhancement for multiple formats
- Interactive correction flow with buttons/modals
- Advanced data aggregation and analytics
- Response formatting improvements
- Comprehensive testing suite
- Complete documentation

### Development Workflow
1. Pick an issue from GitHub
2. Create feature branch: `feature/issue-name`
3. Implement with tests
4. Submit PR with description
5. Review and merge to main

## Future Enhancements (v2)

- [ ] SQLite/PostgreSQL database for better querying
- [ ] Interactive Discord buttons for verification flow
- [ ] Receipt image preprocessing pipeline
- [ ] Category auto-detection for items
- [ ] Budget tracking and alerts
- [ ] Multi-user support with separate data
- [ ] Receipt duplicate detection
- [ ] Export to CSV/Excel
- [ ] Spending visualizations/charts

## File Naming Conventions

- Receipt files: `{YYYY-MM-DD}_{HHMM}_{store_lowercase}.json`
- Use snake_case for Python files
- Use kebab-case for any shell scripts
- Models use PascalCase class names

## Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for public methods
- Max line length: 100 characters
- Use `async`/`await` consistently for I/O operations

## Dependencies (requirements.txt)

```
discord.py>=2.3.0
httpx>=0.25.0
gspread>=5.12.0
google-auth>=2.23.0
Pillow>=10.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0
mypy>=1.7.0
```