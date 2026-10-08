from pathlib import Path
from collections import defaultdict

root = Path("data/clean_split_v2")

files = sorted(root.rglob("*.jpg"))

relative_paths = [str(path.relative_to(root)) for path in files]
filenames = defaultdict(list)

for path in files:
    filenames[path.name].append(str(path.relative_to(root)))

duplicate_paths = [
    path for path, count in
    __import__("collections").Counter(relative_paths).items()
    if count > 1
]

duplicate_filenames = {
    name: paths
    for name, paths in filenames.items()
    if len(paths) > 1
}

print(f"Total files: {len(files)}")
print(f"Unique relative paths: {len(set(relative_paths))}")
print(f"Duplicate relative paths: {len(duplicate_paths)}")
print(f"Unique filenames: {len(filenames)}")
print(f"Filenames occurring in multiple locations: {len(duplicate_filenames)}")

if duplicate_filenames:
    print()
    print("===== DUPLICATE FILENAMES =====")
    for name, paths in sorted(duplicate_filenames.items()):
        print(name)
        for path in paths:
            print(f"  {path}")
