import re

bunnings_text = """3017618 INSECTICIDE GARDEN RICHURO
1L BEAT A BUG RTU CB80010 $14.03"""

lines = bunnings_text.split('\n')
for line in lines:
    print(f'Line: "{line}"')
    matches = re.findall(r'(.+?)\s+\$?(\d+\.\d{2})', line)
    print(f'  Matches: {matches}')
    print()
