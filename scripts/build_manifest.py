"""Build a dataset manifest from captured images plus a labels CSV.

The labels CSV carries the human decisions; this script computes the hashes and
enforces the schema via validate_manifest. Nothing is inferred: a missing label
or licence stops the build.

Expected CSV columns:
    filename,label,label_basis,label_confidence,registered_domain,
    brand_cluster,kit_cluster,captured_at,source,license,split

Exit codes: 0 built, 1 validation failures, 2 input error.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from validate_manifest import validate  # noqa: E402

CSV_FIELDS = [
    "filename", "label", "label_basis", "label_confidence", "registered_domain",
    "brand_cluster", "kit_cluster", "captured_at", "source", "license", "split",
]
EXT = {".jpg", ".jpeg", ".png", ".webp"}


def dhash(path: Path, size: int = 8) -> str:
    from PIL import Image
    import numpy as np

    with Image.open(path) as handle:
        small = handle.convert("L").resize((size + 1, size), Image.LANCZOS)
        pixels = np.asarray(small, dtype=np.int16)

    value = 0
    for bit in (pixels[:, 1:] > pixels[:, :-1]).flatten():
        value = (value << 1) | int(bit)

    return f"{value:016x}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(images_dir: Path, labels_csv: Path, dataset_version: str) -> dict:
    with labels_csv.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError("labels CSV has no rows")

    missing_columns = [field for field in CSV_FIELDS if field not in (rows[0] or {})]
    if missing_columns:
        raise ValueError(f"labels CSV missing columns: {missing_columns}")

    images = []

    for row in rows:
        path = images_dir / row["filename"]

        if not path.is_file():
            raise ValueError(f"missing image: {path}")

        if path.suffix.lower() not in EXT:
            raise ValueError(f"unsupported image type: {path}")

        images.append({
            "filename": row["filename"],
            "sha256": sha256(path),
            "phash": dhash(path),
            "label": row["label"],
            "label_basis": row["label_basis"],
            "label_confidence": float(row["label_confidence"]),
            "registered_domain": row["registered_domain"],
            "brand_cluster": row["brand_cluster"],
            "kit_cluster": row["kit_cluster"],
            "captured_at": row["captured_at"],
            "source": row["source"],
            "license": row["license"],
            "split": row["split"],
        })

    return {"schema_version": 1, "dataset_version": dataset_version, "images": images}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--dataset-version", default="v3-pilot")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        manifest = build(args.images_dir, args.labels, args.dataset_version)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = validate(manifest)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))

    if not result["valid"]:
        for error in result["errors"][:20]:
            print(f"- {error}", file=sys.stderr)
        print("STATUS: FAIL (manifest written for inspection)", file=sys.stderr)
        return 1

    print("STATUS: PASS", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
