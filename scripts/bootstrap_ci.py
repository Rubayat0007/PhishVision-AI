"""Bootstrap confidence intervals for the recorded test-split metrics.

The test split has 85 images. Reporting point estimates without uncertainty
invites over-reading; this quantifies how much the numbers could move under
resampling of the same population.

It does not create new data and does not narrow generalisation limits; it
makes the existing uncertainty explicit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

RESAMPLES = 5000
SEED = 42
THRESHOLD = 0.35


def load(path: Path) -> list[tuple[int, float]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [(int(row["true_label"]), float(row["p_phish"])) for row in csv.DictReader(handle)]


def metrics(rows) -> dict:
    tp = fp = tn = fn = 0
    positives = []
    negatives = []

    for truth, score in rows:
        predicted = 1 if score >= THRESHOLD else 0
        (positives if truth == 1 else negatives).append(score)

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
    f1 = ratio(2 * precision * recall, precision + recall)

    auc = 0.0
    if positives and negatives:
        wins = sum(
            1.0 if p > n else 0.5 if p == n else 0.0
            for p in positives
            for n in negatives
        )
        auc = wins / (len(positives) * len(negatives))

    return {
        "accuracy": ratio(tp + tn, len(rows)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": auc,
        "specificity": ratio(tn, tn + fp),
    }


def percentile(values, p):
    ordered = sorted(values)
    index = (len(ordered) - 1) * p / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    rows = load(args.predictions)
    point = metrics(rows)

    rng = random.Random(SEED)
    samples = {name: [] for name in point}

    for _ in range(RESAMPLES):
        resampled = [rows[rng.randrange(len(rows))] for _ in range(len(rows))]
        result = metrics(resampled)
        for name in samples:
            samples[name].append(result[name])

    summary = {
        "input": str(args.predictions),
        "input_sha256": hashlib.sha256(args.predictions.read_bytes()).hexdigest().upper(),
        "rows": len(rows),
        "threshold": THRESHOLD,
        "resamples": RESAMPLES,
        "seed": SEED,
        "point_estimates": {k: round(v, 6) for k, v in point.items()},
        "intervals": {
            name: {
                "p2_5": round(percentile(values, 2.5), 6),
                "p97_5": round(percentile(values, 97.5), 6),
            }
            for name, values in samples.items()
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "bootstrap_ci.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# Test-split uncertainty (bootstrap)",
        "",
        f"Input: `{args.predictions.name}` — {len(rows)} rows, threshold {THRESHOLD},",
        f"{RESAMPLES} resamples, seed {SEED}. Percentile intervals.",
        "",
        "| Metric | Point estimate | 95% interval |",
        "|---|---|---|",
    ]

    for name in ("accuracy", "precision", "recall", "f1", "roc_auc", "specificity"):
        interval = summary["intervals"][name]
        lines.append(
            f"| {name} | {summary['point_estimates'][name]:.4f} | "
            f"{interval['p2_5']:.4f} – {interval['p97_5']:.4f} |"
        )

    lines += [
        "",
        "## Reading this",
        "",
        "- With 85 images, intervals are wide: differences of a few points between",
        "  models or thresholds are inside the noise band.",
        "- The interval describes sampling variability of this split, not variation",
        "  across datasets. Generalisation to another screenshot population is a",
        "  separate question that needs separate data.",
        "- Resampling is deterministic given the seed, so the table is reproducible",
        "  from the recorded predictions.",
    ]

    (args.output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
