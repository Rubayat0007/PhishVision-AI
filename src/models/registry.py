"""Model registry: which checkpoint is production, candidate, or retired.

The registry is metadata only; it does not load models. Its job is to make the
answer to "which artifact is production" a file with digests, not a memory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

STATUSES = {"production", "candidate", "experimental", "retired"}
REQUIRED = ("name", "version", "digest", "status", "ledger_ref")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_registry(path: Path | str) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("models") if isinstance(payload, dict) else None

    if not isinstance(entries, list) or not entries:
        raise ValueError("registry has no models")

    validate(entries)
    return entries


def validate(entries: list[dict]) -> None:
    seen_names: set[str] = set()
    seen_digests: set[str] = set()
    productions = 0

    for entry in entries:
        missing = [key for key in REQUIRED if key not in entry]
        if missing:
            raise ValueError(f"registry entry missing {missing}: {entry}")

        if entry["status"] not in STATUSES:
            raise ValueError(f"invalid status {entry['status']!r}")

        if not isinstance(entry["digest"], str) or len(entry["digest"]) != 64:
            raise ValueError(f"digest must be 64 hex chars: {entry['name']}")

        key = f"{entry['name']}@{entry['version']}"
        if key in seen_names:
            raise ValueError(f"duplicate registry entry {key}")
        seen_names.add(key)

        if entry["digest"] in seen_digests:
            raise ValueError(f"duplicate digest in registry: {entry['name']}")
        seen_digests.add(entry["digest"])

        if entry["status"] == "production":
            productions += 1

    if productions != 1:
        raise ValueError(f"exactly one production model required, found {productions}")


def resolve(entries: list[dict], name: str) -> dict:
    matches = [entry for entry in entries if entry["name"] == name]

    if not matches:
        raise KeyError(f"model not in registry: {name}")

    return matches[0]


def verify_entry(entry: dict, model_path: Path) -> bool:
    """True when the file matches the registry digest."""
    return sha256_of(model_path) == entry["digest"].upper()
