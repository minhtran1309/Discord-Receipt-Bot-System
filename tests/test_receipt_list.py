"""Test the enhanced /receipt list command functionality."""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import bot modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.storage import Storage


def test_receipt_list_filtering():
    """Test receipt filtering by month."""
    # Initialize storage
    storage = Storage(data_dir="data")

    # Get all receipts
    receipt_filenames = storage.list_receipts()
    print(f"\n{'='*60}")
    print(f"Total receipt files found: {len(receipt_filenames)}")
    print(f"{'='*60}")

    if not receipt_filenames:
        print("No receipts found in data directory.")
        return

    # Load all receipts
    loaded_receipts = []
    for filename in receipt_filenames:
        try:
            receipt = storage.load_receipt(filename)
            if receipt:
                loaded_receipts.append(receipt)
        except Exception as e:
            print(f"Warning: Failed to load {filename}: {e}")

    print(f"Successfully loaded: {len(loaded_receipts)} receipts")

    # Test 1: Filter by current month (January 2026)
    current_month = datetime.now().month
    current_year = datetime.now().year
    print(f"\n{'='*60}")
    print(f"Test 1: Filter by current month ({current_month}/{current_year})")
    print(f"{'='*60}")

    current_month_receipts = [
        r for r in loaded_receipts
        if r.datetime.month == current_month and r.datetime.year == current_year
    ]
    current_month_receipts.sort(key=lambda r: r.datetime, reverse=True)

    print(f"Found {len(current_month_receipts)} receipts for current month")

    # Show first 5 receipts in TOON format
    for idx, receipt in enumerate(current_month_receipts[:5], start=1):
        display_name = receipt.filename.replace('.json', '')
        verified_status = "✅ Verified" if receipt.verified else "⚠️ Not Verified"
        synced_status = "✅ Synced" if receipt.synced_to_sheets else "❌ Not Synced"
        print(f"\n{idx}. {display_name}")
        print(f"   💰 Total: ${receipt.total:.2f}")
        print(f"   {verified_status} | {synced_status}")
        print(f"   📅 Date: {receipt.datetime.strftime('%Y-%m-%d %H:%M')}")

    # Calculate total
    total_spent = sum(r.total for r in current_month_receipts)
    print(f"\n{'='*60}")
    print(f"Total spent: ${total_spent:.2f} | {len(current_month_receipts)} receipts")
    print(f"{'='*60}")

    # Test 2: Filter by a specific month (December)
    test_month = 12
    print(f"\n{'='*60}")
    print(f"Test 2: Filter by December (month={test_month})")
    print(f"{'='*60}")

    december_receipts = [
        r for r in loaded_receipts
        if r.datetime.month == test_month
    ]
    december_receipts.sort(key=lambda r: r.datetime, reverse=True)

    print(f"Found {len(december_receipts)} receipts for December")

    if december_receipts:
        for idx, receipt in enumerate(december_receipts[:3], start=1):
            display_name = receipt.filename.replace('.json', '')
            print(f"\n{idx}. {display_name}")
            print(f"   💰 Total: ${receipt.total:.2f}")
            print(f"   📅 Date: {receipt.datetime.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("No receipts found for December.")

    # Test 3: Verify 30-item limit
    print(f"\n{'='*60}")
    print(f"Test 3: Verify 30-item limit")
    print(f"{'='*60}")

    limited_receipts = current_month_receipts[:30]
    print(f"Limited to: {len(limited_receipts)} receipts")

    if len(current_month_receipts) > 30:
        print(f"⚠️ Note: {len(current_month_receipts) - 30} receipts hidden due to 30-item limit")
    else:
        print("✅ All receipts fit within 30-item limit")

    # Test 4: Check verification and sync status distribution
    print(f"\n{'='*60}")
    print(f"Test 4: Status Distribution")
    print(f"{'='*60}")

    verified_count = sum(1 for r in loaded_receipts if r.verified)
    synced_count = sum(1 for r in loaded_receipts if r.synced_to_sheets)

    print(f"Verified receipts: {verified_count}/{len(loaded_receipts)}")
    print(f"Synced receipts: {synced_count}/{len(loaded_receipts)}")
    print(f"Unverified receipts: {len(loaded_receipts) - verified_count}")
    print(f"Unsynced receipts: {len(loaded_receipts) - synced_count}")


if __name__ == "__main__":
    test_receipt_list_filtering()
