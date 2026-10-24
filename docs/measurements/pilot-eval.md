# Pilot evaluation (exploratory, HYPOTHESIS)

Test split: n=19 (10 phishing, 9 legitimate), threshold 0.35.

| Metric | Value | 95% Wilson CI |
|---|---|---|
| recall | 0.6 | 0.3127-0.8318 |
| false-positive rate | 0.3333 | 0.1206-0.6458 |
| precision | 0.6667 | — |
| F1 | 0.6316 | — |

Confusion: TP 6, FN 4, FP 3, TN 6.

## Why this is not a quality claim

- Labels are feed-derived: 21 of 65 phishing captures (32%) showed no
  credential vocabulary or domain token in OCR.
- 9 legitimate test images: one false positive moves FPR by 11 points.
- Not the sealed holdout, and no threshold was tuned on it.
- It exists to check the pipeline end to end on v3-format data.
