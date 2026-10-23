# Threshold study — frozen v2 CNN

Selection on the validation split, evaluation on the test split.
The test split played no part in choosing the operating point.

| Split | Rows | ROC AUC |
|---|---|---|
| validation | 83 | 0.742442 |
| test | 85 | 0.694568 |

Validation-selected threshold (max Youden J): **0.5**

## Test split

| Threshold | Precision | Recall | Specificity | F1 | Balanced acc | Youden J |
|---|---|---|---|---|---|---|
| 0.35 (production) | 0.609375 | 0.886364 | 0.390244 | 0.722222 | 0.638304 | 0.276608 |
| 0.5 (selected on val) | 0.657143 | 0.522727 | 0.707317 | 0.582278 | 0.615022 | 0.230044 |

## Interpretation

- AUC on the test split is 0.694568, consistent with the recorded baseline; discrimination is modest, not strong.
- A threshold chosen on validation is a defensible operating point only if
  the resulting test numbers are reported as-is, including the cost in
  false positives.
- If the selected threshold differs from 0.35, changing production requires
  a deliberate decision: the frozen model, its documented threshold, and
  earlier results all assume 0.35.

## Inputs

- val: `results\evaluation\v2-val-035\predictions.csv` — rows 83, sha256 `F518B79DAEE23AC3…`
- test: `results\evaluation\v2-test-035\predictions.csv` — rows 85, sha256 `DE5B95CDC79FE78E…`
