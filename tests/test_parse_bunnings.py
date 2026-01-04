import re
from datetime import datetime
from bot.models import Receipt, ReceiptItem

bunnings_ocr_text = """# BUNNINGS warehouse

RYDALMERE
BUNNINGS GROUP LIMITED
ABN 26 008 672 179
Ph: (02) 8832 8200

Fri 02/01/2026 03:48:51 PM
SELF CHECKOUT R95

Sale
**TAX INVOICE**

3017618 INSECTICIDE GARDEN RICHURO
1L BEAT A BUG RTU CB80010 $14.03

1 @ SubTotal: $14.03

Total $14.03
GST INCLUDED IN THE TOTAL $1.28
EFT $14.03
CARD NO: 462263-134
CREDIT

Rounding $0.00
Change $0.00

"*" Indicates non taxable item(s)

$7333 R95 P478 C000001 #095-46934-7333-2026-01-02

Thank you for shopping with Bunnings
Please retain receipt for proof of purchase

SUPERCHARGE YOUR SHOP WITH ONEPASS

OnePass members get 5X Flybuys points in-store, free delivery, 365 day change of mind returns and Express Click &amp; Collect. T&amp;Cs, exclusions apply.

Start your plan from $4/mth.
Cancel anytime.

www.onepass.com.au

Have Your Say

Give us your in-store experience feedback by scanning the QR code below."""

def parse_receipt(ocr_text: str):
    """Parse OCR text into a Receipt object (basic implementation)."""
    lines = [line.strip() for line in ocr_text.strip().split("\n") if line.strip()]

    # Simple heuristics for parsing
    store = lines[0] if lines else "Unknown Store"
    total = 0.0
    items = []

    # Look for total
    for line in lines:
        if "total" in line.lower():
            # Extract price from line
            matches = re.findall(r"\$?(\d+\.\d{2})", line)
            if matches:
                total = float(matches[-1])

    print(f"Store: {store}")
    print(f"Total: {total}")
    print("\nParsing items:")

    # Basic item extraction (simplified)
    for line in lines:
        # Look for lines with prices
        matches = re.findall(r"(.+?)\s+\$?(\d+\.\d{2})", line)
        if matches and "total" not in line.lower():
            name, price = matches[0]
            print(f"  Line: {line}")
            print(f"    Raw name: '{name.strip()}'")
            print(f"    Price: {price}")

            try:
                item = ReceiptItem(raw_name=name.strip(), price=float(price))
                items.append(item)
                print(f"    ✓ Created ReceiptItem")
            except Exception as e:
                print(f"    ✗ ERROR: {e}")
                print(f"    Error type: {type(e).__name__}")
            print()

    print(f"\nTotal items parsed: {len(items)}")

    return Receipt(
        filename="",
        store=store,
        datetime=datetime.now(),
        raw_ocr_text=ocr_text,
        items=items,
        total=total,
    )

# Test parsing
print("Testing Bunnings receipt parsing:")
print("=" * 60)
try:
    receipt = parse_receipt(bunnings_ocr_text)
    print("\n" + "=" * 60)
    print(f"Receipt created successfully with {len(receipt.items)} items")
except Exception as e:
    print(f"\n✗ FAILED TO CREATE RECEIPT: {e}")
    print(f"Error type: {type(e).__name__}")
