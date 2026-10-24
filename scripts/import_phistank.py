"""Import a PhishTank CSV export, keeping only verified live URLs.

PhishTank's online-valid export has columns: phish_id, url, phish_detail_url,
submission_time, verified, verification_time, online, target. The `verified`
flag is the reason to prefer it over a raw feed: it removes most of the doubtful
labels that plain feeds produce.

Usage
-----
    python scripts/import_phistank.py online-valid.csv --output capture_inputs/phishing_urls.txt
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def verified_urls(rows) -> list[str]:
    """Keep rows with verified == yes and online == yes; de-duplicate by URL."""
    seen: dict[str, None] = {}

    for row in rows:
        normalised = {str(key).strip().lower(): (value or "").strip()
                      for key, value in row.items()}
        if normalised.get("verified", "").lower() not in {"yes", "true", "y"}:
            continue
        if normalised.get("online", "").lower() in {"no", "false", "n"}:
            continue
        url = normalised.get("url", "")
        if url.startswith(("http://", "https://")):
            seen.setdefault(url, None)

    return list(seen)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path,
                        default=Path("capture_inputs") / "phishing_urls.txt")
    args = parser.parse_args()

    with args.csv_path.open(encoding="utf-8-sig", newline="") as handle:
        urls = verified_urls(csv.DictReader(handle))

    if not urls:
        print("no verified live URLs found", flush=True)
        return 1

    header = ("# Phishing URLs for the pilot.\n"
              "# Generated from a PhishTank export, verified + online only.\n")

    args.output.write_text(header + "\n".join(urls) + "\n", encoding="utf-8")
    print(f"wrote {len(urls)} verified URL(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
