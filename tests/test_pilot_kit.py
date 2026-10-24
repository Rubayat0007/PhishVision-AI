"""Tests for the pilot capture kit."""

import csv
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts" / "make_pilot_kit.py"


def test_creates_labels_header_and_protocol(tmp_path):
    target = tmp_path / "captures"

    result = subprocess.run([sys.executable, str(TOOL), "--directory", str(target)],
                            capture_output=True, text=True, timeout=60)

    assert result.returncode == 0, result.stderr
    assert (target / "labels.csv").is_file()
    assert (target / "PROTOCOL.txt").is_file()

    with (target / "labels.csv").open(encoding="utf-8") as handle:
        header = next(csv.reader(handle))

    assert header == ["filename", "label", "label_basis", "label_confidence",
                      "registered_domain", "brand_cluster", "kit_cluster",
                      "captured_at", "source", "license", "split"]

    protocol = (target / "PROTOCOL.txt").read_text(encoding="utf-8")
    assert "sealed" in protocol
    assert "split" in protocol.lower()


def test_does_not_overwrite_existing_labels(tmp_path):
    target = tmp_path / "captures"
    target.mkdir()
    labels = target / "labels.csv"
    labels.write_text("existing,content\n", encoding="utf-8")

    subprocess.run([sys.executable, str(TOOL), "--directory", str(target)],
                   capture_output=True, text=True, timeout=60)

    assert labels.read_text(encoding="utf-8") == "existing,content\n"
