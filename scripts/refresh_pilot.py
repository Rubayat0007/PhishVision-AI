"""Refresh the pilot in the one correct order, stopping at the first failure.

Replaces the manual four-command sequence that was run out of order twice.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("prune duplicates", [sys.executable, "scripts/prune_captures.py",
                          "--dedupe", "--dedupe-content", "--apply"]),
    ("prune again", [sys.executable, "scripts/prune_captures.py",
                     "--dedupe", "--dedupe-content", "--apply"]),
    ("curate clusters", [sys.executable, "scripts/curate_pilot.py", "--apply"]),
    ("build manifest", [sys.executable, "scripts/build_manifest.py",
                        "--images-dir", "captures", "--labels", "captures/labels.csv",
                        "--dataset-version", "v3-pilot",
                        "--output", "manifests/v3-pilot.json"]),
]


def main() -> int:
    for name, command in STEPS:
        print(f"\n=== {name}", flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print(f"STOP: {name} failed with exit {result.returncode}", file=sys.stderr)
            return 1

    if "--with-triage" in sys.argv:
        print("\n=== OCR triage", flush=True)
        result = subprocess.run([sys.executable, "scripts/triage_phishing.py", "--apply"],
                                cwd=ROOT)
        if result.returncode != 0:
            print("STOP: triage failed", file=sys.stderr)
            return 1

    print("\nPILOT REFRESHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
