import re
from datetime import datetime
from bot.models import Receipt, ReceiptItem

aldi_ocr_text = """ALDI STORES
A LIMITED PARTNERSHIP
RYDALMERE
ABN: 90 196 565 019
Tax Invoice

399365 TradWmealBread750g 3.69 A
405617 EggsFreeRange 700g 6.19 A
380204 Blueberries 170g 2.29 A
403073 VanillaYogurt 990g 6.99 A
494093 YogMngBlood0rg700g 4.89 A

Total (INCL GST) $ 24.05
5 Items
Card Sales $ 24.05

A 00.0% Net 24.05 GST 0.00
*2380 G541/009/805 30.12.25 18:18

THANK YOU FOR SHOPPING AT ALDI
VISIT ALDI.COM.AU FOR TRADING HOURS

EFTPOS FROM WESTPAC
Rydalmere
CUSTOMER COPY
eftpos SAV
##########2134 (C)

ACCT TYPE SAVING
TRANS TYPE PURCHASE
TERMINAL ID 50409209
POS REF 010902380009
INV/ROC NO 002107
TRAN 023535
DATE/TIME 30DEC25 18:18

AID A00000038410
TC E8ECA58130727384
PAN SEQ NO 00
ATC 0204

AMOUNT $24.05
TOTAL AUD $24.05
AUTH 000000
APPROVED 00"""

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
print("Testing Aldi receipt parsing:")
print("=" * 60)
receipt = parse_receipt(aldi_ocr_text)
print("\n" + "=" * 60)
print(f"Receipt created successfully with {len(receipt.items)} items")
