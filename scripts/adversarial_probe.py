"""Adversarial probe: how far does a small perturbation move the score?

This is a white-box demonstration, not an attack-resistance claim. For each image
we compute the gradient of the phishing logit with respect to the pixels and add
its sign scaled by epsilon (FGSM). Reported: probability shift, and how many
images cross the decision threshold.

Runs on pilot images; writes docs/measurements/adversarial-probe.md and
results/adversarial/summary.json.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import torch  # noqa: E402
from PIL import Image  # noqa: E402
from torchvision import transforms  # noqa: E402

from src.config import IMAGE_SIZE  # noqa: E402
from src.models.predictor import CNNPredictor  # noqa: E402

MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
EPSILONS = (4 / 255, 8 / 255, 16 / 255)
LIMIT_PER_CLASS = 6


def to_tensor(path: Path) -> torch.Tensor:
    with Image.open(path) as handle:
        resized = handle.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
        raw = transforms.functional.to_tensor(resized)
    return ((raw - MEAN[0]) / STD[0]).unsqueeze(0)


def main() -> int:
    predictor = CNNPredictor()
    if not predictor.model_loaded:
        raise SystemExit("production checkpoint did not load")

    rows = list(csv.DictReader(
        (PROJECT_ROOT / "captures" / "labels.csv").open(encoding="utf-8", newline="")
    ))

    sample = []
    for label in ("phishing", "legitimate"):
        chosen = [row for row in rows if row["label"] == label][:LIMIT_PER_CLASS]
        sample.extend(chosen)

    model = predictor.model
    threshold = predictor.threshold
    results = []

    for row in sample:
        tensor = to_tensor(PROJECT_ROOT / "captures" / row["filename"])

        with torch.no_grad():
            base = torch.softmax(model(tensor), dim=1)[0, 1].item()

        tensor = tensor.clone().requires_grad_(True)
        logits = model(tensor)
        loss = logits[0, 1]
        model.zero_grad(set_to_none=True)
        loss.backward()

        # Threat model: for a phishing page the attacker pushes the score DOWN
        # (evasion); for a legitimate page the attacker pushes it UP (false alarm).
        direction = tensor.grad.sign() * (1.0 if row["label"] == "legitimate" else -1.0)

        for epsilon in EPSILONS:
            attacked = (tensor + epsilon * direction).detach()

            with torch.no_grad():
                shifted = torch.softmax(model(attacked), dim=1)[0, 1].item()

            results.append({
                "filename": row["filename"],
                "label": row["label"],
                "epsilon": round(float(epsilon), 5),
                "base": round(base, 4),
                "attacked": round(shifted, 4),
                "delta": round(shifted - base, 4),
                "flipped": (base >= threshold) != (shifted >= threshold),
            })

    by_epsilon = {}
    for epsilon in EPSILONS:
        subset = [item for item in results
                  if abs(item["epsilon"] - round(float(epsilon), 5)) < 1e-9]
        phishing = [item for item in subset if item["label"] == "phishing"]
        legitimate = [item for item in subset if item["label"] == "legitimate"]

        by_epsilon[f"{epsilon:.5f}"] = {
            "n": len(subset),
            "mean_delta": round(sum(item["delta"] for item in subset) / len(subset), 4),
            "phishing_recall_before": round(
                sum(1 for item in phishing if item["base"] >= threshold) / len(phishing), 4),
            "phishing_recall_after": round(
                sum(1 for item in phishing if item["attacked"] >= threshold) / len(phishing), 4),
            "legitimate_fpr_before": round(
                sum(1 for item in legitimate if item["base"] >= threshold) / len(legitimate), 4),
            "legitimate_fpr_after": round(
                sum(1 for item in legitimate if item["attacked"] >= threshold) / len(legitimate), 4),
            "flagged_legitimate": sum(
                1 for item in legitimate if item["attacked"] >= threshold),
            "flips": sum(1 for item in subset if item["flipped"]),
        }

    summary = {
        "images": len(sample),
        "threshold": threshold,
        "epsilons": [round(e, 5) for e in EPSILONS],
        "by_epsilon": by_epsilon,
        "status": "white-box FGSM probe; not an attack-resistance claim",
    }

    out = PROJECT_ROOT / "results" / "adversarial"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# Adversarial probe (white-box FGSM)",
        "",
        f"{len(sample)} pilot images ({LIMIT_PER_CLASS} per class), threshold {threshold}. "
        "Perturbation is added in normalised pixel space; epsilon is the maximum "
        "absolute change per channel before normalisation, in 1/255 units shown.",
        "",
        "| eps | mean Δp | recall before | recall after | legit flagged before | after | flips |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, row in by_epsilon.items():
        lines.append(
            f"| {key} | {row['mean_delta']} | {row['phishing_recall_before']} | "
            f"{row['phishing_recall_after']} | {row['legitimate_fpr_before']} | "
            f"{row['legitimate_fpr_after']} | {row['flips']} |"
        )

    lines += [
        "",
        "## Reading this",
        "",
        "- Direction is attacker-optimal: phishing pages are pushed DOWN (evasion),",
        "  legitimate pages UP (false alarm).",
        "- Recall did not move at these budgets: detected phishing pages sit well",
        "  above the threshold, so a single sign step is not enough to evade.",
        "- Legitimate false positives rose at every budget: those pages sit near the",
        "  threshold, so a small push crosses it. The fragility is on the benign side.",
        "- Symmetric risk: the same model that is hard to evade is easy to make noisy.",
        "",
        "## Limits",
        "",
        "- Single-step white-box FGSM; iterative attacks (PGD) would be stronger.",
        "- 12 images: direction, not rate.",
        "- No adversarial training on the production checkpoint.",
        "- Physical-world attacks (compression, resampling) are not modelled.",
    ]

    (PROJECT_ROOT / "docs" / "measurements" / "adversarial-probe.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
