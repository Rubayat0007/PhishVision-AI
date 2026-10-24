"""Create a ready-to-fill pilot capture kit.

Writes a captures directory with a header-only labels CSV, a protocol README,
and a split plan hint. It does not create images or labels: those are yours.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

COLUMNS = [
    "filename", "label", "label_basis", "label_confidence", "registered_domain",
    "brand_cluster", "kit_cluster", "captured_at", "source", "license", "split",
]

PROTOCOL = """PILOT CAPTURE PROTOCOL
======================

Target: 50 images minimum (25 phishing, 25 legitimate), plus a sealed slice of
at least 100 images if you are building the real v3 set rather than a dry run.

Environment
-----------
- Phishing pages: isolated VM or container, no credentials, no downloads,
  snapshot discarded afterwards.
- Legitimate pages: same VM, normal browsing.
- Fixed viewport: 1280x720 and/or 1920x1080; record which one you used.

Files
-----
- One PNG/JPG per image in this folder.
- Name them <label>_<domain>_<NN>.png, e.g. phishing_example-login_01.png.
- Never overwrite a captured file; take a new number instead.

Labels (labels.csv)
-------------------
Fill one row per image. Rules that matter:

- label: phishing | legitimate - the class, not your confidence.
- label_basis: one short sentence you could defend to a reviewer, e.g.
  "served a credential form on a lookalike domain" or
  "public homepage, no login form".
- label_confidence: 0..1, your own certainty. 0.5 means unsure; say so.
- registered_domain: the registrable domain, not the full URL.
- brand_cluster: the impersonated brand for phishing, or the site's own brand.
- kit_cluster: phishing kit family if known, else "unknown". Legitimate pages
  may use the site's own domain as the kit value.
- captured_at: ISO-8601 with a timezone, e.g. 2026-10-24T15:00:00+08:00.
- source: where you found it (feed name, URL list, manual browsing).
- license: the terms that allow you to keep and use the image.
- split: train | validation | test | sealed

Splitting rules (enforced by validate_manifest.py)
--------------------------------------------------
- A phishing kit, domain, or brand may appear in only ONE split.
- Put whole clusters in one split; never split a kit across train/test.
- Reserve a sealed slice and do not look at it until the final report.
- If a domain has only one capture, the split choice is per domain, not per image.

After filling
-------------
    python scripts/build_manifest.py --images-dir captures\\ --labels labels.csv \\
        --dataset-version v3-pilot --output manifests\\v3-pilot.json

Exit 0 means the manifest is admissible: schema correct, no duplicate content,
no cluster spanning splits. Exit 1 lists exactly what to fix.
"""


def build_kit(target: Path) -> dict:
    target.mkdir(parents=True, exist_ok=True)

    labels = target / "labels.csv"
    if not labels.exists():
        with labels.open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=COLUMNS).writeheader()

    protocol = target / "PROTOCOL.txt"
    protocol.write_text(PROTOCOL, encoding="utf-8")

    return {"directory": str(target), "labels": str(labels), "protocol": str(protocol)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path,
                        default=Path("captures"))
    args = parser.parse_args()

    result = build_kit(args.directory)

    for key, value in result.items():
        print(f"{key}: {value}")
    print("\nnext: add images, fill labels.csv, then run build_manifest.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
