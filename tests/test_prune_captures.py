"""Tests for blank detection and label dedupe."""

import csv
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from prune_captures import dedupe_labels, is_blank  # noqa: E402

COLUMNS = ["filename", "label", "label_basis", "label_confidence",
           "registered_domain", "brand_cluster", "kit_cluster",
           "captured_at", "source", "license", "split"]


def make(path: Path, colour):
    Image.new("RGB", (64, 48), colour).save(path)


def test_white_page_is_blank(tmp_path):
    path = tmp_path / "white.png"
    make(path, "white")

    assert is_blank(path)


def test_content_page_is_not_blank(tmp_path):
    path = tmp_path / "dark.png"
    make(path, "black")

    assert not is_blank(path)


def test_dedupe_keeps_first_row(tmp_path):
    labels = tmp_path / "labels.csv"
    rows = [
        {"filename": "a.png"}, {"filename": "a.png"}, {"filename": "b.png"},
    ]
    for row in rows:
        for column in COLUMNS:
            row.setdefault(column, "x")

    with labels.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    assert dedupe_labels(labels, apply=False) == 1
    assert dedupe_labels(labels, apply=True) == 1

    with labels.open(encoding="utf-8") as handle:
        kept = [row["filename"] for row in csv.DictReader(handle)]

    assert kept == ["a.png", "b.png"]
