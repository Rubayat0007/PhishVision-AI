"""Audit the 555-image dataset for duplicates and acquisition shortcuts.

Three questions:
1. Near-duplicates (perceptual hash) - within a split, and across splits (leakage).
2. Shortcut check - can width/height/aspect/file-size/format alone predict the
   label, trained on train and tested on val? If yes, the dataset may be
   solvable from acquisition artefacts rather than content.
3. Hard negatives - reported as an open question, not scored (needs human eyes).

Exact-duplicate and corrupt-file checks already live in validate_dataset.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "clean_split_v2"
CLASSES = ("legitimate", "phishing")
SPLITS = ("train", "val", "test")
EXT = {".jpg", ".jpeg", ".png", ".webp"}
HAMMING_NEAR = 6


def dhash(path: Path, size: int = 8) -> int:
    with Image.open(path) as handle:
        small = handle.convert("L").resize((size + 1, size), Image.LANCZOS)
        pixels = np.asarray(small, dtype=np.int16)

    bits = (pixels[:, 1:] > pixels[:, :-1]).flatten()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def metadata(path: Path) -> dict:
    with Image.open(path) as handle:
        width, height = handle.size
        mode = handle.mode
    return {
        "width": width,
        "height": height,
        "aspect": round(width / height, 4) if height else 0.0,
        "bytes": path.stat().st_size,
        "format": path.suffix.lower(),
        "mode": mode,
    }


def collect():
    records = []
    for split in SPLITS:
        for label, name in enumerate(CLASSES):
            folder = ROOT / split / name
            for path in sorted(folder.glob("*")):
                if path.suffix.lower() in EXT:
                    record = {"split": split, "label": label, "path": str(path),
                              "hash": dhash(path)}
                    record.update(metadata(path))
                    records.append(record)
    return records


def near_duplicates(records):
    within, across = [], []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            distance = bin(records[i]["hash"] ^ records[j]["hash"]).count("1")
            if distance <= HAMMING_NEAR:
                pair = (records[i]["path"], records[j]["path"], distance)
                (across if records[i]["split"] != records[j]["split"] else within).append(pair)
    return within, across


def shortcut_check(records):
    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "val"]

    def vector(row):
        return [row["width"], row["height"], row["aspect"], row["bytes"],
                1.0 if row["format"] == ".png" else 0.0]

    X_train = np.array([vector(r) for r in train])
    y_train = np.array([r["label"] for r in train])
    X_val = np.array([vector(r) for r in val])
    y_val = np.array([r["label"] for r in val])

    model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=1)
    model.fit(X_train, y_train)

    val_accuracy = float((model.predict(X_val) == y_val).mean())
    cv = cross_val_score(model, X_train, y_train, cv=StratifiedKFold(5, shuffle=True,
                                                                     random_state=42))
    majority = max(y_val.mean(), 1 - y_val.mean())

    return {
        "features": ["width", "height", "aspect", "bytes", "is_png"],
        "train_accuracy_cv5": round(float(cv.mean()), 4),
        "val_accuracy": round(val_accuracy, 4),
        "val_majority_baseline": round(float(majority), 4),
        "interpretation": (
            "shortcut suspected" if val_accuracy - majority > 0.10
            else "no strong metadata shortcut on this split"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "results" / "data_audit")
    args = parser.parse_args()

    records = collect()
    print(f"images: {len(records)}")

    within, across = near_duplicates(records)
    shortcut = shortcut_check(records)

    per_split = {split: sum(1 for r in records if r["split"] == split) for split in SPLITS}
    by_class = {name: sum(1 for r in records if r["label"] == label)
                for label, name in enumerate(CLASSES)}

    summary = {
        "images": len(records),
        "per_split": per_split,
        "per_class": by_class,
        "near_duplicate_threshold_hamming": HAMMING_NEAR,
        "near_duplicates_within_split": len(within),
        "near_duplicates_across_splits": len(across),
        "across_split_examples": across[:10],
        "shortcut_check": shortcut,
        "hard_negatives": "OPEN - requires human review of legitimate samples",
        "label_noise": "BLOCKED - requires manual re-labelling of a sample",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Data audit — 555-image dataset",
        "",
        f"Images {len(records)}: train {per_split['train']}, val {per_split['val']}, "
        f"test {per_split['test']}; legitimate {by_class['legitimate']}, "
        f"phishing {by_class['phishing']}.",
        "",
        "## Near-duplicates (dHash, Hamming <= 6)",
        "",
        f"- within a split: **{len(within)}** pairs",
        f"- across splits: **{len(across)}** pairs",
    ]
    for a, b, distance in across[:10]:
        lines.append(f"  - {Path(a).name} ↔ {Path(b).name} (distance {distance})")

    lines += [
        "",
        "## Shortcut check (metadata only)",
        "",
        f"Train CV-5 accuracy {shortcut['train_accuracy_cv5']}, "
        f"val accuracy {shortcut['val_accuracy']} against majority baseline "
        f"{shortcut['val_majority_baseline']} → **{shortcut['interpretation']}**.",
        "",
        "## Open items",
        "",
        "- Hard-negative coverage: needs human review of the legitimate images.",
        "- Label noise: needs a re-labelled sample; not estimated here.",
        "",
        "## Limits",
        "",
        "- dHash catches re-encodes and small edits, not crops or overlays; a low",
        "  count is not proof of independence.",
        "- The shortcut check uses only coarse metadata; a null result does not",
        "  prove there is no shortcut in finer pixel statistics.",
    ]

    docs = PROJECT_ROOT / "docs" / "measurements"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "data-audit-2026-10-24.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
