import re

line = "1L BEAT A BUG RTU CB80010 $14.03"
skip_keywords = [
    "total", "subtotal", "amount", "change", "rounding",
    "gst", "tax", "card", "eft", "credit", "debit",
    "sales", "payment", "net", "cash"
]

matches = re.findall(r'(.+?)\s+\$?(\d+\.\d{2})', line)
if matches:
    name, price = matches[0]
    price_float = float(price)

    print(f'Line: {line}')
    print(f'Name: "{name.strip()}"')
    print(f'Price: {price_float}')
    print()

    # Test 1: Price check
    if price_float <= 0:
        print('✗ FILTERED: Price <= 0')
    else:
        print('✓ PASS: Price > 0')

    # Test 2: Skip keywords
    if any(keyword in line.lower() for keyword in skip_keywords):
        print('✗ FILTERED: Contains skip keyword')
        matching_keywords = [kw for kw in skip_keywords if kw in line.lower()]
        print(f'  Matching keywords: {matching_keywords}')
    else:
        print('✓ PASS: No skip keywords')

    # Test 3: Date pattern
    if re.search(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}', line):
        print('✗ FILTERED: Contains date pattern')
    else:
        print('✓ PASS: No date pattern')

    # Test 4: Transaction pattern
    if re.search(r'^[*#]\d+|REF|TRANS|TERMINAL', line, re.IGNORECASE):
        print('✗ FILTERED: Contains transaction pattern')
    else:
        print('✓ PASS: No transaction pattern')
