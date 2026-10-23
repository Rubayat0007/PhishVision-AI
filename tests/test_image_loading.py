"""Tests for image loading and sample discovery (torch-free)."""

import pytest
from PIL import Image

from src.data.image_utils import load_image
from src.data.samples import discover_samples


def write_image(path, size=(8, 6), colour="white"):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, colour)
    image.save(path)
    return path


@pytest.fixture
def dataset_root(tmp_path):
    root = tmp_path / "dataset"

    write_image(root / "legitimate" / "b.png")
    write_image(root / "legitimate" / "a.png")
    write_image(root / "legitimate" / "nested" / "c.jpg")
    write_image(root / "phishing" / "z.png")
    (root / "legitimate" / "notes.txt").write_text("ignored", encoding="utf-8")

    return root


def test_discovery_is_sorted_and_labelled(dataset_root):
    samples = discover_samples(dataset_root)

    names = [(path.name, label) for path, label in samples]

    assert names == [
        ("a.png", 0),
        ("b.png", 0),
        ("c.jpg", 0),
        ("z.png", 1),
    ]


def test_discovery_ignores_unsupported_extensions(dataset_root):
    samples = discover_samples(dataset_root)

    assert all(path.suffix.lower() != ".txt" for path, _ in samples)


def test_discovery_requires_images(tmp_path):
    with pytest.raises(RuntimeError):
        discover_samples(tmp_path / "empty")


def test_discovery_skips_missing_class_directory(dataset_root):
    samples = discover_samples(dataset_root, class_names=("phishing",))

    assert [path.name for path, _ in samples] == ["z.png"]


def test_load_image_returns_rgb(tmp_path):
    path = write_image(tmp_path / "image.png", size=(10, 7), colour="red")

    image = load_image(path)

    assert image.mode == "RGB"
    assert image.size == (10, 7)


def test_load_image_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_image(tmp_path / "missing.png")


def test_load_image_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "image.gif"
    path.write_bytes(b"GIF89a")

    with pytest.raises(ValueError):
        load_image(path)


def test_load_image_reports_corrupt_file_with_path(tmp_path):
    path = tmp_path / "corrupt.png"
    path.write_bytes(b"not an image")

    with pytest.raises(RuntimeError) as error:
        load_image(path)

    assert "corrupt.png" in str(error.value)
