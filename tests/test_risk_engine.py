"""Contract tests for the heuristic risk engine.

The composite score is a weighted heuristic (text 30%, URL 30%, CNN 40%),
not a calibrated probability. These tests pin the published weights,
clamping behaviour, and risk-level boundaries.
"""

import pytest

from src.security.risk_engine import calculate_risk


def test_zero_scores_are_minimal():
    result = calculate_risk(0, 0, 0)

    assert result["overall_score"] == 0.0
    assert result["risk_level"] == "MINIMAL"


def test_weights_are_30_30_40():
    assert calculate_risk(100, 0, 0)["overall_score"] == 30.0
    assert calculate_risk(0, 100, 0)["overall_score"] == 30.0
    assert calculate_risk(0, 0, 100)["overall_score"] == 40.0


def test_all_maximum_scores_produce_100():
    result = calculate_risk(100, 100, 100)

    assert result["overall_score"] == 100.0
    assert result["risk_level"] == "HIGH"


def test_inputs_are_clamped_to_0_100():
    result = calculate_risk(200, -50, 150)

    assert result["text_score"] == 100.0
    assert result["url_score"] == 0.0
    assert result["cnn_score"] == 100.0
    assert result["overall_score"] == 70.0
    assert result["risk_level"] == "HIGH"


def test_risk_boundaries():
    assert calculate_risk(100, 0, 0)["risk_level"] == "MEDIUM"
    assert calculate_risk(0, 0, 70)["risk_level"] == "LOW"
    assert calculate_risk(100, 100, 25)["risk_level"] == "HIGH"
    assert calculate_risk(0, 0, 1)["risk_level"] == "LOW"


def test_numeric_strings_are_accepted():
    result = calculate_risk("50", "25", "10")

    assert result["overall_score"] == 26.5
    assert result["risk_level"] == "LOW"


def test_cnn_score_is_returned():
    result = calculate_risk(20, 30, 40)

    assert result["cnn_score"] == 40.0
    assert result["overall_score"] == 31.0


def test_non_numeric_input_is_rejected():
    with pytest.raises(ValueError):
        calculate_risk("not-a-number", 0, 0)


def test_scores_are_rounded_to_two_decimals():
    result = calculate_risk(1 / 3, 1 / 3, 1 / 3)

    assert all(
        len(str(value).split(".")[1]) <= 2
        for value in (
            result["text_score"],
            result["url_score"],
            result["cnn_score"],
        )
    )
