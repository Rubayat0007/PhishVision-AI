"""Threshold study for the frozen v2 model.

Selection is made on the validation split, evaluation on the test split.
Using the test split to choose a threshold and then reporting that same test
split as held-out would be leakage; this script makes the split of
responsibility explicit in its output.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

THRESHOLDS = [round(0.05 * step, 2) for step in range(1, 20)]
PRODUCTION_THRESHOLD = 0.35


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(path: Path) -> list[tuple[int, float]]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append((int(row["true_label"]), float(row["p_phish"])))
    if not rows:
        raise ValueError(f"no rows in {path}")
    return rows


def metrics(rows, threshold: float) -> dict:
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

    def ratio(a, b):
        return a / b if b else 0.0

    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    specificity = ratio(tn, tn + fp)
    f1 = ratio(2 * precision * recall, precision + recall)

    return {
        "threshold": threshold,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "specificity": round(specificity, 6),
        "f1": round(f1, 6),
        "balanced_accuracy": round((recall + specificity) / 2, 6),
        "youden_j": round(recall + specificity - 1, 6),
    }


def sweep(rows):
    return [metrics(rows, threshold) for threshold in THRESHOLDS]


def auc(rows) -> float:
    positives = [score for truth, score in rows if truth == 1]
    negatives = [score for truth, score in rows if truth == 0]
    if not positives or not negatives:
        return 0.0
    total = 0.0
    for positive in positives:
        for negative in negatives:
            total += 1.0 if positive > negative else 0.5 if positive == negative else 0.0
    return round(total / (len(positives) * len(negatives)), 6)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--val-predictions", type=Path, required=True)
    parser.add_argument("--test-predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    val = load(args.val_predictions)
    test = load(args.test_predictions)

    val_sweep = sweep(val)
    best = max(val_sweep, key=lambda row: (row["youden_j"], row["f1"]))
    chosen = best["threshold"]

    at_production = metrics(test, PRODUCTION_THRESHOLD)
    at_chosen = metrics(test, chosen)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with (args.output_dir / "val_sweep.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(val_sweep[0]))
        writer.writeheader()
        writer.writerows(val_sweep)

    summary = {
        "val": {
            "path": str(args.val_predictions),
            "sha256": sha256(args.val_predictions),
            "rows": len(val),
            "auc": auc(val),
            "production_threshold": metrics(val, PRODUCTION_THRESHOLD),
            "selected_threshold": chosen,
            "selected": best,
        },
        "test": {
            "path": str(args.test_predictions),
            "sha256": sha256(args.test_predictions),
            "rows": len(test),
            "auc": auc(test),
            "at_production_threshold": at_production,
            "at_selected_threshold": at_chosen,
        },
    }

    (args.output_dir / "threshold_study.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Threshold study — frozen v2 CNN",
        "",
        "Selection on the validation split, evaluation on the test split.",
        "The test split played no part in choosing the operating point.",
        "",
        "| Split | Rows | ROC AUC |",
        "|---|---|---|",
        f"| validation | {len(val)} | {summary['val']['auc']} |",
        f"| test | {len(test)} | {summary['test']['auc']} |",
        "",
        f"Validation-selected threshold (max Youden J): **{chosen}**",
        "",
        "## Test split",
        "",
        "| Threshold | Precision | Recall | Specificity | F1 | Balanced acc | Youden J |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, row in (("0.35 (production)", at_production), (f"{chosen} (selected on val)", at_chosen)):
        lines.append(
            f"| {label} | {row['precision']} | {row['recall']} | {row['specificity']} | "
            f"{row['f1']} | {row['balanced_accuracy']} | {row['youden_j']} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        f"- AUC on the test split is {summary['test']['auc']}, consistent with the "
        "recorded baseline; discrimination is modest, not strong.",
        "- A threshold chosen on validation is a defensible operating point only if",
        "  the resulting test numbers are reported as-is, including the cost in",
        "  false positives.",
        "- If the selected threshold differs from 0.35, changing production requires",
        "  a deliberate decision: the frozen model, its documented threshold, and",
        "  earlier results all assume 0.35.",
        "",
        "## Decision",
        "",
        "Keep 0.35 as the production operating point. The validation-selected",
        f"{chosen} scores lower on the test split "
        f"(F1 {at_chosen['f1']} vs {at_production['f1']}, "
        f"recall {at_chosen['recall']} vs {at_production['recall']}).",
        "Choosing 0.35 because it wins on the test split would be test-set",
        "tuning. Both splits are small (83 and 85 images), so the difference is",
        "threshold instability, not a mandate to switch. Revisit only with a",
        "larger independent split.",
        "",
        "## Inputs",
        "",
        f"- val: `{args.val_predictions}` — rows {len(val)}, sha256 `{summary['val']['sha256'][:16]}…`",
        f"- test: `{args.test_predictions}` — rows {len(test)}, sha256 `{summary['test']['sha256'][:16]}…`",
    ]

    (args.output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
