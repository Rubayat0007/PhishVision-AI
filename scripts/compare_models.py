"""Compare candidate checkpoints and apply a pre-registered promotion rule.

Rule (fixed before looking at test results):
    Promote a candidate only if, on the VALIDATION split at threshold 0.35,
    it improves F1 by at least 2 absolute points AND does not reduce recall
    relative to the current production model (v2).

The test split is evaluated once, for the baseline and, if any, the single
promoted candidate. No test-set selection is performed.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
from PIL import Image

from src.data.transforms import val_transform
from src.models.cnn import PhishVisionCNN

CLASSES = ("legitimate", "phishing")
THRESHOLD = 0.35
MIN_F1_GAIN = 0.02  # 2 absolute points


def load_model(path: Path):
    model = PhishVisionCNN(num_classes=2)
    state = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model


def scores(model, images, url_note=""):
    results = []
    with torch.no_grad():
        for image_path, label in images:
            with Image.open(image_path) as handle:
                tensor = val_transform(handle.convert("RGB")).unsqueeze(0)
            probability = torch.softmax(model(tensor), dim=1)[0, 1].item()
            results.append((label, probability))
    return results


def metrics(rows, threshold=THRESHOLD):
    tp = fp = tn = fn = 0
    for truth, score in rows:
        predicted = 1 if score >= threshold else 0
        if truth == 1 and predicted == 1:
            tp += 1
        elif truth == 0 and predicted == 0:
            tn += 1
        elif truth == 0:
            fp += 1
        else:
            fn += 1

    ratio = lambda a, b: a / b if b else 0.0
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    specificity = ratio(tn, tn + fp)
    f1 = ratio(2 * precision * recall, precision + recall)

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4), "recall": round(recall, 4),
        "specificity": round(specificity, 4), "f1": round(f1, 4),
        "accuracy": round(ratio(tp + tn, len(rows)), 4),
    }


def collect(split: str):
    root = Path("data") / "clean_split_v2" / split
    items = []
    for label, name in enumerate(CLASSES):
        folder = root / name
        if not folder.is_dir():
            raise FileNotFoundError(folder)
        for path in sorted(folder.glob("*")):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                items.append((path, label))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("results/evaluation/model-comparison"))
    args = parser.parse_args()

    val = collect("val")
    test = collect("test")
    print(f"val={len(val)} test={len(test)}")

    candidates = sorted(Path("models").glob("*.pth"))
    baseline_path = Path("models/phishvision_cnn_v2.pth")

    rows = []
    skipped = []
    val_scores = {}

    for path in candidates:
        try:
            model = load_model(path)
        except Exception as exc:
            skipped.append({"model": path.name, "reason": f"{type(exc).__name__}: {exc}"[:120]})
            continue

        scored = scores(model, val)
        val_scores[path.name] = scored
        result = metrics(scored)
        result["model"] = path.name
        rows.append(result)
        print(f"{path.name:42} F1={result['f1']:.4f} recall={result['recall']:.4f} precision={result['precision']:.4f}")

    if baseline_path.name not in val_scores:
        print("ERROR: baseline model missing from models/")
        return 2

    baseline = next(r for r in rows if r["model"] == baseline_path.name)

    eligible = [
        r for r in rows
        if r["model"] != baseline["model"]
        and r["f1"] >= baseline["f1"] + MIN_F1_GAIN
        and r["recall"] >= baseline["recall"]
    ]
    promoted = max(eligible, key=lambda r: r["f1"]) if eligible else None

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with (args.output_dir / "validation_comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    test_result = None
    test_rows = {}
    if promoted:
        model = load_model(Path("models") / promoted["model"])
        test_rows[promoted["model"]] = metrics(scores(model, test))
        test_result = test_rows[promoted["model"]]

    test_baseline = metrics(scores(load_model(baseline_path), test))
    test_rows[baseline_path.name] = test_baseline

    summary = {
        "rule": {
            "split_for_selection": "validation",
            "threshold": THRESHOLD,
            "min_f1_gain_absolute": MIN_F1_GAIN,
            "recall_must_not_drop": True,
        },
        "baseline": baseline,
        "promoted": promoted["model"] if promoted else None,
        "validation": rows,
        "test": test_rows,
        "skipped": skipped,
        "inputs": {"val_images": len(val), "test_images": len(test)},
    }

    (args.output_dir / "model_comparison.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Candidate model comparison",
        "",
        "Rule fixed before seeing test results: promote only if validation F1",
        f"improves by at least {MIN_F1_GAIN:.2f} and validation recall does not drop.",
        "",
        "## Validation split",
        "",
        "| Model | Precision | Recall | Specificity | F1 | Accuracy |",
        "|---|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda r: -r["f1"]):
        lines.append(
            f"| {row['model']} | {row['precision']} | {row['recall']} | "
            f"{row['specificity']} | {row['f1']} | {row['accuracy']} |"
        )

    lines += ["", "## Decision", ""]
    if promoted:
        lines.append(f"Promote **{promoted['model']}** (validation F1 {promoted['f1']} vs baseline {baseline['f1']}).")
    else:
        lines.append(
            f"**Keep {baseline['model']}.** No candidate met the rule "
            f"(F1 >= {baseline['f1'] + MIN_F1_GAIN:.2f} with recall >= {baseline['recall']})."
        )

    lines += [
        "",
        "## Test split (evaluated once)",
        "",
        "| Model | Precision | Recall | Specificity | F1 | Accuracy |",
        "|---|---|---|---|---|---|",
    ]
    for name, row in test_rows.items():
        lines.append(
            f"| {name} | {row['precision']} | {row['recall']} | "
            f"{row['specificity']} | {row['f1']} | {row['accuracy']} |"
        )

    if skipped:
        lines += ["", "## Skipped checkpoints", ""]
        for item in skipped:
            lines.append(f"- `{item['model']}` — {item['reason']}")

    lines += [
        "",
        "## Limits",
        "",
        "- 83 validation and 85 test images: differences under ~3 points are noise.",
        "- Clean images only; adversarial robustness is measured by the dedicated",
        "  evaluators in `robustness/`, not here.",
        "- Promotion changes production only via `src/config.py` `CNN_THRESHOLD`",
        "  and `ACTIVE_MODEL_PATH`, plus the digest in `src/models/integrity.py` —",
        "  a separate, deliberate change.",
    ]

    (args.output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
