"""Test script to debug clerk sync functionality."""

import os
import sys

# Add bot directory to path
sys.path.insert(0, os.path.dirname(__file__))

from bot.services.sheets import SheetsService
from bot.storage import Storage

# Read .env file manually
env_vars = {}
try:
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip().strip("'\"")
except FileNotFoundError:
    print("ERROR: .env file not found!")
    exit(1)

# Initialize services
credentials_path = env_vars.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
spreadsheet_id = env_vars.get("GOOGLE_SPREADSHEET_ID")
data_dir = env_vars.get("DATA_DIR", "data")

print("=" * 60)
print("Clerk Sync Test")
print("=" * 60)
print(f"Credentials path: {credentials_path}")
print(f"Spreadsheet ID: {spreadsheet_id}")
print(f"Data directory: {data_dir}")
print()

# Initialize storage
storage = Storage(data_dir)

# List all receipts
print("Loading receipts...")
filenames = storage.list_receipts()
print(f"Found {len(filenames)} receipt files")
print()

# Find verified receipts
verified_receipts = []
verified_synced = []
unverified_receipts = []

for filename in filenames:
    receipt = storage.load_receipt(filename)
    if receipt:
        if receipt.verified and not receipt.synced_to_sheets:
            verified_receipts.append(receipt)
            print(f"✓ VERIFIED (not synced): {filename}")
            print(f"  Store: {receipt.store}")
            print(f"  Date: {receipt.datetime.strftime('%Y-%m-%d')}")
            print(f"  Items: {len(receipt.items)}")
        elif receipt.verified and receipt.synced_to_sheets:
            verified_synced.append(receipt)
            print(f"↻ VERIFIED (already synced): {filename}")
        else:
            unverified_receipts.append(receipt)
            print(f"✗ UNVERIFIED: {filename}")

print()
print(f"Total verified (not synced): {len(verified_receipts)}")
print(f"Total verified (already synced): {len(verified_synced)}")
print(f"Total unverified: {len(unverified_receipts)}")
print()

if not verified_receipts:
    if verified_synced:
        print("✅ All verified receipts are already synced!")
        print(f"   {len(verified_synced)} receipts have been synced previously.")
        print()
        print("To test the sync again, you can:")
        print("1. Verify more receipts with: `/receipt verify <filename>`")
        print("2. Or re-run migration script with option 1 to mark all as unsynced")
    else:
        print("❌ No verified receipts found!")
        print("Use `/receipt verify <filename>` in Discord to verify receipts first.")
    exit(0)

# Try to sync
print("=" * 60)
print("Attempting to sync verified receipts to Google Sheets...")
print("=" * 60)
print()

try:
    sheets_service = SheetsService(credentials_path, spreadsheet_id)
    count = sheets_service.sync_multiple(verified_receipts)
    print()
    print("=" * 60)
    print(f"✅ SUCCESS! Synced {count} receipts to Google Sheets")
    print("=" * 60)
except Exception as e:
    import traceback
    print()
    print("=" * 60)
    print("❌ ERROR!")
    print("=" * 60)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print()
    print("Full traceback:")
    print(traceback.format_exc())
    print()

    # Additional debugging info
    if "404" in str(e):
        print("🔍 Debugging 404 Error:")
        print("1. Check that GOOGLE_SPREADSHEET_ID is correct in .env")
        print(f"   Current ID: {spreadsheet_id}")
        print("2. Verify the spreadsheet exists at:")
        print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        print("3. Ensure the service account has Editor access to the spreadsheet")
        print(f"   Service account email is in credentials.json under 'client_email'")
    elif "403" in str(e):
        print("🔍 Debugging 403 Error:")
        print("1. The service account doesn't have permission to access the spreadsheet")
        print("2. Open your Google Sheet and click 'Share'")
        print("3. Add the service account email (from credentials.json)")
        print("4. Set permission to 'Editor'")
