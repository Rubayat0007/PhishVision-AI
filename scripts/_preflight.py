"""Shared prerequisite checks for the manual validation harnesses.

The ``check_*`` harnesses exercise the full analyzer stack: torch,
torchvision, easyocr, and a local dataset split. They are deliberately
outside the pytest suite (``tests/``), so this module converts missing
prerequisites into a single actionable message instead of an import
traceback.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "data" / "clean_split_v2"

RUNTIME_MODULES = ("torch", "torchvision", "easyocr")


def missing_modules(names=RUNTIME_MODULES):
    """Return the names that cannot be imported without importing them."""
    return [
        name for name in names if importlib.util.find_spec(name) is None
    ]


def require_modules(names=RUNTIME_MODULES, hint=None):
    missing = missing_modules(names)

    if not missing:
        return

    hint = hint or (
        "Install the runtime dependencies with: "
        "python -m pip install -r requirements.txt"
    )

    print(
        "SKIP: harness prerequisites are missing: " + ", ".join(missing),
        file=sys.stderr,
    )
    print(hint, file=sys.stderr)
    raise SystemExit(2)


def require_dataset(path=DEFAULT_DATASET):
    path = Path(path)

    if path.is_dir():
        return

    print(f"SKIP: dataset split not found: {path}", file=sys.stderr)
    print(
        "Populate data/clean_split_v2/ (see README) and retry.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def require_runtime():
    """Check the analyzer stack and the dataset used by these harnesses."""
    require_modules()
    require_dataset()
