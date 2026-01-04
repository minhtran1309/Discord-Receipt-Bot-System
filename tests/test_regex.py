import re

# Test with Aldi receipt format
aldi_lines = [
    '399365 TradWmealBread750g 3.69 A',
    '405617 EggsFreeRange 700g 6.19 A',
    '380204 Blueberries 170g 2.29 A',
]

print('Testing Aldi format with current regex:')
print('Pattern: r"(.+?)\\s+\\$?(\\d+\\.\\d{2})"')
print()

for line in aldi_lines:
    matches = re.findall(r'(.+?)\s+\$?(\d+\.\d{2})', line)
    print(f'Line: {line}')
    print(f'Matches: {matches}')
    if matches:
        name, price = matches[0]
        print(f'  Name: "{name.strip()}"')
        print(f'  Price: {price}')
    else:
        print('  NO MATCH!')
    print()

# Test with improved regex
print('\n' + '='*60)
print('Testing with improved regex:')
print('Pattern: r"(.+?)\\s*\\$?(\\d+\\.\\d{2})"')
print()

for line in aldi_lines:
    matches = re.findall(r'(.+?)\s*\$?(\d+\.\d{2})', line)
    print(f'Line: {line}')
    print(f'Matches: {matches}')
    if matches:
        # Take the last match (in case there are multiple prices)
        name, price = matches[-1]
        print(f'  Name: "{name.strip()}"')
        print(f'  Price: {price}')
    else:
        print('  NO MATCH!')
    print()
