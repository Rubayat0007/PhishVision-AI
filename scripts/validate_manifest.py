"""Validate a dataset manifest before any evaluation uses it.

Enforces the rules the 555-image set broke: one row per image, hashes present,
enum-labelled splits, and no cluster or domain spanning two splits.

Exit codes: 0 valid, 1 validation failures, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SPLITS = {"train", "validation", "test", "sealed"}
LABELS = {"phishing", "legitimate"}
REQUIRED = {
    "filename", "sha256", "phash", "label", "label_basis", "label_confidence",
    "registered_domain", "brand_cluster", "kit_cluster", "captured_at",
    "source", "license", "split",
}
SHA = re.compile(r"^[0-9a-f]{64}$")
PHASH = re.compile(r"^[0-9a-f]{16}$")


def validate(manifest: dict) -> dict:
    errors: list[str] = []
    images = manifest.get("images")

    if not isinstance(images, list) or not images:
        return {"valid": False, "errors": ["manifest has no images"], "counts": {}}

    seen_names, seen_sha = set(), set()
    by_split: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    brands: dict[str, set[str]] = defaultdict(set)
    sealed = []

    for index, row in enumerate(images):
        where = f"image[{index}]"

        if not isinstance(row, dict):
            errors.append(f"{where}: not an object")
            continue

        missing = REQUIRED - set(row)
        if missing:
            errors.append(f"{where}: missing {sorted(missing)}")
            continue

        name = row["filename"]
        if name in seen_names:
            errors.append(f"{where}: duplicate filename {name}")
        seen_names.add(name)

        if not SHA.fullmatch(str(row["sha256"])):
            errors.append(f"{where}: sha256 malformed")
        if str(row["sha256"]) in seen_sha:
            errors.append(f"{where}: duplicate content hash")
        seen_sha.add(str(row["sha256"]))

        if not PHASH.fullmatch(str(row["phash"])):
            errors.append(f"{where}: phash must be 16 hex chars")

        if row["label"] not in LABELS:
            errors.append(f"{where}: label {row['label']!r} invalid")
        if row["split"] not in SPLITS:
            errors.append(f"{where}: split {row['split']!r} invalid")

        try:
            datetime.fromisoformat(str(row["captured_at"]).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{where}: captured_at not ISO-8601")

        confidence = row["label_confidence"]
        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            errors.append(f"{where}: label_confidence must be in [0,1]")

        by_split[row["split"]][row["label"]] += 1
        groups[(str(row["registered_domain"]), str(row["kit_cluster"]))].add(row["split"])
        brands[str(row["brand_cluster"])].add(row["split"])

        if row["split"] == "sealed":
            sealed.append(name)

    for group, splits in groups.items():
        if len(splits) > 1:
            errors.append(f"group {group} spans splits {sorted(splits)}")

    for brand, splits in brands.items():
        if {"train", "test"} <= splits or {"train", "sealed"} <= splits:
            errors.append(f"brand {brand} appears in train and test/sealed")

    counts = {split: dict(classes) for split, classes in by_split.items()}

    if "sealed" in by_split:
        if len(sealed) < 100:
            errors.append(f"sealed holdout has only {len(sealed)} images")

    return {"valid": not errors, "errors": errors, "counts": counts,
            "images": len(images)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = validate(payload)
    text = json.dumps(result, indent=2, sort_keys=True)

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(text + "\n", encoding="utf-8")

    print(text)

    if not result["valid"]:
        for error in result["errors"][:20]:
            print(f"- {error}", file=sys.stderr)
        print("STATUS: FAIL", file=sys.stderr)
        return 1

    print("STATUS: PASS", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
