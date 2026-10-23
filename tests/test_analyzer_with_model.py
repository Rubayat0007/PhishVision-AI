"""Live-model analyzer tests: the full path, including the production CNN.

Skipped unless the provisioned checkpoint is present at the configured
path. Deliberately does **not** download anything: network access inside a
test suite makes results irreproducible, so provisioning stays a separate,
explicit step (``scripts/provision_model.py``).
"""

import pytest

pytest.importorskip("torch")
pytest.importorskip("easyocr")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from src.config import ACTIVE_MODEL_PATH  # noqa: E402
from src.models.integrity import PRODUCTION_MODEL_SHA256  # noqa: E402
from src.security.analyzer import PhishVisionAnalyzer  # noqa: E402

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not ACTIVE_MODEL_PATH.is_file(),
        reason=f"production checkpoint not provisioned at {ACTIVE_MODEL_PATH}",
    ),
]

SUSPICIOUS_URL = "http://192.168.1.10/login/verify-account"


@pytest.fixture(scope="module")
def result():
    font = ImageFont.load_default(size=46)
    image = Image.new("RGB", (1200, 520), "white")
    draw = ImageDraw.Draw(image)

    for index, line in enumerate([
        "SECURITY ALERT",
        "Verify your account and enter your password",
    ]):
        draw.text((50, 40 + index * 100), line, fill="black", font=font)

    analyzer = PhishVisionAnalyzer()

    assert analyzer.cnn.model_loaded, "provisioned checkpoint failed to load"

    return analyzer.analyze(image, SUSPICIOUS_URL)


def test_loaded_model_reports_verified_provenance(result, ):
    model = result["model"]

    assert model["loaded"] is True
    assert model["sha256"] == PRODUCTION_MODEL_SHA256
    assert model["threshold"] == 0.35


def test_no_component_degraded(result):
    assert result["security_assessment"]["component_errors"] == []
    assert result["cnn_analysis"]["model_loaded"] is True


def test_cnn_output_is_a_probability_vector(result):
    cnn = result["cnn_analysis"]

    assert cnn["prediction"] in {"phishing", "legitimate"}
    assert 0.0 <= cnn["phishing_probability"] <= 1.0
    assert cnn["phishing_probability"] + cnn["legitimate_probability"] == pytest.approx(1.0)
    expected = "phishing" if cnn["phishing_probability"] >= cnn["threshold"] else "legitimate"
    assert cnn["prediction"] == expected


def test_risk_includes_the_visual_component(result):
    text = result["text_analysis"]["score"]
    url = result["url_analysis"]["score"]
    cnn = result["cnn_analysis"]["phishing_probability"] * 100

    expected = round(
        round(text, 2) * 0.30 + round(url, 2) * 0.30 + round(cnn, 2) * 0.40,
        2,
    )

    assert result["risk"]["cnn_score"] == round(cnn, 2)
    assert result["risk"]["overall_score"] == expected


def test_assessment_may_cite_the_cnn(result):
    assessment = result["security_assessment"]

    assert assessment["finding_count"] == len(assessment["evidence"])
    assert assessment["component_scores"]["cnn"] == result["risk"]["cnn_score"]
    assert assessment["verdict"] == f"{result['risk']['risk_level']} RISK"
