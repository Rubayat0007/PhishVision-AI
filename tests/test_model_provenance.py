"""Tests for the provenance record attached to analyzer results."""

from src.models.integrity import build_provenance


def test_provenance_defaults_to_the_production_model():
    record = build_provenance(loaded=True, sha256="A" * 64, threshold=0.35)

    assert record == {
        "name": "phishvision_cnn_v2",
        "loaded": True,
        "sha256": "A" * 64,
        "threshold": 0.35,
    }


def test_provenance_reports_an_unloaded_model():
    record = build_provenance(loaded=False, sha256=None, threshold=0.35)

    assert record["loaded"] is False
    assert record["sha256"] is None


def test_provenance_coerces_threshold_to_float():
    assert build_provenance(loaded=True, sha256=None, threshold="0.5")["threshold"] == 0.5


def test_provenance_name_can_be_overridden():
    record = build_provenance(loaded=True, sha256=None, threshold=0.35, name="candidate")

    assert record["name"] == "candidate"
