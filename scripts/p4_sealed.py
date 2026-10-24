"""P-4: pre-registered sealed evaluation of URL + risk threshold 20/100.

Hypothesis written before scoring:
  Supplying the source URL and using risk >= 20/100 raises phishing detection
  without increasing legitimate false positives.

Decision rule (fixed now):
  promote if detection >= 0.70 and FPR <= 0.25 on the test split;
  reject otherwise.

The test split has been used by earlier evaluations, so this is "sealed once from
now", not pristine. At this n it can reject, not confirm.
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

THRESHOLD = 20.0
MIN_DETECTION = 0.70
MAX_FPR = 0.25
MIN_PER_CLASS = 10


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
    test = [row for row in rows if row["split"] == "test"]
    phishing = [row for row in test if row["label"] == "phishing"]
    legitimate = [row for row in test if row["label"] == "legitimate"]

    print(f"test: {len(phishing)} phishing, {len(legitimate)} legitimate")

    analyzer = PhishVisionAnalyzer()

    def score(subset):
        detected = 0
        rows_out = []
        for row in subset:
            url = (row.get("source_url") or "").strip() or None
            with Image.open(PROJECT_ROOT / "captures" / row["filename"]) as handle:
                result = analyzer.analyze(handle.convert("RGB"), url=url)
            risk = float(result["risk"]["overall_score"])
            rows_out.append({"filename": row["filename"], "risk": risk, "url": bool(url)})
            if risk >= THRESHOLD:
                detected += 1
        return detected, rows_out

    phish_detected, phish_rows = score(phishing)
    legit_flagged, legit_rows = score(legitimate)

    detection = phish_detected / len(phishing) if phishing else 0.0
    fpr = legit_flagged / len(legitimate) if legitimate else 0.0

    enough = len(phishing) >= MIN_PER_CLASS and len(legitimate) >= MIN_PER_CLASS

    if not enough:
        verdict = "INCONCLUSIVE - test split smaller than the pre-registered minimum"
    elif detection >= MIN_DETECTION and fpr <= MAX_FPR:
        verdict = "PROMOTE candidate"
    else:
        verdict = "REJECT"

    summary = {
        "threshold": THRESHOLD,
        "test_phishing": len(phishing),
        "test_legitimate": len(legitimate),
        "with_url": sum(1 for row in test if (row.get("source_url") or "").strip()),
        "detection": round(detection, 4),
        "detection_ci": [round(v, 4) for v in wilson(phish_detected, len(phishing))],
        "fpr": round(fpr, 4),
        "fpr_ci": [round(v, 4) for v in wilson(legit_flagged, len(legitimate))],
        "min_detection": MIN_DETECTION,
        "max_fpr": MAX_FPR,
        "verdict": verdict,
        "frames": phish_rows + legit_rows,
        "status": "SEALED-ONE-SHOT; pilot labels feed-derived",
    }

    out = PROJECT_ROOT / "results" / "p4_sealed"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")

    lines = [
        "# P-4: sealed evaluation of URL + risk >= 20/100",
        "",
        "Pre-registered before scoring: promote if detection >= 0.70 and FPR <= 0.25.",
        "",
        f"Test split: {len(phishing)} phishing, {len(legitimate)} legitimate "
        f"({summary['with_url']} rows carry a URL).",
        "",
        "| Metric | Value | 95% Wilson CI | Bound |",
        "|---|---|---|---|",
        f"| detection | {summary['detection']} | {summary['detection_ci'][0]}-"
        f"{summary['detection_ci'][1]} | >= {MIN_DETECTION} |",
        f"| false-positive rate | {summary['fpr']} | {summary['fpr_ci'][0]}-"
        f"{summary['fpr_ci'][1]} | <= {MAX_FPR} |",
        "",
        f"**Verdict: {verdict}**",
        "",
        "## Frames",
        "",
        "The test split was already used by earlier evaluations, so this is sealed",
        "once from now rather than pristine. At this n it can reject a hypothesis,",
        "not confirm one.",
        "",
        "## Limits",
        "",
        "- Labels feed-derived; OCR triage flags ~36% of phishing captures.",
        "- Only rows with a source_url receive the URL; the rest are scored without it.",
    ]

    (PROJECT_ROOT / "docs" / "measurements" / "p4-sealed.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
