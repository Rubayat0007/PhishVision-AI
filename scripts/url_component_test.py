"""P-3: does supplying the URL change the decision?

Compares the analyser with and without the URL for captures that recorded a
source_url. Measures phishing detection, legitimate false positives, and the mean
risk-score change. Balanced sample; no threshold tuning.

Writes docs/measurements/url-component.md and results/url_component/summary.json.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image  # noqa: E402

from src.security.analyzer import PhishVisionAnalyzer  # noqa: E402

THRESHOLD = 35.0
LIMIT_PER_CLASS = 12


def wilson(successes, total, z=1.96):
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    d = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> int:
    rows = list(csv.DictReader(
        (PROJECT_ROOT / "captures" / "labels.csv").open(encoding="utf-8", newline="")
    ))
    with_url = [row for row in rows if (row.get("source_url") or "").strip()]

    sample = []
    for label in ("phishing", "legitimate"):
        sample.extend([row for row in with_url if row["label"] == label][:LIMIT_PER_CLASS])

    print(f"images with URL: {len(with_url)}; sampled: {len(sample)}")

    analyzer = PhishVisionAnalyzer()
    records = []

    for index, row in enumerate(sample, 1):
        path = PROJECT_ROOT / "captures" / row["filename"]
        with Image.open(path) as handle:
            image = handle.convert("RGB")

        without = analyzer.analyze(image)
        with_url_result = analyzer.analyze(image, url=row["source_url"])

        records.append({
            "filename": row["filename"],
            "label": row["label"],
            "url": row["source_url"],
            "risk_without": float(without["risk"]["overall_score"]),
            "risk_with": float(with_url_result["risk"]["overall_score"]),
            "url_score": (
                float(with_url_result["url_analysis"]["score"])
                if with_url_result.get("url_analysis") else None
            ),
        })

        if index % 6 == 0:
            print(f"  {index}/{len(sample)}", flush=True)

    def rate(label, key):
        subset = [record for record in records if record["label"] == label]
        flagged = sum(1 for record in subset if record[key] >= THRESHOLD)
        return flagged, len(subset)

    phish_without = rate("phishing", "risk_without")
    phish_with = rate("phishing", "risk_with")
    legit_without = rate("legitimate", "risk_without")
    legit_with = rate("legitimate", "risk_with")

    def summary_row(pair):
        flagged, total = pair
        return {"flagged": flagged, "n": total,
                "rate": round(flagged / total, 4) if total else 0.0,
                "ci": [round(v, 4) for v in wilson(flagged, total)]}

    deltas = [record["risk_with"] - record["risk_without"] for record in records]

    summary = {
        "n": len(records),
        "threshold": THRESHOLD,
        "phishing_detection_without_url": summary_row(phish_without),
        "phishing_detection_with_url": summary_row(phish_with),
        "legitimate_fp_without_url": summary_row(legit_without),
        "legitimate_fp_with_url": summary_row(legit_with),
        "mean_risk_delta": round(sum(deltas) / len(deltas), 2),
        "rows": records,
        "status": "DEVELOPMENT - pilot labels, balanced sample",
    }

    out = PROJECT_ROOT / "results" / "url_component"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# P-3: the URL component, measured",
        "",
        f"n={summary['n']} captures that recorded a `source_url` "
        f"({LIMIT_PER_CLASS} per class). Threshold: risk score >= {THRESHOLD}/100.",
        "",
        "| Measure | without URL | with URL |",
        "|---|---|---|",
        f"| phishing detected | {phish_without[0]}/{phish_without[1]} "
        f"({summary['phishing_detection_without_url']['rate']}) | "
        f"{phish_with[0]}/{phish_with[1]} ({summary['phishing_detection_with_url']['rate']}) |",
        f"| legitimate flagged | {legit_without[0]}/{legit_without[1]} "
        f"({summary['legitimate_fp_without_url']['rate']}) | "
        f"{legit_with[0]}/{legit_with[1]} ({summary['legitimate_fp_with_url']['rate']}) |",
        "",
        f"Mean risk-score change when the URL is supplied: {summary['mean_risk_delta']:+.2f} points.",
        "",
        "## Reading this",
        "",
        "- The platform documents a 30% weight for the URL component; dataset images",
        "  historically carried no URL, so that weight was never exercised.",
        "- A positive mean delta means the URL raises risk; whether it raises it for",
        "  the right class is the question, and the two rows above answer it.",
        "",
        "## Limits",
        "",
        f"- {LIMIT_PER_CLASS} images per class: one case is {100 / LIMIT_PER_CLASS:.0f} points.",
        "- Feed-derived labels; the earlier OCR triage flagged ~36% of phishing caps.",
        "- The URL comes from the feed, so it is the *reported* phishing URL, which is",
        "  the most favourable case for the URL component.",
    ]

    (PROJECT_ROOT / "docs" / "measurements" / "url-component.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
