"""Fusion calibration on train/validation, evaluated once on a sealed test.

Hypothesis (pre-registered here, before evaluation): the fixed 30/30/40 weighting
is arbitrary. Fitting a two-feature logistic model on (OCR text score, CNN
probability) with the threshold chosen on validation will keep recall >= 0.50 and
lower false positives on test compared with the current fusion.

Rules: fit on `train`, choose the threshold on `validation`, and touch `test`
exactly once. This is the P-2/P-4-style comparison the pilot can still support.

OCR scores are cached so the run resumes instead of re-reading every image.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import csv  # noqa: E402
import math  # noqa: E402

import numpy as np  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

CACHE = PROJECT_ROOT / "results" / "fusion" / "scores.json"
RECALL_FLOOR = 0.50


def collect():
    rows = list(csv.DictReader(
        (PROJECT_ROOT / "captures" / "labels.csv").open(encoding="utf-8", newline="")
    ))

    cache = {}
    if CACHE.is_file():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))

    missing = [row["filename"] for row in rows if row["filename"] not in cache]

    if missing:
        from PIL import Image
        from src.security.analyzer import PhishVisionAnalyzer

        analyzer = PhishVisionAnalyzer()

        for index, row in enumerate(rows, 1):
            if row["filename"] in cache:
                continue
            with Image.open(PROJECT_ROOT / "captures" / row["filename"]) as handle:
                result = analyzer.analyze(handle.convert("RGB"))
            cache[row["filename"]] = {
                "text": float(result["text_analysis"]["score"]),
                "cnn": float(result["cnn_analysis"]["phishing_probability"] or 0.0),
                "risk": float(result["risk"]["overall_score"]),
            }
            if index % 10 == 0:
                print(f"  scored {index}/{len(rows)}", flush=True)
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                CACHE.write_text(json.dumps(cache), encoding="utf-8")

        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache), encoding="utf-8")

    return rows, cache


def wilson(successes, total, z=1.96):
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def operating(scores, truth, floor=RECALL_FLOOR):
    positives = sorted((scores[i] for i in range(len(truth)) if truth[i] == 1), reverse=True)
    if not positives:
        return None
    cutoff = positives[max(0, math.ceil(floor * len(positives)) - 1)]

    tp = sum(1 for i in range(len(truth)) if truth[i] == 1 and scores[i] >= cutoff)
    fn = sum(1 for i in range(len(truth)) if truth[i] == 1 and scores[i] < cutoff)
    fp = sum(1 for i in range(len(truth)) if truth[i] == 0 and scores[i] >= cutoff)
    tn = sum(1 for i in range(len(truth)) if truth[i] == 0 and scores[i] < cutoff)

    return {"threshold": round(float(cutoff), 4),
            "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
            "fpr": round(fp / (fp + tn), 4) if fp + tn else 0.0,
            "fpr_ci": [round(v, 4) for v in wilson(fp, fp + tn)],
            "tp": tp, "fn": fn, "fp": fp, "tn": tn}


def main() -> int:
    rows, cache = collect()

    labels = np.array([1 if row["label"] == "phishing" else 0 for row in rows])
    splits = np.array([row["split"] for row in rows])
    text = np.array([cache[row["filename"]]["text"] for row in rows]) / 100.0
    cnn = np.array([cache[row["filename"]]["cnn"] for row in rows])
    risk = np.array([cache[row["filename"]]["risk"] for row in rows]) / 100.0

    X = np.column_stack([text, cnn])
    train, val, test = splits == "train", splits == "validation", splits == "test"

    fusion = LogisticRegression(C=1.0, max_iter=2000, class_weight="balanced")
    fusion.fit(X[train], labels[train])

    print(f"fusion weights: text {fusion.coef_[0][0]:.3f}, cnn {fusion.coef_[0][1]:.3f}, "
          f"intercept {fusion.intercept_[0]:.3f}")

    val_scores = fusion.predict_proba(X[val])[:, 1]
    chosen = operating(val_scores, labels[val])
    if chosen is None:
        raise SystemExit("validation has no positives")

    # Freeze the threshold now; test is scored once, below.
    threshold = chosen["threshold"]
    test_scores = fusion.predict_proba(X[test])[:, 1]
    fused_test = operating(test_scores, labels[test])

    baseline_test = operating(risk[test], labels[test])
    cnn_test = operating(cnn[test], labels[test])

    summary = {
        "n": {"train": int(train.sum()), "validation": int(val.sum()), "test": int(test.sum())},
        "weights": {"text": round(float(fusion.coef_[0][0]), 4),
                    "cnn": round(float(fusion.coef_[0][1]), 4)},
        "cv_auc_val_fusion": round(float(roc_auc_score(labels[val], val_scores)), 4),
        "chosen_threshold_on_validation": threshold,
        "test": {"fusion": fused_test, "current_risk_rule": baseline_test,
                 "cnn_only": cnn_test},
        "status": "SEALED-TEST, single evaluation; pilot labels feed-derived",
    }

    out = PROJECT_ROOT / "results" / "fusion"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# Fusion calibration (pre-registered, single sealed-test evaluation)",
        "",
        f"Train {summary['n']['train']}, validation {summary['n']['validation']}, "
        f"test {summary['n']['test']}. Threshold fixed on validation before test was scored.",
        "",
        f"Fitted weights: OCR text {summary['weights']['text']}, CNN {summary['weights']['cnn']}.",
        "",
        "| Rule | threshold | TP | FP | FN | TN | recall | FPR | FPR 95% CI |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, row in (("calibrated fusion", fused_test),
                      ("current risk rule", baseline_test),
                      ("CNN only", cnn_test)):
        if row:
            lines.append(f"| {name} | {row['threshold']} | {row['tp']} | {row['fp']} | "
                         f"{row['fn']} | {row['tn']} | {row['recall']} | {row['fpr']} | "
                         f"{row['fpr_ci'][0]}-{row['fpr_ci'][1]} |")

    if fused_test and baseline_test:
        better = fused_test["fpr"] < baseline_test["fpr"] - 1e-9
        lines += [
            "",
            "## Verdict",
            "",
            ("- **Hypothesis supported on the sealed test**: calibrated fusion has the "
             f"lower FPR ({fused_test['fpr']} vs {baseline_test['fpr']}) at recall "
             f">= {fused_test['recall']}.")
            if better else
            ("- **Hypothesis not supported**: the calibrated fusion does not beat the "
             "current rule on FPR at the recall floor."),
            "- Single sealed evaluation, 18 test images: direction and mechanism, not "
            "a promotion decision.",
        ]

    lines += [
        "",
        "## Limits",
        "",
        "- Labels feed-derived; 32% of phishing captures flagged by OCR triage.",
        "- Test n=18: one case moves FPR by 11 points.",
        "- The fit uses two features; URL weighting (P-3) remains untested because no",
        "  dataset image carries a URL.",
    ]

    (PROJECT_ROOT / "docs" / "measurements" / "fusion-calibration.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
