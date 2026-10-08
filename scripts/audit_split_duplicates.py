from pathlib import Path
from collections import defaultdict
import hashlib

root = Path("data/clean_split_v2")

hashes = defaultdict(list)

for path in sorted(root.rglob("*.jpg")):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    relative = path.relative_to(root)
    split = relative.parts[0]
    hashes[digest].append((split, str(relative)))

duplicate_groups = {
    digest: locations
    for digest, locations in hashes.items()
    if len(locations) > 1
}

cross_split_groups = {
    digest: locations
    for digest, locations in duplicate_groups.items()
    if len({location[0] for location in locations}) > 1
}

print(f"Total files: {sum(len(v) for v in hashes.values())}")
print(f"Unique SHA-256 hashes: {len(hashes)}")
print(f"Duplicate hash groups: {len(duplicate_groups)}")
print(f"Cross-split duplicate groups: {len(cross_split_groups)}")

if duplicate_groups:
    print()
    print("===== DUPLICATE GROUPS =====")
    for digest, locations in duplicate_groups.items():
        print(f"{digest}")
        for split, path in locations:
            print(f"  [{split}] {path}")
