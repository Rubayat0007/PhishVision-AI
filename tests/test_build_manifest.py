"""Tests for the manifest builder (labels supplied, hashes computed)."""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts" / "build_manifest.py"

COLUMNS = ["filename", "label", "label_basis", "label_confidence",
           "registered_domain", "brand_cluster", "kit_cluster",
           "captured_at", "source", "license", "split"]


def make_image(path: Path, colour):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 24), colour).save(path)


def write_labels(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def label_row(index, split="train", label="phishing"):
    return {
        "filename": f"shot_{index:03d}.png",
        "label": label,
        "label_basis": "screenshot of reported page",
        "label_confidence": "0.9",
        "registered_domain": f"site{index}.example",
        "brand_cluster": f"brand{index}",
        "kit_cluster": f"kit{index}",
        "captured_at": "2026-10-20T10:00:00+00:00",
        "source": "pilot",
        "license": "research",
        "split": split,
    }


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                          capture_output=True, text=True, timeout=120)


@pytest.fixture
def pilot(tmp_path):
    images = tmp_path / "images"
    colours = ["white", "black", "red", "green", "blue"]
    for index, colour in enumerate(colours):
        make_image(images / f"shot_{index:03d}.png", colour)

    labels = tmp_path / "labels.csv"
    write_labels(labels, [label_row(i) for i in range(len(colours))])
    return images, labels, tmp_path


def test_build_computes_hashes_and_passes(pilot):
    images, labels, tmp = pilot
    output = tmp / "manifest.json"

    result = run("--images-dir", images, "--labels", labels, "--output", output)

    assert result.returncode == 0, result.stderr

    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert len(manifest["images"]) == 5
    for row in manifest["images"]:
        assert len(row["sha256"]) == 64
        assert len(row["phash"]) == 16
        assert row["label"] == "phishing"


def test_identical_images_are_rejected(pilot):
    images, labels, tmp = pilot
    make_image(images / "copy.png", "white")
    rows = [label_row(0), label_row(9)]
    rows[1]["filename"] = "copy.png"
    write_labels(labels, rows)

    result = run("--images-dir", images, "--labels", labels,
                 "--output", tmp / "manifest.json")

    assert result.returncode == 1
    assert "duplicate content" in result.stderr


def test_missing_image_is_an_input_error(pilot):
    images, labels, tmp = pilot
    labels.write_text(labels.read_text(encoding="utf-8")
                      + "\n" + ",".join(["absent.png", "phishing", "basis", "0.9",
                                         "d.example", "b", "k",
                                         "2026-10-20T10:00:00+00:00", "s", "l", "train"]),
                      encoding="utf-8")

    result = run("--images-dir", images, "--labels", labels,
                 "--output", tmp / "manifest.json")

    assert result.returncode == 2
    assert "missing image" in result.stderr


def test_missing_column_is_an_input_error(tmp_path):
    images = tmp_path / "images"
    make_image(images / "shot_000.png", "white")
    labels = tmp_path / "bad.csv"
    labels.write_text("filename,label\nshot_000.png,phishing\n", encoding="utf-8")

    result = run("--images-dir", images, "--labels", labels,
                 "--output", tmp_path / "m.json")

    assert result.returncode == 2
    assert "missing columns" in result.stderr
