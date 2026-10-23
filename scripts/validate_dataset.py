"""Validate a local class-folder dataset and record a reproducible manifest.

Structure: <root>/<split>/<class>/<image>, with splits discovered as the
immediate subdirectories of the root (train/validation/test by convention).

Checks: presence of both classes per split, corrupt images, duplicate
content anywhere in the dataset (reported as cross-split leakage when the
duplicates straddle splits), and filename collisions.

Exit codes: 0 valid, 1 validation failures, 2 input/output error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, UnidentifiedImageError

CLASS_NAMES = ("legitimate", "phishing")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_splits(root: Path) -> list[Path]:
    if not root.is_dir():
        raise FileNotFoundError(f"dataset root not found: {root}")
    splits = sorted(
        child for child in root.iterdir() if child.is_dir() and not child.name.startswith(".")
    )
    if not splits:
        raise ValueError(f"no split directories under {root}")
    return splits


def inspect_image(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.load()
    except (UnidentifiedImageError, OSError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def validate(root: Path) -> dict:
    errors: list[str] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    filenames: dict[str, list[str]] = defaultdict(list)
    corrupt: list[str] = []
    splits_report: dict[str, dict[str, int]] = {}

    for split_dir in discover_splits(root):
        split = split_dir.name
        counts: dict[str, int] = {}

        for class_name in CLASS_NAMES:
            class_dir = split_dir / class_name
            if not class_dir.is_dir():
                errors.append(f"{split}: missing class directory '{class_name}'")
                counts[class_name] = 0
                continue

            images = sorted(
                path for path in class_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            )
            counts[class_name] = len(images)

            if not images:
                errors.append(f"{split}/{class_name}: no images found")

            for image_path in images:
                relative = image_path.relative_to(root).as_posix()
                filenames[image_path.name].append(relative)
                hashes[file_sha256(image_path)].append(relative)

                problem = inspect_image(image_path)
                if problem is not None:
                    corrupt.append(relative)
                    errors.append(f"{relative}: corrupt image ({problem})")

        splits_report[split] = counts

    duplicates = {digest: paths for digest, paths in hashes.items() if len(paths) > 1}

    leakage = []
    for paths in duplicates.values():
        splits = {path.split("/", 1)[0] for path in paths}
        if len(splits) > 1:
            leakage.append(sorted(paths))
    if leakage:
        errors.append(f"{len(leakage)} duplicate image(s) cross split boundaries")

    collisions = {name: paths for name, paths in filenames.items() if len(paths) > 1}
    if collisions:
        errors.append(f"{len(collisions)} filename collision(s)")

    totals = {
        class_name: sum(split.get(class_name, 0) for split in splits_report.values())
        for class_name in CLASS_NAMES
    }

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_root": str(root),
        "splits": splits_report,
        "totals": {**totals, "images": sum(totals.values())},
        "cross_split_duplicates": leakage,
        "identical_content": duplicates,
        "filename_collisions": collisions,
        "corrupt_files": corrupt,
        "valid": not errors,
        "errors": errors,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="dataset root containing <split>/<class>/<image>")
    parser.add_argument("--json-output", type=Path, help="write the manifest to this path")
    args = parser.parse_args(argv)

    try:
        report = validate(args.root.expanduser().resolve())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, sort_keys=True)

    if args.json_output:
        try:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(text + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot write manifest: {exc}", file=sys.stderr)
            return 2

    print(text)

    if not report["valid"]:
        for error in report["errors"]:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Dataset validation: PASS", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
