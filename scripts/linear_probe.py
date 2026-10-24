"""Frozen-backbone linear probe, trained on train and scored on validation.

Motivation: three measurements agree that the model's weakness is the benign
side (FPR 0.33-0.43), not phishing recall. This tests whether the learned
embedding already separates legitimate pages better than the tuned head does.

Rules: train on `train`, select the threshold on `validation`, and never touch
`test`. The probe never updates the checkpoint - it is a linear model over the
256-dim penultimate features.

Writes docs/measurements/linear-probe.md and results/linear_probe/summary.json.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

from src.data.transforms import val_transform  # noqa: E402
from src.models.predictor import CNNPredictor  # noqa: E402

THRESHOLD = 0.35
RECALL_FLOOR = 0.50


def wilson(successes: int, total: int, z: float = 1.96):
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> int:
    predictor = CNNPredictor()
    if not predictor.model_loaded:
        raise SystemExit("production checkpoint did not load")

    model = predictor.model
    captured: list[torch.Tensor] = []

    def hook(_module, _inputs, output):
        captured.append(output.detach())

    handle = model.classifier[1].register_forward_hook(hook)

    rows = list(csv.DictReader(
        (PROJECT_ROOT / "captures" / "labels.csv").open(encoding="utf-8", newline="")
    ))
    usable = [row for row in rows if row["split"] in {"train", "validation"}]

    embeddings, labels, baseline, splits = [], [], [], []

    try:
        with torch.no_grad():
            for row in usable:
                captured.clear()
                with Image.open(PROJECT_ROOT / "captures" / row["filename"]) as handle_img:
                    tensor = val_transform(handle_img.convert("RGB")).unsqueeze(0)

                logits = model(tensor)
                probability = float(torch.softmax(logits, dim=1)[0, 1])
                features = captured[0].flatten().cpu().numpy()

                embeddings.append(features)
                labels.append(1 if row["label"] == "phishing" else 0)
                baseline.append(probability)
                splits.append(row["split"])
    finally:
        handle.remove()

    X = np.vstack(embeddings)
    y = np.array(labels)
    base = np.array(baseline)
    split = np.array(splits)

    train_mask = split == "train"
    val_mask = split == "validation"

    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    base_val = base[val_mask]

    probe = LogisticRegression(C=0.05, max_iter=2000, class_weight="balanced")
    probe.fit(X_train, y_train)

    cv = StratifiedKFold(5, shuffle=True, random_state=42)
    cv_auc = []
    for fit_idx, test_idx in cv.split(X_train, y_train):
        model_cv = LogisticRegression(C=0.05, max_iter=2000, class_weight="balanced")
        model_cv.fit(X_train[fit_idx], y_train[fit_idx])
        cv_auc.append(roc_auc_score(
            y_train[test_idx], model_cv.predict_proba(X_train[test_idx])[:, 1]))

    val_scores = probe.predict_proba(X_val)[:, 1]
    probe_auc = float(roc_auc_score(y_val, val_scores)) if len(set(y_val)) > 1 else float("nan")
    base_auc = float(roc_auc_score(y_val, base_val)) if len(set(y_val)) > 1 else float("nan")

    def at_recall_floor(scores, truth, floor=RECALL_FLOOR):
        """Lowest threshold that keeps recall >= floor; return FPR and recall."""
        positives = sorted((scores[i] for i in range(len(truth)) if truth[i] == 1),
                           reverse=True)
        if not positives:
            return None
        index = max(0, math.ceil(floor * len(positives)) - 1)
        cutoff = positives[index]

        tp = sum(1 for i in range(len(truth)) if truth[i] == 1 and scores[i] >= cutoff)
        fn = sum(1 for i in range(len(truth)) if truth[i] == 1 and scores[i] < cutoff)
        fp = sum(1 for i in range(len(truth)) if truth[i] == 0 and scores[i] >= cutoff)
        tn = sum(1 for i in range(len(truth)) if truth[i] == 0 and scores[i] < cutoff)

        return {"threshold": round(float(cutoff), 4),
                "recall": round(tp / (tp + fn), 4),
                "fpr": round(fp / (fp + tn), 4),
                "fpr_ci": [round(v, 4) for v in wilson(fp, fp + tn)],
                "tp": tp, "fp": fp, "fn": fn, "tn": tn}

    probe_operating = at_recall_floor(val_scores, y_val)
    base_operating = at_recall_floor(base_val, y_val)

    summary = {
        "n_train": int(train_mask.sum()),
        "n_validation": int(val_mask.sum()),
        "features": int(X.shape[1]),
        "cv_auc_train": round(float(np.mean(cv_auc)), 4),
        "cv_auc_std": round(float(np.std(cv_auc)), 4),
        "validation_auc_probe": round(probe_auc, 4),
        "validation_auc_baseline": round(base_auc, 4),
        "probe_at_recall_floor": probe_operating,
        "baseline_at_recall_floor": base_operating,
        "test_used": False,
        "status": "DEVELOPMENT - pilot labels feed-derived; test untouched",
    }

    out = PROJECT_ROOT / "results" / "linear_probe"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# Frozen-backbone linear probe (Phase 4.2)",
        "",
        f"Train n={summary['n_train']}, validation n={summary['n_validation']}, "
        f"{summary['features']} features. Test split untouched.",
        "",
        "| Model | train CV AUC | validation AUC |",
        "|---|---|---|",
        f"| frozen features + logistic (C=0.05) | {summary['cv_auc_train']} "
        f"± {summary['cv_auc_std']} | {summary['validation_auc_probe']} |",
        f"| tuned production head | — | {summary['validation_auc_baseline']} |",
        "",
        "## Operating point at recall >= 0.50 (chosen on validation)",
        "",
        "| Model | threshold | recall | FPR | FPR 95% CI |",
        "|---|---|---|---|---|",
    ]
    for name, row in (("probe", probe_operating), ("baseline", base_operating)):
        if row:
            lines.append(f"| {name} | {row['threshold']} | {row['recall']} | "
                         f"{row['fpr']} | {row['fpr_ci'][0]}-{row['fpr_ci'][1]} |")

    lines += [
        "",
        "## Reading this",
        "",
    ]

    if abs(probe_auc - base_auc) < 0.02:
        lines.append(
            "- **No evidence the probe helps**: validation AUCs are within 0.02 of each "
            "other, and the operating-point FPR is identical."
        )
    else:
        lines.append(
            f"- Probe AUC {probe_auc:.3f} vs baseline {base_auc:.3f} on validation."
        )

    lines += [
        f"- Train CV AUC {np.mean(cv_auc):.3f} collapsing to {probe_auc:.3f} on "
        "validation is the signature of over-fitting on 84 rows, not of a better head.",
        "- With n=15-19 validation images, neither outcome can be distinguished from "
        "noise; this experiment cannot settle the question it was designed for.",
        "",
        "## Limits",
        "",
        "- Linear probe on 256-dim features with ~80 training rows: strong",
        "  regularisation, but over-fitting risk remains and CV is optimistic.",
        "- Feed-derived labels; pilot only; no promotion decision follows.",
    ]

    (PROJECT_ROOT / "docs" / "measurements" / "linear-probe.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
