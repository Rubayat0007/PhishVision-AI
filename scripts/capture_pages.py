"""Capture phishing and legitimate page screenshots and append label rows.

Run this on a machine with normal internet access, with phishing URLs taken from
a feed you are entitled to use. Run the phishing half inside an isolated VM:
no credentials, no downloads, snapshot discarded afterwards.

Usage
-----
    python -m pip install playwright
    python -m playwright install chromium

    python scripts/capture_pages.py ^
        --phishing-file capture_inputs/phishing_urls.txt ^
        --legit-file capture_inputs/legit_urls.txt ^
        --out-dir captures

Then:

    python scripts/build_manifest.py --images-dir captures ^
        --labels captures/labels.csv --dataset-version v3-pilot ^
        --output manifests/v3-pilot.json

Splits are assigned per registered domain, so one domain never spans two splits.
Rows are appended, never rewritten: an existing labels.csv is extended.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from urllib.parse import urlparse

COLUMNS = [
    "filename", "label", "label_basis", "label_confidence", "registered_domain",
    "brand_cluster", "kit_cluster", "captured_at", "source", "license", "split",
]

TWO_PART_TLDS = {"co.uk", "com.au", "co.jp", "com.br", "co.in", "org.uk", "ac.uk"}


def registered_domain(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    parts = [part for part in host.split(".") if part]

    if len(parts) <= 2:
        return host

    if ".".join(parts[-2:]) in TWO_PART_TLDS:
        return ".".join(parts[-3:])

    return ".".join(parts[-2:])


def split_for(domain: str) -> str:
    """Stable per-domain split: one domain can only ever land in one split."""
    bucket = int(hashlib.sha256(domain.encode("utf-8")).hexdigest()[:8], 16) % 100

    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"


def read_urls(path: Path) -> list[str]:
    if not path.is_file():
        raise SystemExit(f"missing URL file: {path}")

    urls = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line.split()[0])
    return urls


def slug(domain: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "-" else "_" for ch in domain)[:60]


def append_rows(labels: Path, rows: list[dict]) -> None:
    exists = labels.is_file() and labels.stat().st_size > 0

    with labels.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phishing-file", type=Path, required=True)
    parser.add_argument("--legit-file", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("captures"))
    parser.add_argument("--viewport", default="1280x720")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--source", default="manual feed")
    parser.add_argument("--license", default="research use of public page")
    args = parser.parse_args()

    width, height = (int(x) for x in args.viewport.lower().split("x"))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed.\n"
              "  python -m pip install playwright\n"
              "  python -m playwright install chromium", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    labels = args.out_dir / "labels.csv"

    jobs = [(url, "phishing") for url in read_urls(args.phishing_file)]
    jobs += [(url, "legitimate") for url in read_urls(args.legit_file)]

    from datetime import datetime, timezone

    rows: list[dict] = []
    failures: list[tuple[str, str]] = []

    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)

        for url, label in jobs:
            domain = registered_domain(url)
            index = sum(1 for row in rows if row["registered_domain"] == domain) + 1
            filename = f"{label}_{slug(domain)}_{index:02d}.png"
            target = args.out_dir / filename

            page = browser.new_page(viewport={"width": width, "height": height},
                                    accept_downloads=False)
            try:
                page.goto(url, wait_until="load", timeout=args.timeout_ms)
                page.wait_for_timeout(1500)
                page.screenshot(path=str(target), full_page=False)
            except Exception as exc:  # noqa: BLE001 - one bad URL must not stop the run
                failures.append((url, f"{type(exc).__name__}: {exc}"[:160]))
                page.close()
                continue
            finally:
                try:
                    page.close()
                except Exception:  # noqa: BLE001
                    pass

            rows.append({
                "filename": filename,
                "label": label,
                "label_basis": (
                    "URL listed by the supplied phishing feed; screenshot taken, "
                    "visual review still required"
                    if label == "phishing"
                    else "public page captured, no credentials entered"
                ),
                "label_confidence": "0.7",
                "registered_domain": domain,
                "brand_cluster": domain,
                "kit_cluster": "unknown",
                "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "source": args.source,
                "license": args.license,
                "split": split_for(domain),
            })
            print(f"captured {filename}")

        browser.close()

    append_rows(labels, rows)

    phishing = sum(1 for row in rows if row["label"] == "phishing")
    print(f"\nrow(s) appended: {len(rows)} (phishing {phishing}, "
          f"legitimate {len(rows) - phishing})")
    print(f"failures: {len(failures)}")
    for url, reason in failures[:10]:
        print(f"  {url} -> {reason}")

    if len(rows) < 50:
        print("\nsmaller than the 50-image pilot target; add more URLs and re-run "
              "(existing rows are kept).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
