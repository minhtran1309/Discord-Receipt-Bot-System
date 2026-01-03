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

lines = [line.strip() for line in bunnings_ocr_text.strip().split("\n") if line.strip()]

skip_keywords = [
    "total", "subtotal", "amount", "change", "rounding",
    "gst", "tax", "card", "eft", "credit", "debit",
    "sales", "payment", "net", "cash"
]

print("Looking for items with prices:")
print("=" * 70)

for idx, line in enumerate(lines):
    matches = re.findall(r'(.+?)\s+\$?(\d+\.\d{2})', line)
    if matches:
        name, price = matches[0]
        price_float = float(price)

        # Skip if price is 0 or negative
        if price_float <= 0:
            print(f"Line {idx}: SKIP - price <= 0")
            continue

        # Skip lines containing common non-item keywords
        if any(keyword in line.lower() for keyword in skip_keywords):
            print(f"Line {idx}: SKIP - keyword ({[kw for kw in skip_keywords if kw in line.lower()]})")
            continue

        # Skip lines that look like dates
        if re.search(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}', line):
            print(f"Line {idx}: SKIP - date pattern")
            continue

        # Skip transaction codes
        if re.search(r'^[*#]\d+|REF|TRANS|TERMINAL', line, re.IGNORECASE):
            print(f"Line {idx}: SKIP - transaction pattern")
            continue

        print(f"Line {idx}: ACCEPT - \"{name.strip()}\" = ${price_float:.2f}")
        print(f"  Full line: {line}")
