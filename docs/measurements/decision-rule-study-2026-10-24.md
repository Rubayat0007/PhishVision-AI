# Decision-rule study — false positives on cached validation scores

n=83 (40 legitimate, 43 phishing). DEVELOPMENT set; thresholds were chosen after earlier choices on this same
split, so every figure is optimistic. No test data was used.

## Rules

| Rule | TP | FP | FN | TN | precision | recall | FPR | F1 |
|---|---|---|---|---|---|---|---|---|
| risk score >= 0.35/100 (scale-confused) | 2 | 0 | 41 | 40 | 1.0 | 0.0465 | 0.0 | 0.0889 |
| risk score >= 0.25/100 | 26 | 3 | 17 | 37 | 0.8966 | 0.6047 | 0.075 | 0.7222 |
| risk score >= 0.20/100 | 31 | 11 | 12 | 29 | 0.7381 | 0.7209 | 0.275 | 0.7294 |
| cnn probability >= 0.50 | 27 | 9 | 16 | 31 | 0.75 | 0.6279 | 0.225 | 0.6835 |
| text >= 50 and cnn >= 0.35 | 0 | 0 | 43 | 40 | 0.0 | 0.0 | 0.0 | 0.0 |
| text >= 30 and cnn >= 0.35 | 3 | 0 | 40 | 40 | 1.0 | 0.0698 | 0.0 | 0.1304 |
| text >= 50 or cnn >= 0.50 | 27 | 9 | 16 | 31 | 0.75 | 0.6279 | 0.225 | 0.6835 |

## Combined-score threshold sweep

| Threshold | precision | recall | FPR | F1 |
|---|---|---|---|---|
| 0.20 | 0.7381 | 0.7209 | 0.275 | 0.7294 |
| 0.25 | 0.8966 | 0.6047 | 0.075 | 0.7222 |
| 0.30 | 1.0 | 0.2791 | 0.0 | 0.4364 |
| 0.35 | 1.0 | 0.0465 | 0.0 | 0.0889 |
| 0.40 | 1.0 | 0.0233 | 0.0 | 0.0455 |
| 0.50 | 0.0 | 0.0 | 0.0 | 0.0 |
| 0.60 | 0.0 | 0.0 | 0.0 | 0.0 |
| 0.70 | 0.0 | 0.0 | 0.0 | 0.0 |

## Reading this

- The production threshold (0.35) is a **CNN probability**, not a risk score:
  the analyzer's combined score is 0-100, so comparing it to 0.35 flags
  everything. That scale confusion is recorded here rather than quietly fixed.
- On the risk scale, score >= 0.20 flags 11 of 40 legitimate pages (FPR 0.275) with recall 0.7209; score >= 0.25 gives FPR 0.075 and recall 0.6047.
- CNN-only at probability 0.50: FPR 0.225, recall 0.6279.
- Requiring both components to fire trades recall for precision; the table shows how much, rather than assuming the trade is free.

## Limits

- Selection on the evaluation split: the chosen rule will regress on new data.
- n=83 with 40 legitimate images: one false positive moves FPR by 2.5 points.
- Scores come from the frozen production model; nothing was retrained.
