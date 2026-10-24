"""Dry run of the pre-registered P-1 rule on the pilot test split.

P-1: risk score >= 25/100 cuts false positives at a small recall cost. Predicted
(cached validation, n=83): FPR 0.075, recall 0.605, F1 0.722.

This is a dry run on 19 images with feed-derived labels: it can show the direction
of the effect, never confirm it. No threshold is changed by this script.

Writes results/pilot_rule_check/summary.json and docs/measurements/pilot-rule-check.md.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.security.analyzer import PhishVisionAnalyzer  # noqa: E402


def wilson(successes: int, total: int, z: float = 1.96):
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def score_rows(rows):
    from PIL import Image

    analyzer = PhishVisionAnalyzer()
    triples = []

    for index, row in enumerate(rows, 1):
        path = PROJECT_ROOT / "captures" / row["filename"]
        with Image.open(path) as handle:
            result = analyzer.analyze(handle.convert("RGB"))
        triples.append((
            1 if row["label"] == "phishing" else 0,
            float(result["cnn_analysis"]["phishing_probability"] or 0.0),
            float(result["risk"]["overall_score"]),
        ))
        if index % 5 == 0:
            print(f"  {index}/{len(rows)}", flush=True)
    return triples


def evaluate(triples, rule):
    tp = fn = fp = tn = 0
    for label, cnn, risk in triples:
        flagged = rule(cnn, risk)
        if label == 1 and flagged:
            tp += 1
        elif label == 1:
            fn += 1
        elif flagged:
            fp += 1
        else:
            tn += 1

    recall = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "recall": round(recall, 4), "fpr": round(fpr, 4),
            "precision": round(precision, 4), "f1": round(f1, 4),
            "fpr_ci": [round(v, 4) for v in wilson(fp, fp + tn)]}


def main() -> int:
    rows = list(csv.DictReader(
        (PROJECT_ROOT / "captures" / "labels.csv").open(encoding="utf-8", newline="")
    ))
    test = [row for row in rows if row["split"] == "test"]
    print(f"scoring {len(test)} test images")

    triples = score_rows(test)

    rules = {
        "current: cnn >= 0.35": lambda cnn, risk: cnn >= 0.35,
        "P-1: risk >= 25/100": lambda cnn, risk: risk >= 25.0,
        "risk >= 20/100": lambda cnn, risk: risk >= 20.0,
        "cnn >= 0.50": lambda cnn, risk: cnn >= 0.50,
        "risk >= 25 and cnn >= 0.35": lambda cnn, risk: risk >= 25.0 and cnn >= 0.35,
    }

    results = {name: evaluate(triples, rule) for name, rule in rules.items()}

    summary = {
        "split": "test",
        "n": len(triples),
        "positives": sum(1 for t in triples if t[0] == 1),
        "negatives": sum(1 for t in triples if t[0] == 0),
        "rules": results,
        "label_status": "feed-derived, unreviewed",
        "status": "DRY RUN - direction only, not a promotion decision",
    }

    out = PROJECT_ROOT / "results" / "pilot_rule_check"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# P-1 dry run on the pilot test split",
        "",
        f"n={len(triples)} ({summary['positives']} phishing, {summary['negatives']} legitimate). "
        "Labels are feed-derived. This shows direction only.",
        "",
        "| Rule | TP | FP | FN | TN | recall | FPR | FPR 95% CI | F1 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, row in results.items():
        lines.append(
            f"| {name} | {row['tp']} | {row['fp']} | {row['fn']} | {row['tn']} | "
            f"{row['recall']} | {row['fpr']} | {row['fpr_ci'][0]}-{row['fpr_ci'][1]} | {row['f1']} |"
        )

    current = results["current: cnn >= 0.35"]
    candidate = results["P-1: risk >= 25/100"]

    lines += [
        "",
        "## Reading this",
        "",
        f"- Current operating point: {current['fp']} false positives on "
        f"{summary['negatives']} legitimate pages (FPR {current['fpr']}).",
        f"- P-1 (risk >= 25): {candidate['fp']} false positives, FPR {candidate['fpr']}, "
        f"recall {candidate['recall']}.",
        f"- Pre-registered prediction was FPR 0.075 at recall 0.605 (n=83 cached validation).",
        "",
        "## Limits",
        "",
        f"- {summary['negatives']} legitimate images: one false positive is "
        f"{100 / summary['negatives']:.0f} FPR points.",
        "- Feed-derived labels, 32% of phishing flagged by OCR triage.",
        "- Direction only: promotion still requires the sealed holdout.",
    ]

    (PROJECT_ROOT / "docs" / "measurements" / "pilot-rule-check.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
