from pathlib import Path
from collections import Counter
from PIL import Image

root = Path("data/clean_split_v2")
files = sorted(root.rglob("*.jpg"))

bad = []
dimensions = Counter()
modes = Counter()

for path in files:
    try:
        with Image.open(path) as image:
            image.verify()

        with Image.open(path) as image:
            image.load()
            dimensions[image.size] += 1
            modes[image.mode] += 1

    except Exception as error:
        bad.append((path, str(error)))

print(f"Total JPEG files: {len(files)}")
print(f"Unreadable/corrupt: {len(bad)}")

print()
print("Dimensions:")
for size, count in dimensions.most_common():
    print(f"  {size}: {count}")

print()
print("Image modes:")
for mode, count in modes.most_common():
    print(f"  {mode}: {count}")

if bad:
    print()
    print("===== BAD FILES =====")
    for path, error in bad:
        print(f"{path}: {error}")
