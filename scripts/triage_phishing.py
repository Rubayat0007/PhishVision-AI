"""OCR triage for phishing captures that may not show a phishing page.

For each `phishing` row: read the text with EasyOCR, then look for
(a) a token from the capture's own domain and (b) credential vocabulary. Images
with neither are flagged as unlikely to be phishing pages - parked domains,
dashboards, or error pages that slipped past the interstitial guard.

Writes results/pilot_triage/summary.json and docs/measurements/pilot-triage.md.
`--apply` lowers label_confidence to 0.3 for flagged rows and records the reason
in label_basis; nothing is deleted.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CREDENTIAL_WORDS = (
    "password", "sign in", "log in", "login", "verify", "account", "confirm",
    "secure", "unlock", "bank", "wallet", "email", "username", "otp", "code",
)


def domain_token(domain: str) -> str:
    parts = [part for part in re.split(r"[.\-_]", domain.lower()) if part]
    parts = [part for part in parts if part not in {"www", "com", "net", "org", "co"}]
    return parts[0] if parts else ""


def triage_text(text: str, token: str) -> dict:
    lowered = text.lower()
    has_credential = any(word in lowered for word in CREDENTIAL_WORDS)
    has_token = bool(token) and token in lowered

    return {
        "has_credential": has_credential,
        "has_domain_token": has_token,
        "suspicious": not has_credential and not has_token,
        "chars": len(text),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, default=PROJECT_ROOT / "captures")
    parser.add_argument("--labels", type=Path,
                        default=PROJECT_ROOT / "captures" / "labels.csv")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    import easyocr

    reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    with args.labels.open(encoding="utf-8", newline="") as handle:
        reader_csv = csv.DictReader(handle)
        fieldnames = reader_csv.fieldnames or []
        rows = list(reader_csv)

    targets = [row for row in rows if row["label"] == "phishing"]
    if args.limit:
        targets = targets[: args.limit]

    results = []

    for index, row in enumerate(targets, 1):
        path = args.captures / row["filename"]
        token = domain_token(row["registered_domain"])

        try:
            text = " ".join(reader.readtext(str(path), detail=0))
        except Exception as exc:  # noqa: BLE001 - one unreadable image must not stop triage
            results.append({"filename": row["filename"], "error": str(exc)[:120],
                            "suspicious": True})
            continue

        verdict = triage_text(text, token)
        verdict.update({"filename": row["filename"], "domain_token": token,
                        "sample": text[:120]})
        results.append(verdict)

        if index % 10 == 0:
            print(f"  {index}/{len(targets)}", flush=True)

    suspicious = [item for item in results if item.get("suspicious")]
    summary = {
        "triaged": len(results),
        "suspicious": len(suspicious),
        "rate": round(len(suspicious) / len(results), 4) if results else 0.0,
        "flagged": [item["filename"] for item in suspicious],
        "results": results,
    }

    out = PROJECT_ROOT / "results" / "pilot_triage"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    doc = PROJECT_ROOT / "docs" / "measurements" / "pilot-triage.md"
    lines = [
        "# OCR triage of phishing captures",
        "",
        f"Triaged {summary['triaged']} images; **{summary['suspicious']}** "
        f"({summary['rate']:.1%}) show neither credential vocabulary nor their "
        "own domain token and are flagged as unlikely phishing pages.",
        "",
        "| Flagged image | Domain token | OCR sample |",
        "|---|---|---|",
    ]
    for item in suspicious[:25]:
        sample = (item.get("sample") or item.get("error") or "").replace("|", "/")
        lines.append(f"| {item['filename']} | {item.get('domain_token', '')} | {sample[:80]} |")

    lines += [
        "",
        "## What this is and is not",
        "",
        "- It is a screen for dead campaigns, parked domains, and blank dashboards.",
        "- It is not a label: a real phishing page can omit credential words in OCR,",
        "  and a parked page can contain the domain token.",
        "- Nothing was deleted. Flagged rows keep their label; with `--apply` their",
        "  confidence drops to 0.3 and the reason is recorded.",
    ]
    doc.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.apply:
        flagged = set(summary["flagged"])
        for row in rows:
            if row["filename"] in flagged:
                row["label_confidence"] = "0.3"
                row["label_basis"] = (
                    "feed URL; OCR found no credential vocabulary or domain token"
                )
        with args.labels.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"applied: {len(flagged)} row(s) marked confidence 0.3")

    print(json.dumps({k: summary[k] for k in ("triaged", "suspicious", "rate")},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
