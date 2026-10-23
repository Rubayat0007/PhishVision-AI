"""Tests for the model promotion rule (torch-free)."""

import pytest

from src.evaluation.model_selection import select_promotion

BASELINE = {"model": "v2", "f1": 0.71, "recall": 0.88}


def row(model, f1, recall):
    return {"model": model, "f1": f1, "recall": recall}


def test_improvement_with_recall_held_is_eligible():
    candidate = row("candidate", 0.76, 0.90)

    assert select_promotion([BASELINE, candidate], BASELINE) == candidate


def test_recall_drop_disqualifies_even_with_f1_gain():
    candidate = row("candidate", 0.80, 0.81)

    assert select_promotion([BASELINE, candidate], BASELINE) is None


def test_insufficient_f1_gain_is_not_eligible():
    candidate = row("candidate", 0.72, 0.90)

    assert select_promotion([BASELINE, candidate], BASELINE) is None


def test_exact_threshold_is_eligible():
    candidate = row("candidate", BASELINE["f1"] + 0.02, BASELINE["recall"])

    assert select_promotion([BASELINE, candidate], BASELINE) == candidate


def test_baseline_never_promotes_itself():
    assert select_promotion([BASELINE], BASELINE) is None


def test_best_eligible_candidate_wins():
    first = row("a", 0.75, 0.90)
    second = row("b", 0.79, 0.89)

    assert select_promotion([BASELINE, first, second], BASELINE) == second


def test_ineligible_high_f1_candidate_does_not_block_eligible_one():
    ineligible = row("bad", 0.95, 0.10)
    eligible = row("good", 0.75, 0.90)

    assert select_promotion([BASELINE, ineligible, eligible], BASELINE) == eligible


def test_missing_baseline_raises():
    with pytest.raises(ValueError):
        select_promotion([], None)
