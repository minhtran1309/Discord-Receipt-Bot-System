"""Test script to process all receipts in data/receipts folder with structured extraction."""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from bot.services.ocr import OCRService, OCRReceiptData
from bot.models import Receipt, ReceiptItem


async def process_receipt(ocr_service: OCRService, receipt_path: Path, output_dir: Path):
    """Process a single receipt and save results.

    Args:
        ocr_service: OCR service instance
        receipt_path: Path to receipt image
        output_dir: Directory to save test results
    """
    print(f"\n{'='*80}")
    print(f"Processing: {receipt_path.name}")
    print(f"{'='*80}")

    # Read image bytes
    with open(receipt_path, 'rb') as f:
        image_bytes = f.read()

    # Track results
    result = {
        "filename": receipt_path.name,
        "file_size": len(image_bytes),
        "timestamp": datetime.now().isoformat(),
        "structured_extraction_used": False,
        "fallback_to_regex": False,
        "success": False,
        "error": None,
        "ocr_raw_text": "",
        "structured_data": None,
        "validation_issues": []
    }

    try:
        # Process with structured extraction
        print("🔍 Running OCR with structured extraction...")
        raw_text, structured_data = await ocr_service.process_image(
            image_bytes,
            use_structured_extraction=True
        )

        result["ocr_raw_text"] = raw_text
        result["success"] = True

        if structured_data:
            print("✅ Structured extraction succeeded!")
            result["structured_extraction_used"] = True

            # Convert to dict for JSON serialization
            result["structured_data"] = {
                "store_name": structured_data.store_name,
                "store_location": structured_data.store_location,
                "date": structured_data.date,
                "time": structured_data.time,
                "total": structured_data.total,
                "subtotal": structured_data.subtotal,
                "tax": structured_data.tax,
                "discount_total": structured_data.discount_total,
                "payment_method": structured_data.payment_method,
                "items": [
                    {
                        "raw_name": item.raw_name,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "price": item.price,
                        "discount": item.discount,
                        "sku": item.sku
                    }
                    for item in structured_data.items
                ]
            }

            # Display extracted data
            print(f"\n📋 Extracted Data:")
            print(f"  Store: {structured_data.store_name}")
            if structured_data.store_location:
                print(f"  Location: {structured_data.store_location}")
            print(f"  Date: {structured_data.date} {structured_data.time or ''}")
            print(f"  Items: {len(structured_data.items)}")
            print(f"  Total: ${structured_data.total:.2f}")
            if structured_data.subtotal:
                print(f"  Subtotal: ${structured_data.subtotal:.2f}")
            if structured_data.tax:
                print(f"  Tax: ${structured_data.tax:.2f}")
            if structured_data.discount_total:
                print(f"  Discount: ${structured_data.discount_total:.2f}")
            if structured_data.payment_method:
                print(f"  Payment: {structured_data.payment_method}")

            # Display items table
            print(f"\n📦 Items:")
            print(f"  {'#':<3} {'Name':<40} {'Qty':<6} {'Unit':<6} {'Price':<8} {'Disc':<6}")
            print(f"  {'-'*3} {'-'*40} {'-'*6} {'-'*6} {'-'*8} {'-'*6}")

            for i, item in enumerate(structured_data.items, 1):
                name = item.raw_name[:38] + ".." if len(item.raw_name) > 40 else item.raw_name
                print(f"  {i:<3} {name:<40} {item.quantity:<6.1f} {item.unit:<6} ${item.price:<7.2f} ${item.discount:<5.2f}")

            # Validate data
            items_sum = sum(item.price * item.quantity for item in structured_data.items)
            if abs(items_sum - structured_data.total) > 0.10:
                issue = f"Items sum (${items_sum:.2f}) != total (${structured_data.total:.2f})"
                result["validation_issues"].append(issue)
                print(f"\n⚠️  Validation Issue: {issue}")
            else:
                print(f"\n✅ Validation: Items sum matches total")

            if not structured_data.items:
                issue = "No items detected"
                result["validation_issues"].append(issue)
                print(f"⚠️  Validation Issue: {issue}")

        else:
            print("⚠️  Structured extraction returned None, using raw text only")
            result["fallback_to_regex"] = True

        # Save raw OCR text
        text_output_path = output_dir / f"{receipt_path.stem}_ocr.txt"
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.write(raw_text)
        print(f"\n💾 Saved raw OCR text to: {text_output_path.name}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        result["success"] = False
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()

    # Save result JSON
    json_output_path = output_dir / f"{receipt_path.stem}_result.json"
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved test result to: {json_output_path.name}")

    return result


async def main():
    """Main test function to process all receipts."""
    print("\n" + "="*80)
    print("RECEIPT PROCESSING TEST - Structured Extraction")
    print("="*80)

    # Setup paths
    receipts_dir = Path("data/receipts")
    output_dir = Path("data/test_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize OCR service
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Error: MISTRAL_API_KEY not found in environment")
        return

    ocr_service = OCRService(
        api_key=api_key,
        model=os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest")
    )

    # Find all receipt images
    receipt_files = sorted(receipts_dir.glob("*.HEIC")) + sorted(receipts_dir.glob("*.heic"))
    receipt_files += sorted(receipts_dir.glob("*.jpg")) + sorted(receipts_dir.glob("*.jpeg"))
    receipt_files += sorted(receipts_dir.glob("*.png"))

    if not receipt_files:
        print(f"❌ No receipt images found in {receipts_dir}")
        return

    print(f"\n📁 Found {len(receipt_files)} receipt(s) to process:")
    for i, f in enumerate(receipt_files, 1):
        print(f"  {i}. {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")

    # Process all receipts
    results = []
    for receipt_path in receipt_files:
        result = await process_receipt(ocr_service, receipt_path, output_dir)
        results.append(result)

    # Generate summary report
    print(f"\n{'='*80}")
    print("SUMMARY REPORT")
    print(f"{'='*80}")

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    structured = sum(1 for r in results if r["structured_extraction_used"])
    fallback = sum(1 for r in results if r["fallback_to_regex"])
    errors = sum(1 for r in results if not r["success"])

    print(f"\n📊 Statistics:")
    print(f"  Total receipts: {total}")
    print(f"  ✅ Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"  🔧 Structured extraction: {structured} ({structured/total*100:.1f}%)")
    print(f"  ⚠️  Fallback to regex: {fallback} ({fallback/total*100:.1f}%)")
    print(f"  ❌ Errors: {errors} ({errors/total*100:.1f}%)")

    if errors > 0:
        print(f"\n❌ Failed receipts:")
        for r in results:
            if not r["success"]:
                print(f"  • {r['filename']}: {r['error']}")

    # Validation issues summary
    issues_count = sum(len(r["validation_issues"]) for r in results)
    if issues_count > 0:
        print(f"\n⚠️  Validation issues found: {issues_count}")
        for r in results:
            if r["validation_issues"]:
                print(f"  • {r['filename']}:")
                for issue in r["validation_issues"]:
                    print(f"    - {issue}")

    # Save summary report
    summary_path = output_dir / f"test_summary_{datetime.now():%Y%m%d_%H%M%S}.json"
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_receipts": total,
        "successful": successful,
        "structured_extraction": structured,
        "fallback_to_regex": fallback,
        "errors": errors,
        "validation_issues_count": issues_count,
        "results": results
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Summary saved to: {summary_path}")
    print(f"💾 All outputs saved to: {output_dir}/")
    print("\n" + "="*80)
    print("✅ Test complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
