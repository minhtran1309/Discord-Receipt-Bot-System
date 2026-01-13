"""Migration script to add synced_to_sheets field to existing receipts."""

import json
from pathlib import Path

data_dir = Path("data/receipts")
receipt_files = sorted(data_dir.glob("*.json"))

print("=" * 60)
print("Receipt Sync Status Migration")
print("=" * 60)
print(f"Found {len(receipt_files)} receipt files\n")

# Ask user how to handle existing receipts
print("How should existing receipts be marked?")
print("1. Mark as NOT synced (synced_to_sheets=False)")
print("   - Use if you haven't synced receipts yet OR want to re-sync all")
print("   - WARNING: May create duplicates if already synced")
print()
print("2. Mark as SYNCED (synced_to_sheets=True)")
print("   - Use if you've already synced receipts to Google Sheets")
print("   - Prevents duplicates but won't re-sync existing data")
print()

while True:
    choice = input("Enter choice (1 or 2): ").strip()
    if choice in ["1", "2"]:
        break
    print("Invalid choice. Please enter 1 or 2.")

mark_as_synced = (choice == "2")
print()
print(f"Will mark receipts as: synced_to_sheets={mark_as_synced}")
print()

updated = 0
skipped = 0

for receipt_file in receipt_files:
    # Skip non-JSON files
    if not receipt_file.name.endswith(".json"):
        continue

    try:
        with open(receipt_file, "r") as f:
            data = json.load(f)

        # Check if field already exists
        if "synced_to_sheets" in data:
            skipped += 1
            print(f"⊘ Skipped (already has field): {receipt_file.name}")
            continue

        # Add synced_to_sheets field
        data["synced_to_sheets"] = mark_as_synced

        with open(receipt_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        updated += 1
        status = "✅ SYNCED" if mark_as_synced else "⏳ NOT SYNCED"
        print(f"✓ Updated [{status}]: {receipt_file.name}")

    except Exception as e:
        print(f"✗ Error updating {receipt_file.name}: {e}")

print()
print("=" * 60)
print("Migration Complete!")
print("=" * 60)
print(f"Updated: {updated} receipts")
print(f"Skipped: {skipped} receipts (already had synced_to_sheets field)")
print(f"Total: {len(receipt_files)} receipt files")
print()

if mark_as_synced:
    print("✅ All receipts marked as SYNCED.")
    print("   Next `/clerk sync` will only sync NEW verified receipts.")
else:
    print("⏳ All receipts marked as NOT SYNCED.")
    print("   Next `/clerk sync` will sync all verified receipts.")
    if updated > 0:
        print("   ⚠️  WARNING: If you already synced these receipts to Google")
        print("               Sheets, this will create DUPLICATE entries!")
        print()
        print("   To avoid duplicates, manually delete rows from Google Sheets")
        print("   before running `/clerk sync`, or re-run this script with option 2.")
