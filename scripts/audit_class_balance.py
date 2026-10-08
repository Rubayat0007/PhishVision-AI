from pathlib import Path
from collections import Counter

root = Path("data/clean_split_v2")

print("Split      Legit   Phishing   Total   Legit%   Phishing%")
print("-" * 58)

for split in ["train", "val", "test"]:
    files = list((root / split).rglob("*.jpg"))
    counts = Counter(path.parent.name for path in files)

    legit = counts["legitimate"]
    phishing = counts["phishing"]
    total = legit + phishing

    legit_pct = legit / total * 100
    phishing_pct = phishing / total * 100

    print(
        f"{split:<10}"
        f"{legit:>7}"
        f"{phishing:>11}"
        f"{total:>8}"
        f"{legit_pct:>9.2f}%"
        f"{phishing_pct:>11.2f}%"
    )
