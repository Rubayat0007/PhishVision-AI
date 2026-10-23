"""Tests for checkpoint integrity verification.

These tests are torch-free: verification operates on bytes, so the
production guard can be exercised on any machine.
"""

import hashlib

import pytest

from src.models.integrity import (
    BYPASS_ENV_VAR,
    PRODUCTION_MODEL_SHA256,
    ModelIntegrityError,
    calculate_sha256,
    is_verification_bypassed,
    normalize_digest,
    verify_model_file,
)

CONTENT = b"phishvision-model-bytes"
CONTENT_SHA256 = hashlib.sha256(CONTENT).hexdigest().upper()


@pytest.fixture
def model_file(tmp_path):
    path = tmp_path / "model.pth"
    path.write_bytes(CONTENT)
    return path


def test_calculate_sha256_returns_uppercase_digest(model_file):
    assert calculate_sha256(model_file) == CONTENT_SHA256
    assert calculate_sha256(model_file) == CONTENT_SHA256.upper()


def test_calculate_sha256_matches_hashlib(tmp_path):
    path = tmp_path / "blob.bin"
    path.write_bytes(b"abc")

    assert calculate_sha256(path) == (
        "BA7816BF8F01CFEA414140DE5DAE2223"
        "B00361A396177A9CB410FF61F20015AD"
    )


def test_verify_accepts_matching_digest(model_file):
    assert verify_model_file(
        model_file, expected_sha256=CONTENT_SHA256
    ) == CONTENT_SHA256


def test_verify_accepts_lowercase_expected_digest(model_file):
    assert verify_model_file(
        model_file, expected_sha256=CONTENT_SHA256.lower()
    ) == CONTENT_SHA256


def test_verify_rejects_mismatched_digest(model_file):
    with pytest.raises(ModelIntegrityError) as error:
        verify_model_file(model_file, expected_sha256="0" * 64)

    message = str(error.value)
    assert "integrity check failed" in message
    assert BYPASS_ENV_VAR in message
    assert CONTENT_SHA256 in message


def test_verify_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify_model_file(tmp_path / "absent.pth")


def test_verify_rejects_malformed_expected_digest(model_file):
    with pytest.raises(ValueError):
        verify_model_file(model_file, expected_sha256="not-a-digest")


def test_verify_still_hashes_when_bypassed(model_file):
    digest = verify_model_file(
        model_file,
        expected_sha256="0" * 64,
        allow_unverified=True,
    )

    assert digest == CONTENT_SHA256


def test_normalize_digest_strips_and_uppercases():
    assert normalize_digest(f"  {CONTENT_SHA256.lower()}  ") == CONTENT_SHA256


def test_normalize_digest_rejects_non_string():
    with pytest.raises(ValueError):
        normalize_digest(123)


@pytest.mark.parametrize(
    "value", ["1", "true", "TRUE", " yes ", "on"]
)
def test_bypass_detected_for_truthy_values(value):
    assert is_verification_bypassed({BYPASS_ENV_VAR: value}) is True


@pytest.mark.parametrize(
    "value", ["0", "false", "no", "off", "", "maybe"]
)
def test_bypass_not_detected_for_other_values(value):
    assert is_verification_bypassed({BYPASS_ENV_VAR: value}) is False


def test_bypass_defaults_to_false():
    assert is_verification_bypassed({}) is False


def test_production_digest_is_well_formed():
    assert normalize_digest(PRODUCTION_MODEL_SHA256) == PRODUCTION_MODEL_SHA256
