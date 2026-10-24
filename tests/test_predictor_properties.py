"""Robustness properties the platform assumes about the predictor.

Slow tests: they load the production checkpoint. Marked `slow` so the fast suite
stays quick in CI without torch.
"""

from __future__ import annotations

import pytest
from PIL import Image

pytest.importorskip("torch")

from src.models.predictor import CNNPredictor  # noqa: E402

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def predictor():
    model = CNNPredictor()
    if not model.model_loaded:
        pytest.skip("production checkpoint did not load")
    return model


def image(colour="white", size=(160, 90), mode="RGB"):
    return Image.new(mode, size, colour)


def test_prediction_is_deterministic(predictor):
    first = predictor.predict(image())
    second = predictor.predict(image())

    assert first["phishing_probability"] == second["phishing_probability"]


def test_probabilities_sum_to_one(predictor):
    result = predictor.predict(image("blue"))

    total = result["phishing_probability"] + result["legitimate_probability"]
    assert total == pytest.approx(1.0, abs=1e-6)


def test_prediction_matches_threshold(predictor):
    result = predictor.predict(image("black"))
    expected = (
        "phishing"
        if result["phishing_probability"] >= predictor.threshold
        else "legitimate"
    )

    assert result["prediction"] == expected


def test_grayscale_and_rgba_are_accepted(predictor):
    grey = predictor.predict(image("white", mode="L"))
    rgba = predictor.predict(image("white", mode="RGBA"))

    assert grey["prediction"] == rgba["prediction"]


def test_tiny_and_large_images_are_accepted(predictor):
    tiny = predictor.predict(image(size=(8, 8)))
    large = predictor.predict(image(size=(1920, 1080)))

    for result in (tiny, large):
        assert 0.0 <= result["phishing_probability"] <= 1.0


def test_non_image_input_is_rejected(predictor):
    with pytest.raises(TypeError):
        predictor.predict(b"not an image")


def test_uniform_colour_does_not_crash(predictor):
    for colour in ("white", "black", "red", "green"):
        result = predictor.predict(image(colour))
        assert 0.0 <= result["phishing_probability"] <= 1.0


def test_repeat_calls_do_not_accumulate_state(predictor):
    results = [predictor.predict(image("white"))["phishing_probability"]
               for _ in range(3)]

    assert len(set(results)) == 1
