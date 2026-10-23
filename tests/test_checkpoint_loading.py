"""Tests for reading checkpoints as verified bytes."""

import hashlib

import pytest

from src.models.integrity import ModelIntegrityError, read_verified_checkpoint

CONTENT = b"checkpoint-bytes"
DIGEST = hashlib.sha256(CONTENT).hexdigest().upper()


@pytest.fixture
def checkpoint(tmp_path):
    path = tmp_path / "checkpoint.pth"
    path.write_bytes(CONTENT)
    return path


def test_returns_bytes_and_digest(checkpoint):
    data, digest = read_verified_checkpoint(checkpoint, expected_sha256=DIGEST)

    assert data == CONTENT
    assert digest == DIGEST


def test_mismatch_raises(checkpoint):
    with pytest.raises(ModelIntegrityError):
        read_verified_checkpoint(checkpoint, expected_sha256="0" * 64)


def test_bypass_returns_digest(checkpoint):
    data, digest = read_verified_checkpoint(
        checkpoint, expected_sha256="0" * 64, allow_unverified=True
    )

    assert data == CONTENT
    assert digest == DIGEST


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_verified_checkpoint(tmp_path / "absent.pth")


def test_verified_bytes_are_loadable(tmp_path):
    torch = pytest.importorskip("torch")

    path = tmp_path / "state.pth"
    torch.save({"weight": torch.zeros(2, 2)}, path)

    expected = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    data, digest = read_verified_checkpoint(path, expected_sha256=expected)
    restored = torch.load(__import__("io").BytesIO(data), weights_only=True)

    assert digest == hashlib.sha256(data).hexdigest().upper()
    assert restored["weight"].shape == (2, 2)
