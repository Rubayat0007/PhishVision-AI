# Test-split uncertainty (bootstrap)

Input: `predictions.csv` — 85 rows, threshold 0.35,
5000 resamples, seed 42. Percentile intervals.

| Metric | Point estimate | 95% interval |
|---|---|---|
| accuracy | 0.6471 | 0.5412 – 0.7529 |
| precision | 0.6094 | 0.4844 – 0.7286 |
| recall | 0.8864 | 0.7857 – 0.9750 |
| f1 | 0.7222 | 0.6170 – 0.8104 |
| roc_auc | 0.6946 | 0.5782 – 0.8007 |
| specificity | 0.3902 | 0.2439 – 0.5429 |

## Reading this

- With 85 images, intervals are wide: differences of a few points between
  models or thresholds are inside the noise band.
- The interval describes sampling variability of this split, not variation
  across datasets. Generalisation to another screenshot population is a
  separate question that needs separate data.
- Resampling is deterministic given the seed, so the table is reproducible
  from the recorded predictions.
