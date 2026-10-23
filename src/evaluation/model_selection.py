"""Promotion rule for candidate model checkpoints.

Kept separate from the evaluation script so the rule itself is testable
without torch, a dataset, or a checkpoint.
"""

from __future__ import annotations

MIN_F1_GAIN = 0.02


def select_promotion(rows, baseline, min_f1_gain: float = MIN_F1_GAIN):
    """Return the best eligible candidate, or None.

    A row is eligible when it is not the baseline, its F1 improves on the
    baseline by at least ``min_f1_gain`` absolute points, and its recall does
    not drop below the baseline's. Ties are broken by higher F1.
    """
    if baseline is None:
        raise ValueError("baseline row is required")

    eligible = [
        row
        for row in rows
        if row["model"] != baseline["model"]
        and row["f1"] >= baseline["f1"] + min_f1_gain
        and row["recall"] >= baseline["recall"]
    ]

    if not eligible:
        return None

    return max(eligible, key=lambda row: (row["f1"], row["recall"]))
