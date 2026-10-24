"""Tests for the dataset-manifest validator (Phase 2.1)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from validate_manifest import validate  # noqa: E402


def row(index, split="train", label="phishing", domain=None, brand=None, kit=None):
    return {
        "filename": f"img_{index:03d}.png",
        "sha256": f"{index:064x}",
        "phash": f"{index:016x}",
        "label": label,
        "label_basis": "screenshot of reported page",
        "label_confidence": 0.9,
        "registered_domain": domain or f"site{index}.example",
        "brand_cluster": brand or f"brand{index}",
        "kit_cluster": kit or f"kit{index}",
        "captured_at": "2026-10-20T10:00:00+00:00",
        "source": "pilot feed",
        "license": "research",
        "split": split,
    }


def manifest(rows):
    return {"schema_version": 1, "dataset_version": "v3-pilot", "images": rows}


def test_valid_pilot_passes():
    rows = [row(i, split=s) for i, s in enumerate(
        ["train"] * 20 + ["validation"] * 15 + ["test"] * 15)]

    result = validate(manifest(rows))

    assert result["valid"], result["errors"]
    assert result["images"] == 50


def test_duplicate_filename_rejected():
    rows = [row(1), row(2)]
    rows[1]["filename"] = rows[0]["filename"]

    assert not validate(manifest(rows))["valid"]


def test_duplicate_content_rejected():
    rows = [row(1), row(2)]
    rows[1]["sha256"] = rows[0]["sha256"]

    assert not validate(manifest(rows))["valid"]


def test_bad_label_rejected():
    rows = [row(1)]
    rows[0]["label"] = "suspicious"

    assert not validate(manifest(rows))["valid"]


def test_group_spanning_splits_rejected():
    rows = [row(1, split="train", domain="d", kit="k"),
            row(2, split="test", domain="d", kit="k")]

    result = validate(manifest(rows))

    assert not result["valid"]
    assert any("spans splits" in error for error in result["errors"])


def test_brand_crossing_train_and_test_rejected():
    rows = [row(1, split="train", brand="acme"),
            row(2, split="test", brand="acme")]

    assert not validate(manifest(rows))["valid"]


def test_bad_timestamp_rejected():
    rows = [row(1)]
    rows[0]["captured_at"] = "20 October 2026"

    assert not validate(manifest(rows))["valid"]


def test_missing_field_rejected():
    rows = [row(1)]
    del rows[0]["phash"]

    assert not validate(manifest(rows))["valid"]


def test_small_sealed_holdout_rejected():
    rows = [row(i, split="sealed") for i in range(20)]

    result = validate(manifest(rows))

    assert not result["valid"]


def test_cli_exit_codes(tmp_path):
    good = manifest([row(1)])
    path = tmp_path / "m.json"
    path.write_text(json.dumps(good), encoding="utf-8")

    ok = subprocess.run([sys.executable, str(REPO / "scripts" / "validate_manifest.py"),
                         str(path)], capture_output=True, text=True, timeout=60)
    assert ok.returncode == 0

    path.write_text("not json", encoding="utf-8")
    bad = subprocess.run([sys.executable, str(REPO / "scripts" / "validate_manifest.py"),
                          str(path)], capture_output=True, text=True, timeout=60)
    assert bad.returncode == 2
