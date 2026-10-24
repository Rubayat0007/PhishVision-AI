# P-4: sealed evaluation of URL + risk >= 20/100

Pre-registered before scoring: promote if detection >= 0.70 and FPR <= 0.25.

Test split: 14 phishing, 8 legitimate (11 rows carry a URL).

| Metric | Value | 95% Wilson CI | Bound |
|---|---|---|---|
| detection | 0.6429 | 0.3876-0.8366 | >= 0.7 |
| false-positive rate | 0.125 | 0.0224-0.4709 | <= 0.25 |

**Verdict: INCONCLUSIVE - test split smaller than the pre-registered minimum**

## Frames

The test split was already used by earlier evaluations, so this is sealed
once from now rather than pristine. At this n it can reject a hypothesis,
not confirm one.

## Limits

- Labels feed-derived; OCR triage flags ~36% of phishing captures.
- Only rows with a source_url receive the URL; the rest are scored without it.
