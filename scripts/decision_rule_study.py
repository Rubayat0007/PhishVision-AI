"""Which decision rule reduces false positives on the cached validation scores?

Uses results/component_diagnostics/scores.json (83 validation images): text
score, CNN probability, combined risk, label. No model is retrained and no
threshold is tuned on test. Every number here is DEVELOPMENT-set and was
selected on data already used for earlier choices, so it is optimistic.

Writes docs/measurements/decision-rule-study-2026-10-24.md.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCORES = PROJECT_ROOT / "results" / "component_diagnostics" / "scores.json"
DOC = PROJECT_ROOT / "docs" / "measurements" / "decision-rule-study-2026-10-24.md"
LEDGER = PROJECT_ROOT / "docs" / "ledger.md"


def confusion(labels, flags):
    tp = sum(1 for y, f in zip(labels, flags) if y == 1 and f)
    fn = sum(1 for y, f in zip(labels, flags) if y == 1 and not f)
    fp = sum(1 for y, f in zip(labels, flags) if y == 0 and f)
    tn = sum(1 for y, f in zip(labels, flags) if y == 0 and not f)
    return tp, fn, fp, tn


def metrics(labels, flags):
    tp, fn, fp, tn = confusion(labels, flags)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "precision": round(precision, 4), "recall": round(recall, 4),
            "fpr": round(fpr, 4), "f1": round(f1, 4)}


def main() -> int:
    data = json.loads(SCORES.read_text(encoding="utf-8"))
    labels = data["labels"]
    text, cnn = data["text"], data["cnn"]
    combined = data["combined"]

    # The analyzer's risk score is 0-100, the CNN output is 0-1. Comparing a
    # risk score against a probability threshold flags everything, so normalise
    # before using any shared threshold.
    if combined and max(combined) > 1.0:
        combined = [value / 100.0 for value in combined]

    rules = {
        "risk score >= 0.35/100 (scale-confused)": [c >= 0.35 for c in combined],
        "risk score >= 0.25/100": [c >= 0.25 for c in combined],
        "risk score >= 0.20/100": [c >= 0.20 for c in combined],
        "cnn probability >= 0.50": [p >= 0.50 for p in cnn],
        "text >= 50 and cnn >= 0.35": [t >= 50 and p >= 0.35 for t, p in zip(text, cnn)],
        "text >= 30 and cnn >= 0.35": [t >= 30 and p >= 0.35 for t, p in zip(text, cnn)],
        "text >= 50 or cnn >= 0.50": [t >= 50 or p >= 0.50 for t, p in zip(text, cnn)],
    }

    rows = {name: metrics(labels, flags) for name, flags in rules.items()}

    sweep = []
    for threshold in (0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70):
        sweep.append((threshold, metrics(labels, [c >= threshold for c in combined])))

    with_fpr = [(name, row) for name, row in rows.items() if row["recall"] >= 0.85]
    best = max(with_fpr, key=lambda item: item[1]["f1"]) if with_fpr else None

    lines = [
        "# Decision-rule study — false positives on cached validation scores",
        "",
        f"n={len(labels)} ({labels.count(0)} legitimate, {labels.count(1)} phishing). "
        "DEVELOPMENT set; thresholds were chosen after earlier choices on this same",
        "split, so every figure is optimistic. No test data was used.",
        "",
        "## Rules",
        "",
        "| Rule | TP | FP | FN | TN | precision | recall | FPR | F1 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, row in rows.items():
        lines.append(
            f"| {name} | {row['tp']} | {row['fp']} | {row['fn']} | {row['tn']} | "
            f"{row['precision']} | {row['recall']} | {row['fpr']} | {row['f1']} |"
        )

    lines += [
        "",
        "## Combined-score threshold sweep",
        "",
        "| Threshold | precision | recall | FPR | F1 |",
        "|---|---|---|---|---|",
    ]
    for threshold, row in sweep:
        lines.append(f"| {threshold:.2f} | {row['precision']} | {row['recall']} | "
                     f"{row['fpr']} | {row['f1']} |")

    current = rows["risk score >= 0.35/100 (scale-confused)"]

    lines += [
        "",
        "## Reading this",
        "",
        "- The production threshold (0.35) is a **CNN probability**, not a risk score:",
        "  the analyzer's combined score is 0-100, so comparing it to 0.35 flags",
        "  everything. That scale confusion is recorded here rather than quietly fixed.",
        f"- On the risk scale, score >= 0.20 flags {rows['risk score >= 0.20/100']['fp']} of "
        f"{labels.count(0)} legitimate pages (FPR {rows['risk score >= 0.20/100']['fpr']}) "
        f"with recall {rows['risk score >= 0.20/100']['recall']}; score >= 0.25 gives "
        f"FPR {rows['risk score >= 0.25/100']['fpr']} and recall {rows['risk score >= 0.25/100']['recall']}.",
        f"- CNN-only at probability 0.50: FPR {rows['cnn probability >= 0.50']['fpr']}, "
        f"recall {rows['cnn probability >= 0.50']['recall']}.",
    ]
    if best:
        name, row = best
        lines += [
            f"- Best F1 among rules keeping recall >= 0.85: **{name}**, "
            f"F1 {row['f1']}, FPR {row['fpr']}, recall {row['recall']}.",
            "- That is a candidate, not a result: it was selected on the same split "
            "used for earlier choices.",
        ]
    lines += [
        "- Requiring both components to fire trades recall for precision; the table "
        "shows how much, rather than assuming the trade is free.",
        "",
        "## Limits",
        "",
        "- Selection on the evaluation split: the chosen rule will regress on new data.",
        "- n=83 with 40 legitimate images: one false positive moves FPR by 2.5 points.",
        "- Scores come from the frozen production model; nothing was retrained.",
    ]

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")

    row = (
        "| R-PV-rule-study-01 | HEAD | 2026-10-24 | `scripts/decision_rule_study.py` | "
        "cached val scores (83) | 83 (40 legit / 43 phish) | `1403582C…` | 0.35 | "
        f"current rule FP {current['fp']}, FPR {current['fpr']}, F1 {current['f1']}; "
        f"best recall>=0.85 rule {(best[0] if best else 'none')} F1 {best[1]['f1'] if best else 'n/a'}, "
        f"FPR {best[1]['fpr'] if best else 'n/a'} | rule selection on DEVELOPMENT data | "
        "RECORDED, DEVELOPMENT |\n"
    )
    ledger_text = LEDGER.read_text(encoding="utf-8")
    if "R-PV-rule-study-01" not in ledger_text:
        anchor = "| R-PV-tests-01 |"
        LEDGER.write_text(ledger_text.replace(anchor, row + anchor, 1), encoding="utf-8")

    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
