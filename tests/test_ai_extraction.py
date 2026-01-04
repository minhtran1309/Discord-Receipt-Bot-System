"""Test AI-powered structured extraction from OCR text using OpenRouter."""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os
import httpx

# Load environment variables
load_dotenv()


async def extract_receipt_data_with_ai(ocr_text: str, api_key: str, model: str = "openai/gpt-4o-mini") -> dict:
    """Use AI to extract structured data from OCR text.

    Args:
        ocr_text: Raw OCR markdown text
        api_key: OpenRouter API key
        model: Model to use for extraction

    Returns:
        Extracted receipt data as dict
    """
    prompt = f"""You are a receipt data extractor. Analyze this OCR text from a grocery receipt and extract structured data.

OCR Text:
{ocr_text}

Extract the following information in JSON format:
- store_name: Store name from header
- store_location: Store branch or address (if visible)
- date: Transaction date in YYYY-MM-DD format
- time: Transaction time in HH:MM format (if visible)
- items: Array of items, each with:
  - raw_name: Full item name (combine multi-line names)
  - quantity: Quantity purchased (default 1.0)
  - unit: Unit type (ea, kg, g, L, ml, etc., default "ea")
  - price: Item price as shown (final price after discount)
  - discount: Discount amount from separate column (0 if none)
  - sku: Product SKU/barcode if visible
- subtotal: Subtotal before tax (if shown)
- tax: Tax amount (GST, VAT, sales tax)
- discount_total: Total discount amount (if shown)
- total: Final total amount
- payment_method: Payment method used (if visible)

Important:
1. For multi-line items, combine them into a single raw_name
2. Extract units (kg, g, L, ml) separately from item names
3. Price should be the final price customer pays
4. Discount is a separate field (0 if no discount column)
5. Preserve original language for item names (Korean, Chinese, etc.)

Return ONLY valid JSON, no markdown formatting."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
        )

        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

        result = response.json()
        extracted_json = result["choices"][0]["message"]["content"]
        return json.loads(extracted_json)


async def test_ai_extraction():
    """Test AI extraction on existing OCR outputs."""
    print("\n" + "="*80)
    print("AI-POWERED STRUCTURED EXTRACTION TEST")
    print("="*80)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in environment")
        return

    # Find OCR output files
    output_dir = Path("data/test_output")
    ocr_files = sorted(output_dir.glob("*_ocr.txt"))

    if not ocr_files:
        print(f"❌ No OCR output files found in {output_dir}")
        return

    print(f"\n📁 Found {len(ocr_files)} OCR output(s) to process\n")

    results = []

    for ocr_file in ocr_files:
        print(f"{'='*80}")
        print(f"Processing: {ocr_file.name}")
        print(f"{'='*80}")

        # Read OCR text
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()

        print(f"📄 OCR text length: {len(ocr_text)} chars")

        result = {
            "filename": ocr_file.stem.replace("_ocr", ""),
            "ocr_file": ocr_file.name,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "extracted_data": None
        }

        try:
            # Extract with AI
            print("🤖 Extracting structured data with AI...")
            extracted = await extract_receipt_data_with_ai(ocr_text, api_key)

            result["success"] = True
            result["extracted_data"] = extracted

            # Display results
            print(f"\n✅ Extraction successful!")
            print(f"\n📋 Extracted Data:")
            print(f"  Store: {extracted.get('store_name', 'N/A')}")
            if extracted.get('store_location'):
                print(f"  Location: {extracted['store_location']}")
            print(f"  Date: {extracted.get('date', 'N/A')} {extracted.get('time', '')}")
            print(f"  Total: ${extracted.get('total', 0):.2f}")

            items = extracted.get('items', [])
            print(f"  Items: {len(items)}")

            if extracted.get('subtotal'):
                print(f"  Subtotal: ${extracted['subtotal']:.2f}")
            if extracted.get('tax'):
                print(f"  Tax: ${extracted['tax']:.2f}")
            if extracted.get('discount_total'):
                print(f"  Discount: ${extracted['discount_total']:.2f}")
            if extracted.get('payment_method'):
                print(f"  Payment: {extracted['payment_method']}")

            # Display items
            if items:
                print(f"\n📦 Items:")
                print(f"  {'#':<3} {'Name':<40} {'Qty':<6} {'Unit':<6} {'Price':<8} {'Disc':<6}")
                print(f"  {'-'*3} {'-'*40} {'-'*6} {'-'*6} {'-'*8} {'-'*6}")

                for i, item in enumerate(items, 1):
                    name = item.get('raw_name', 'N/A')
                    name = name[:38] + ".." if len(name) > 40 else name
                    qty = item.get('quantity', 1.0)
                    unit = item.get('unit', 'ea')
                    price = item.get('price', 0.0)
                    discount = item.get('discount', 0.0)
                    print(f"  {i:<3} {name:<40} {qty:<6.1f} {unit:<6} ${price:<7.2f} ${discount:<5.2f}")

            # Validation
            items_sum = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
            total = extracted.get('total', 0)

            if abs(items_sum - total) > 0.10:
                print(f"\n⚠️  Validation: Items sum (${items_sum:.2f}) != total (${total:.2f})")
            else:
                print(f"\n✅ Validation: Items sum matches total")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            result["success"] = False
            result["error"] = str(e)
            import traceback
            traceback.print_exc()

        # Save result
        result_file = output_dir / f"{result['filename']}_ai_extraction.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved to: {result_file.name}")

        results.append(result)
        print()

    # Summary
    print(f"{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful

    print(f"\n📊 Statistics:")
    print(f"  Total: {total}")
    print(f"  ✅ Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"  ❌ Failed: {failed} ({failed/total*100:.1f}%)")

    if failed > 0:
        print(f"\n❌ Failed extractions:")
        for r in results:
            if not r["success"]:
                print(f"  • {r['filename']}: {r['error']}")

    print(f"\n💾 Results saved to: {output_dir}/")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_ai_extraction())
