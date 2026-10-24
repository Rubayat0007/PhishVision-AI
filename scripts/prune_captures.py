"""Remove blank captures and their label rows.

A page that renders as a white rectangle (bot wall, consent gate, JS failure) is
not a legitimate page and must not become a training example. Blankness is
measured as the fraction of non-white pixels.

Dry run by default: pass --apply to delete files and rewrite labels.csv.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image

BLANK_NONWHITE = 0.005  # 0.5% of pixels


def nonwhite_fraction(path: Path) -> float:
    with Image.open(path) as handle:
        pixels = np.asarray(handle.convert("L"), dtype=np.uint8)

    if pixels.size == 0:
        return 0.0

    return float((pixels < 245).mean())


def is_blank(path: Path, threshold: float = BLANK_NONWHITE) -> bool:
    try:
        return nonwhite_fraction(path) < threshold
    except OSError:
        return True


def dedupe_labels(labels: Path, apply: bool = False) -> int:
    """Drop repeated filename rows, keeping the first occurrence."""
    if not labels.is_file():
        return 0

    with labels.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        seen: set[str] = set()
        kept: list[dict] = []

        for row in reader:
            name = row.get("filename", "")
            if name in seen:
                continue
            seen.add(name)
            kept.append(row)

    with labels.open(encoding="utf-8", newline="") as handle:
        original = sum(1 for _ in csv.DictReader(handle))

    removed = original - len(kept)

    if apply and removed:
        with labels.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept)

    return removed


def dedupe_content(captures: Path, labels: Path, apply: bool = False) -> list[str]:
    """Remove images whose bytes repeat an earlier image; keep the first.

    Returns the filenames that are duplicates (removed only when apply=True).
    """
    import hashlib

    seen: dict[str, str] = {}
    duplicates: list[str] = []

    for image in sorted(captures.glob("*.png")):
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if digest in seen:
            duplicates.append(image.name)
            if apply:
                image.unlink()
        else:
            seen[digest] = image.name

    if apply and duplicates and labels.is_file():
        with labels.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            rows = [row for row in reader if row.get("filename") not in set(duplicates)]

        with labels.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return duplicates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, default=Path("captures"))
    parser.add_argument("--labels", type=Path, default=Path("captures/labels.csv"))
    parser.add_argument("--threshold", type=float, default=BLANK_NONWHITE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dedupe", action="store_true",
                        help="also remove repeated filename rows")
    parser.add_argument("--dedupe-content", action="store_true",
                        help="remove images whose bytes repeat an earlier image")
    args = parser.parse_args()

    if args.dedupe_content:
        removed = dedupe_content(args.captures, args.labels, apply=args.apply)
        action = "removed" if args.apply else "would remove"
        print(f"byte-identical images {action}: {len(removed)}")
        for name in removed[:10]:
            print(f"  {name}")

    if args.dedupe:
        removed = dedupe_labels(args.labels, apply=args.apply)
        action = "removed" if args.apply else "would remove"
        print(f"duplicate label rows {action}: {removed}")

    blank = []

    for image in sorted(args.captures.glob("*.png")):
        fraction = nonwhite_fraction(image)
        if fraction < args.threshold:
            blank.append((image, fraction))

    print(f"scanned {len(list(args.captures.glob('*.png')))} images; "
          f"{len(blank)} blank/near-blank")

    for image, fraction in blank:
        print(f"  {image.name}: non-white {fraction:.4%}")

    if not blank:
        return 0

    if not args.apply:
        print("\ndry run: re-run with --apply to remove these images and rows")
        return 0

    names = {image.name for image, _ in blank}

    for image, _ in blank:
        image.unlink()

    if args.labels.is_file():
        with args.labels.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            rows = [row for row in reader if row.get("filename") not in names]

        with args.labels.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"removed {len(blank)} image(s) and their rows; "
              f"{len(rows)} row(s) remain")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
