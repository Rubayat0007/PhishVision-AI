"""Exploratory evaluation on the pilot's test split.

This is NOT the sealed holdout and NOT a reliability profile. Labels are
feed-derived (see docs/measurements/pilot-label-status.md), so every number here
is HYPOTHESIS with wide intervals. The purpose is to check that the frozen model
behaves plausibly on v3-format data, not to publish a quality claim.

Writes docs/measurements/pilot-eval.md and results/pilot_eval/summary.json.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys  # noqa: E402

sys.path.insert(0, str(PROJECT_ROOT))

THRESHOLD = 0.35


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> int:
    import torch
    from PIL import Image

    from src.data.transforms import val_transform
    from src.models.predictor import CNNPredictor

    rows = list(csv.DictReader(
        (PROJECT_ROOT / "captures" / "labels.csv").open(encoding="utf-8", newline="")
    ))
    test = [row for row in rows if row["split"] == "test"]

    predictor = CNNPredictor()
    if not predictor.model_loaded:
        raise SystemExit("production checkpoint did not load")

    labels, scores = [], []

    with torch.no_grad():
        for row in test:
            with Image.open(PROJECT_ROOT / "captures" / row["filename"]) as handle:
                tensor = val_transform(handle.convert("RGB")).unsqueeze(0)
            probability = float(torch.softmax(predictor.model(tensor), dim=1)[0, 1])
            scores.append(probability)
            labels.append(1 if row["label"] == "phishing" else 0)

    tp = sum(1 for y, s in zip(labels, scores) if y == 1 and s >= THRESHOLD)
    fn = sum(1 for y, s in zip(labels, scores) if y == 1 and s < THRESHOLD)
    fp = sum(1 for y, s in zip(labels, scores) if y == 0 and s >= THRESHOLD)
    tn = sum(1 for y, s in zip(labels, scores) if y == 0 and s < THRESHOLD)

    recall = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    summary = {
        "split": "test",
        "n": len(labels),
        "positives": labels.count(1),
        "negatives": labels.count(0),
        "threshold": THRESHOLD,
        "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "recall": round(recall, 4),
        "recall_ci": [round(v, 4) for v in wilson(tp, tp + fn)],
        "fpr": round(fpr, 4),
        "fpr_ci": [round(v, 4) for v in wilson(fp, fp + tn)],
        "precision": round(precision, 4),
        "f1": round(f1, 4),
        "label_status": "feed-derived, unreviewed; 32% of phishing flagged by OCR triage",
        "status": "HYPOTHESIS - not a profile, not the sealed holdout",
    }

    out = PROJECT_ROOT / "results" / "pilot_eval"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# Pilot evaluation (exploratory, HYPOTHESIS)",
        "",
        f"Test split: n={summary['n']} ({summary['positives']} phishing, "
        f"{summary['negatives']} legitimate), threshold {THRESHOLD}.",
        "",
        "| Metric | Value | 95% Wilson CI |",
        "|---|---|---|",
        f"| recall | {summary['recall']} | {summary['recall_ci'][0]}-{summary['recall_ci'][1]} |",
        f"| false-positive rate | {summary['fpr']} | {summary['fpr_ci'][0]}-{summary['fpr_ci'][1]} |",
        f"| precision | {summary['precision']} | — |",
        f"| F1 | {summary['f1']} | — |",
        "",
        f"Confusion: TP {tp}, FN {fn}, FP {fp}, TN {tn}.",
        "",
        "## Why this is not a quality claim",
        "",
        "- Labels are feed-derived: 21 of 65 phishing captures (32%) showed no",
        "  credential vocabulary or domain token in OCR.",
        "- 9 legitimate test images: one false positive moves FPR by 11 points.",
        "- Not the sealed holdout, and no threshold was tuned on it.",
        "- It exists to check the pipeline end to end on v3-format data.",
    ]
    (PROJECT_ROOT / "docs" / "measurements" / "pilot-eval.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({k: summary[k] for k in
                      ("n", "recall", "recall_ci", "fpr", "fpr_ci", "precision", "f1")},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
