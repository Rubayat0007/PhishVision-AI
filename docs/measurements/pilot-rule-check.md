# P-1 dry run on the pilot test split

n=19 (10 phishing, 9 legitimate). Labels are feed-derived. This shows direction only.

| Rule | TP | FP | FN | TN | recall | FPR | FPR 95% CI | F1 |
|---|---|---|---|---|---|---|---|---|
| current: cnn >= 0.35 | 6 | 3 | 4 | 6 | 0.6 | 0.3333 | 0.1206-0.6458 | 0.6316 |
| P-1: risk >= 25/100 | 2 | 1 | 8 | 8 | 0.2 | 0.1111 | 0.0199-0.435 | 0.3077 |
| risk >= 20/100 | 4 | 2 | 6 | 7 | 0.4 | 0.2222 | 0.0632-0.5474 | 0.5 |
| cnn >= 0.50 | 2 | 2 | 8 | 7 | 0.2 | 0.2222 | 0.0632-0.5474 | 0.2857 |
| risk >= 25 and cnn >= 0.35 | 2 | 1 | 8 | 8 | 0.2 | 0.1111 | 0.0199-0.435 | 0.3077 |

## Reading this

- Current operating point: 3 false positives on 9 legitimate pages (FPR 0.3333).
- P-1 (risk >= 25): 1 false positives, FPR 0.1111, recall 0.2.
- Pre-registered prediction was FPR 0.075 at recall 0.605 (n=83 cached validation).

## Limits

- 9 legitimate images: one false positive is 11 FPR points.
- Feed-derived labels, 32% of phishing flagged by OCR triage.
- Direction only: promotion still requires the sealed holdout.
