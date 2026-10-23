"""Analyzer contract tests that do not require the production checkpoint.

The CNN predictor is pointed at a path that does not exist, which is the
analyzer's documented "model unavailable" branch. This exercises OCR,
suspicious-text detection, URL analysis, risk arithmetic, the assessment
response contract, the CNN entry in ``component_errors``, and the unified
adapter's handling of an unavailable visual component.

Skipped automatically when torch or EasyOCR is unavailable (e.g. in CI).
"""

import pytest

pytest.importorskip("torch")
pytest.importorskip("easyocr")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from src.models.predictor import CNNPredictor  # noqa: E402
from src.security.analyzer import PhishVisionAnalyzer  # noqa: E402

SUSPICIOUS_URL = "http://192.168.1.10/login/verify-account"

pytestmark = pytest.mark.slow

EXPECTED_KEYS = sorted(
    [
        "extracted_text",
        "text_analysis",
        "url_analysis",
        "cnn_analysis",
        "risk",
        "security_assessment",
        "model",
    ]
)


@pytest.fixture(scope="module")
def screenshot():
    font = ImageFont.load_default(size=46)
    image = Image.new("RGB", (1200, 520), "white")
    draw = ImageDraw.Draw(image)

    lines = [
        "SECURITY ALERT",
        "Your account is suspended",
        "Verify your account and enter your password",
        "immediately",
    ]

    for index, line in enumerate(lines):
        draw.text((50, 40 + index * 100), line, fill="black", font=font)

    return image


@pytest.fixture(scope="module")
def analyzer():
    instance = PhishVisionAnalyzer()
    instance.cnn = CNNPredictor(model_path="definitely-missing.pth")
    return instance


@pytest.fixture(scope="module")
def result(analyzer, screenshot):
    return analyzer.analyze(screenshot, SUSPICIOUS_URL)


def test_result_contract(result):
    assert sorted(result) == EXPECTED_KEYS


def test_provenance_reports_unloaded_model(result):
    model = result["model"]

    assert model["loaded"] is False
    assert model["sha256"] is None
    assert model["threshold"] == 0.35


def test_cnn_analysis_is_unavailable_but_well_formed(result):
    cnn = result["cnn_analysis"]

    assert cnn["model_loaded"] is False
    assert cnn["prediction"] is None
    assert cnn["phishing_probability"] is None
    assert cnn["error"]


def test_component_errors_contains_one_cnn_entry(result):
    errors = result["security_assessment"]["component_errors"]

    assert len(errors) == 1
    assert errors[0]["component"] == "CNN"
    assert "not loaded" in errors[0]["error"].lower()


def test_text_analysis_detects_credentials(result):
    text = result["text_analysis"]

    assert result["extracted_text"].strip()
    assert "password" in text["matches"]
    assert text["is_suspicious"] is True
    assert text["score"] == 10 * len(text["matches"])


def test_url_analysis_detects_indicators(result):
    url = result["url_analysis"]

    assert {"uses_http", "ip_address"} <= set(url["indicators"])
    assert {"login", "verify", "account"} <= set(url["matched_keywords"])
    assert url["score"] == 15 * len(url["indicators"])


def test_risk_arithmetic_treats_missing_cnn_as_zero(result):
    text = result["text_analysis"]
    url = result["url_analysis"]
    risk = result["risk"]

    expected = round(text["score"] * 0.30 + url["score"] * 0.30, 2)

    assert risk["cnn_score"] == 0.0
    assert risk["overall_score"] == expected


def test_assessment_contract(result):
    assessment = result["security_assessment"]
    risk = result["risk"]

    for field in (
        "verdict",
        "risk_level",
        "overall_score",
        "evidence",
        "finding_count",
        "recommended_action",
        "component_scores",
        "component_errors",
    ):
        assert field in assessment

    assert assessment["finding_count"] == len(assessment["evidence"])
    assert all(finding["source"] != "CNN" for finding in assessment["evidence"])
    assert assessment["component_scores"]["cnn"] == 0.0
    assert all(
        {"source", "category", "severity", "evidence"} <= set(finding)
        for finding in assessment["evidence"]
    )
    assert assessment["verdict"] == f"{risk['risk_level']} RISK"
