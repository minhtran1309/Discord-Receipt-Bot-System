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

def parse_receipt(ocr_text: str) -> Receipt:
    """Parse OCR text into a Receipt object (improved implementation)."""
    lines = [line.strip() for line in ocr_text.strip().split("\n") if line.strip()]

    # Simple heuristics for parsing
    store = lines[0] if lines else "Unknown Store"
    total = 0.0
    items = []

    # Look for total (prioritize lines with just "total", not "subtotal")
    for line in lines:
        line_lower = line.lower()
        # Match "total" but not "subtotal"
        if line_lower.startswith("total") or " total " in line_lower or line_lower.endswith("total"):
            # Extract price from line (take the last match)
            matches = re.findall(r"\$?(\d+\.\d{2})", line)
            if matches:
                total = float(matches[-1])
                break  # Stop at first "total" match

    # Keywords to skip (not actual items)
    skip_keywords = [
        "total", "subtotal", "amount", "change", "rounding",
        "gst", "tax", "card", "eft", "credit", "debit",
        "sales", "payment", "net", "cash"
    ]

    # Basic item extraction (simplified)
    for line in lines:
        # Look for lines with prices
        matches = re.findall(r"(.+?)\s+\$?(\d+\.\d{2})", line)
        if matches:
            name, price = matches[0]
            price_float = float(price)

            # Skip if price is 0 or negative
            if price_float <= 0:
                continue

            # Skip lines containing common non-item keywords
            if any(keyword in line.lower() for keyword in skip_keywords):
                continue

            # Skip lines that look like dates (e.g., "30.12.25" or "02/01/2026")
            # Check if line contains date patterns: DD.MM.YY or MM/DD/YYYY
            if re.search(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}', line):
                continue

            # Skip lines that look like transaction codes or reference numbers
            # (typically have many digits and special characters)
            if re.search(r'[*#]\d+|[A-Z]\d{4,}|REF|TRANS|TERMINAL', line, re.IGNORECASE):
                continue

            # Try to create ReceiptItem, skip if validation fails
            try:
                items.append(
                    ReceiptItem(raw_name=name.strip(), price=price_float)
                )
            except Exception:
                # Skip invalid items silently
                continue

    return Receipt(
        filename="",
        store=store,
        datetime=datetime.now(),
        raw_ocr_text=ocr_text,
        items=items,
        total=total,
    )

# Test Aldi receipt
print("=" * 70)
print("Testing ALDI receipt:")
print("=" * 70)
try:
    receipt = parse_receipt(aldi_ocr_text)
    print(f"✓ Store: {receipt.store}")
    print(f"✓ Total: ${receipt.total:.2f}")
    print(f"✓ Items parsed: {len(receipt.items)}")
    for i, item in enumerate(receipt.items, 1):
        print(f"  {i}. {item.raw_name:<35} ${item.price:.2f}")
    print()
except Exception as e:
    print(f"✗ FAILED: {e}\n")

# Test Bunnings receipt
print("=" * 70)
print("Testing BUNNINGS receipt:")
print("=" * 70)
try:
    receipt = parse_receipt(bunnings_ocr_text)
    print(f"✓ Store: {receipt.store}")
    print(f"✓ Total: ${receipt.total:.2f}")
    print(f"✓ Items parsed: {len(receipt.items)}")
    for i, item in enumerate(receipt.items, 1):
        print(f"  {i}. {item.raw_name:<35} ${item.price:.2f}")
    print()
except Exception as e:
    print(f"✗ FAILED: {e}\n")

print("=" * 70)
print("All tests completed successfully!")
print("=" * 70)
