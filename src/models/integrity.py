"""Integrity verification for local model checkpoints.

The production checkpoint is distributed outside Git and must be verified
against a published SHA-256 digest. Verification is mandatory for the
configured production path and can only be bypassed deliberately, for
experimental checkpoints, through an explicit environment variable.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Mapping

# Frozen production CNN (v2), published in README.md and provision_model.py.
PRODUCTION_MODEL_SHA256 = (
    "1403582CCE07BE1E36E70E4A0D425CFB152B86C7ABEE5D1074DEF79CBB2FB628"
)

# Deliberate opt-out for experiments that use a non-production checkpoint.
BYPASS_ENV_VAR = "PHISHVISION_ALLOW_UNVERIFIED_MODEL"

_TRUTHY_VALUES = {"1", "true", "yes", "on"}
_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")


class ModelIntegrityError(RuntimeError):
    """Raised when a checkpoint does not match the expected digest."""


def calculate_sha256(path: Path | str) -> str:
    """Return the uppercase SHA-256 hex digest of a file."""
    digest = hashlib.sha256()

    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def normalize_digest(value: str, field: str = "expected_sha256") -> str:
    """Normalize and validate a SHA-256 digest string."""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")

    digest = value.strip().upper()

    if not _SHA256_PATTERN.fullmatch(digest):
        raise ValueError(
            f"{field} must be a 64-character hexadecimal SHA-256 digest"
        )

    return digest


def is_verification_bypassed(
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Return True when verification was explicitly disabled for experiments."""
    raw = (environ if environ is not None else os.environ).get(
        BYPASS_ENV_VAR
    )

    if raw is None:
        return False

    return raw.strip().lower() in _TRUTHY_VALUES


def build_provenance(
    *,
    loaded: bool,
    sha256: str | None,
    threshold: float,
    name: str = "phishvision_cnn_v2",
) -> dict:
    """Describe the model behind an analysis result."""
    return {
        "name": name,
        "loaded": bool(loaded),
        "sha256": sha256,
        "threshold": float(threshold),
    }


def verify_model_file(
    path: Path | str,
    *,
    expected_sha256: str = PRODUCTION_MODEL_SHA256,
    allow_unverified: bool = False,
) -> str:
    """Verify a checkpoint file and return its actual SHA-256 digest.

    Args:
        path: checkpoint file to hash.
        expected_sha256: published digest of the production checkpoint.
        allow_unverified: explicit opt-out for experimental checkpoints.

    Raises:
        FileNotFoundError: the checkpoint does not exist.
        ValueError: the expected digest is malformed.
        ModelIntegrityError: the file does not match the expected digest.
    """
    model_path = Path(path)

    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    expected = normalize_digest(expected_sha256)
    actual = calculate_sha256(model_path)

    if allow_unverified:
        return actual

    if actual != expected:
        raise ModelIntegrityError(
            f"Model integrity check failed for {model_path.name}: "
            f"expected SHA-256 {expected}, got {actual}. "
            f"Set {BYPASS_ENV_VAR}=1 only for a deliberate experiment "
            "with a non-production checkpoint."
        )

    return actual
