"""Component diagnostics on the PhishVision validation split.

Answers two questions before any model work:
1. Does each component carry ranking information (AUC), and does the CNN add
   anything over the text heuristics at the current 30/30/40 weights?
2. Is the CNN probability calibrated (reliability, Brier, ECE)?

No URL is supplied for dataset images, so the URL component is absent and its
AUC is undefined - stated rather than faked with zeros.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.security.analyzer import PhishVisionAnalyzer  # noqa: E402

VAL = PROJECT_ROOT / "data" / "clean_split_v2" / "val"
CLASSES = ("legitimate", "phishing")
BOOTSTRAP = 2000
SEED = 42


def auc(labels, scores) -> float:
    positives = [s for s, y in zip(scores, labels) if y == 1]
    negatives = [s for s, y in zip(scores, labels) if y == 0]
    if not positives or not negatives:
        return float("nan")
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def bootstrap_auc(labels, scores, rng):
    values = []
    n = len(labels)
    for _ in range(BOOTSTRAP):
        idx = rng.integers(0, n, n).tolist()
        values.append(auc([labels[i] for i in idx], [scores[i] for i in idx]))
    values = [v for v in values if not np.isnan(v)]
    values.sort()
    return (round(values[int(0.025 * len(values))], 4),
            round(values[int(0.975 * len(values)) - 1], 4))


def calibration(probabilities, labels, bins=5):
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    ece = 0.0
    n = len(labels)

    for low, high in zip(edges[:-1], edges[1:]):
        members = [(p, y) for p, y in zip(probabilities, labels)
                   if low <= p < high or (high == 1.0 and p == 1.0)]
        if not members:
            continue
        mean_p = float(np.mean([p for p, _ in members]))
        observed = float(np.mean([y for _, y in members]))
        ece += len(members) / n * abs(observed - mean_p)
        rows.append({"bin": f"{low:.1f}-{high:.1f}", "n": len(members),
                     "mean_predicted": round(mean_p, 4), "observed_rate": round(observed, 4)})

    brier = float(np.mean([(p - y) ** 2 for p, y in zip(probabilities, labels)]))
    return rows, round(ece, 4), round(brier, 4)


def main() -> int:
    analyzer = PhishVisionAnalyzer()

    labels, text_scores, cnn_scores, combined = [], [], [], []

    for label, name in enumerate(CLASSES):
        folder = VAL / name
        images = sorted(p for p in folder.glob("*")
                        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
        print(f"{name}: {len(images)} images")

        for path in images:
            with Image.open(path) as handle:
                result = analyzer.analyze(handle.convert("RGB"))

            labels.append(label)
            text_scores.append(float(result["text_analysis"]["score"]))
            cnn_scores.append(float(result["cnn_analysis"]["phishing_probability"] or 0.0))
            combined.append(float(result["risk"]["overall_score"]))

    rng = np.random.default_rng(SEED)

    out = PROJECT_ROOT / "results" / "component_diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "scores.json").write_text(json.dumps(
        {"labels": labels, "text": text_scores, "cnn": cnn_scores, "combined": combined}
    ), encoding="utf-8")
    print("per-image scores cached at", out / "scores.json")

    diagnostics = {}
    for name, scores in (("text", text_scores), ("cnn", cnn_scores), ("combined", combined)):
        point = auc(labels, scores)
        low, high = bootstrap_auc(labels, scores, rng)
        diagnostics[name] = {"auc": round(point, 4), "ci": [low, high]}

    binned, ece, brier = calibration(cnn_scores, labels)
    majority = max(labels.count(0), labels.count(1)) / len(labels)

    summary = {
        "split": "val",
        "n": len(labels),
        "class_counts": {"legitimate": labels.count(0), "phishing": labels.count(1)},
        "majority_class_accuracy": round(majority, 4),
        "component_auc": diagnostics,
        "url_component": "absent - no URLs supplied for dataset images; AUC undefined",
        "calibration": {"bins": binned, "ece": ece, "brier": brier},
        "notes": [
            "CNN weights were selected on this split, so its AUC is mildly optimistic.",
            "Images are not independent (same sources/kits), so bootstrap intervals are optimistic.",
        ],
    }

    out = PROJECT_ROOT / "results" / "component_diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# Component diagnostics — PhishVision validation split",
        "",
        f"n={len(labels)} (legitimate {labels.count(0)}, phishing {labels.count(1)}). "
        f"Majority-class accuracy {majority:.4f}.",
        "",
        "| Signal | ROC AUC | 95% bootstrap CI |",
        "|---|---|---|",
    ]
    for name in ("text", "cnn", "combined"):
        row = diagnostics[name]
        lines.append(f"| {name} | {row['auc']:.4f} | {row['ci'][0]:.4f}–{row['ci'][1]:.4f} |")

    lines += [
        "",
        "URL component: **absent** — dataset images have no URL, so its AUC is",
        "undefined. The combined score is therefore 0.30·text + 0.40·CNN rescaled,",
        "not the full 30/30/40.",
        "",
        "## CNN calibration",
        "",
        f"Brier {brier}, ECE {ece} (5 bins).",
        "",
        "| Bin | n | Mean predicted | Observed rate |",
        "|---|---|---|---|",
    ]
    for row in binned:
        lines.append(f"| {row['bin']} | {row['n']} | {row['mean_predicted']} | {row['observed_rate']} |")

    lines += [
        "",
        "## Reading this",
        "",
        f"- Chance AUC is 0.5; the text heuristic scores {diagnostics['text']['auc']:.3f}, the CNN "
        f"{diagnostics['cnn']['auc']:.3f}.",
        "- Whether the CNN earns its 40% weight is a decision for Phase 4 under the",
        "  pre-registered demotion rule, not a conclusion from this table alone.",
        "- ECE with n=83 across 5 bins is a coarse estimate; the interval is wide.",
        "",
        "## Limits",
        "",
        "- CNN selected on this split: mildly optimistic.",
        "- Samples not independent (source/kit clustering): bootstrap CIs optimistic.",
        "- No URL component exists here, so the platform's full weighting is untested.",
    ]

    docs = PROJECT_ROOT / "docs" / "measurements"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "component-diagnostics-2026-10-24.md").write_text("\n".join(lines) + "\n",
                                                             encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
