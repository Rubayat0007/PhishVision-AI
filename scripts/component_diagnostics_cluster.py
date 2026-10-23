"""Component diagnostics on the cluster-disjoint split.

The earlier component AUCs were measured on a split with near-duplicate
leakage. This recomputes them with whole perceptual clusters assigned to one
split only, reusing the clustering from leakage_free_eval.py.

Runtime is dominated by OCR (about 10-20 s per image on CPU), so this is meant
to run as a background job; nothing is committed by the script.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.security.analyzer import PhishVisionAnalyzer  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "leakage_free_eval", PROJECT_ROOT / "scripts" / "leakage_free_eval.py"
)
_lfe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lfe)


def auc(labels, scores):
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return float("nan")
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def bootstrap(labels, scores, rng, rounds=2000):
    values = []
    n = len(labels)
    for _ in range(rounds):
        idx = rng.integers(0, n, n).tolist()
        v = auc([labels[i] for i in idx], [scores[i] for i in idx])
        if not np.isnan(v):
            values.append(v)
    values.sort()
    return round(values[int(0.025 * len(values))], 4), round(values[int(0.975 * len(values)) - 1], 4)


def calibration(probabilities, labels, bins=5):
    edges = np.linspace(0, 1, bins + 1)
    rows, ece, n = [], 0.0, len(labels)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "results" / "component_diagnostics_cluster")
    args = parser.parse_args()

    records = _lfe.collect()
    groups = _lfe.cluster(records)
    assignment = _lfe.assign_splits(records, groups)

    index_to_split = {i: split for key, split in assignment.items() for i in key}
    test = [records[i] for i in range(len(records)) if index_to_split.get(i) == "test"]
    print(f"cluster-disjoint test images: {len(test)}", flush=True)

    analyzer = PhishVisionAnalyzer()
    labels, text_scores, cnn_scores, combined = [], [], [], []

    for count, record in enumerate(test, 1):
        with Image.open(record["path"]) as handle:
            result = analyzer.analyze(handle.convert("RGB"))

        labels.append(record["label"])
        text_scores.append(float(result["text_analysis"]["score"]))
        cnn_scores.append(float(result["cnn_analysis"]["phishing_probability"] or 0.0))
        combined.append(float(result["risk"]["overall_score"]))

        if count % 10 == 0:
            print(f"  {count}/{len(test)}", flush=True)

    rng = np.random.default_rng(42)
    diagnostics = {}
    for name, scores in (("text", text_scores), ("cnn", cnn_scores), ("combined", combined)):
        point = auc(labels, scores)
        low, high = bootstrap(labels, scores, rng)
        diagnostics[name] = {"auc": round(float(point), 4), "ci": [low, high]}

    binned, ece, brier = calibration(cnn_scores, labels)

    summary = {
        "split": "cluster-disjoint test",
        "clusters": len(groups),
        "n": len(labels),
        "class_counts": {"legitimate": labels.count(0), "phishing": labels.count(1)},
        "component_auc": diagnostics,
        "url_component": "absent - dataset images carry no URL",
        "calibration": {"bins": binned, "ece": ece, "brier": brier},
        "note": "No cluster spans two splits; compare with the leaky-split figures in R-PV-components-01.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Component diagnostics — cluster-disjoint test split",
        "",
        f"n={len(labels)} (legitimate {labels.count(0)}, phishing {labels.count(1)}); "
        f"{len(groups)} perceptual clusters, none spanning splits.",
        "",
        "| Signal | ROC AUC | 95% bootstrap CI |",
        "|---|---|---|",
    ]
    for name in ("text", "cnn", "combined"):
        row = diagnostics[name]
        lines.append(f"| {name} | {row['auc']:.4f} | {row['ci'][0]:.4f}-{row['ci'][1]:.4f} |")
    lines += [
        "",
        "URL component absent: no URLs for dataset images.",
        "",
        f"Calibration: Brier {brier}, ECE {ece}.",
        "",
        "| Bin | n | Mean predicted | Observed rate |",
        "|---|---|---|---|",
    ]
    for row in binned:
        lines.append(f"| {row['bin']} | {row['n']} | {row['mean_predicted']} | {row['observed_rate']} |")

    lines += [
        "",
        "## Comparison with the leaky split",
        "",
        "| Signal | leaky test AUC | cluster-disjoint AUC |",
        "|---|---|---|",
        "| text | 0.7419 | %s |" % diagnostics["text"]["auc"],
        "| CNN | 0.7424 | %s |" % diagnostics["cnn"]["auc"],
        "| combined | 0.8041 | %s |" % diagnostics["combined"]["auc"],
        "",
        "Residual leakage cannot be excluded: crops and overlays survive dHash.",
    ]

    docs = PROJECT_ROOT / "docs" / "measurements"
    (docs / "component-diagnostics-cluster-2026-10-24.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
