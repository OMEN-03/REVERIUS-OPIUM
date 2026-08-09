from collections import Counter
from pathlib import Path
path = Path('REVERIUS_OPIUM.py')
text = path.read_text(encoding='utf-8', errors='replace').splitlines()
counts = Counter(text)
for line, count in counts.most_common():
    if line.strip() and count > 1:
        print(f'{count}: {line}')
