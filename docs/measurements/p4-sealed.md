# P-4: sealed evaluation of URL + risk >= 20/100

Pre-registered before scoring: promote if detection >= 0.70 and FPR <= 0.25.

Test split: 19 phishing, 12 legitimate (20 rows carry a URL).

| Metric | Value | 95% Wilson CI | Bound |
|---|---|---|---|
| detection | 0.5263 | 0.3171-0.7267 | >= 0.7 |
| false-positive rate | 0.3333 | 0.1381-0.6094 | <= 0.25 |

**Verdict: REJECT**

## Frames

The test split was already used by earlier evaluations, so this is sealed
once from now rather than pristine. At this n it can reject a hypothesis,
not confirm one.

## Limits

- Labels feed-derived; OCR triage flags ~36% of phishing captures.
- Only rows with a source_url receive the URL; the rest are scored without it.
