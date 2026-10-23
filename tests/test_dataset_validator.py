"""Tests for the dataset validator, using synthetic images.

Content is irrelevant to these checks; they cover structure discovery,
counting, duplicate detection, corruption detection, and exit codes.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts" / "validate_dataset.py"

sys.path.insert(0, str(REPO / "scripts"))

from validate_dataset import validate  # noqa: E402


def write_image(path, colour="white", size=(6, 6)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, colour).save(path)
    return path


@pytest.fixture
def dataset(tmp_path):
    root = tmp_path / "dataset"

    write_image(root / "train" / "legitimate" / "a.png", "white")
    write_image(root / "train" / "phishing" / "b.png", "black")
    write_image(root / "validation" / "legitimate" / "c.png", "red")
    write_image(root / "validation" / "phishing" / "d.png", "blue")
    write_image(root / "test" / "legitimate" / "e.png", "green")
    write_image(root / "test" / "phishing" / "f.png", "yellow")

    return root


def test_clean_dataset_validates(dataset):
    report = validate(dataset)

    assert report["valid"] is True, report["errors"]
    assert report["splits"]["train"] == {"legitimate": 1, "phishing": 1}
    assert report["totals"]["images"] == 6
    assert report["cross_split_duplicates"] == []
    assert report["corrupt_files"] == []


def test_cross_split_duplicate_content_is_leakage(tmp_path):
    root = tmp_path / "dataset"
    write_image(root / "train" / "legitimate" / "a.png", "white")
    write_image(root / "train" / "phishing" / "b.png", "black")
    write_image(root / "test" / "legitimate" / "copy.png", "white")

    report = validate(root)

    assert report["valid"] is False
    assert report["cross_split_duplicates"]
    assert any("cross split" in error for error in report["errors"])


def test_corrupt_image_is_reported(tmp_path):
    root = tmp_path / "dataset"
    write_image(root / "train" / "legitimate" / "a.png", "white")
    write_image(root / "train" / "phishing" / "b.png", "black")
    (root / "test" / "legitimate").mkdir(parents=True)
    (root / "test" / "phishing").mkdir(parents=True)
    (root / "test" / "legitimate" / "broken.png").write_bytes(b"not an image")

    report = validate(root)

    assert report["valid"] is False
    assert report["corrupt_files"] == ["test/legitimate/broken.png"]


def test_missing_class_directory_is_reported(tmp_path):
    root = tmp_path / "dataset"
    write_image(root / "train" / "legitimate" / "a.png", "white")

    report = validate(root)

    assert report["valid"] is False
    assert any("missing class" in error for error in report["errors"])


def test_missing_root_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate(tmp_path / "absent")


def test_cli_writes_manifest_and_exits_zero(dataset, tmp_path):
    output = tmp_path / "manifest.json"

    result = subprocess.run(
        [sys.executable, str(TOOL), str(dataset), "--json-output", str(output)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["valid"] is True
    assert manifest["totals"]["images"] == 6


def test_cli_exits_one_on_failures(tmp_path):
    root = tmp_path / "dataset"
    write_image(root / "train" / "legitimate" / "a.png", "white")

    result = subprocess.run(
        [sys.executable, str(TOOL), str(root)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 1
    assert "missing class" in result.stderr


def test_cli_exits_two_on_missing_root(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL), str(tmp_path / "absent")],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 2
    assert "not found" in result.stderr.lower()
