# Fusion calibration (pre-registered, single sealed-test evaluation)

Train 84, validation 19, test 18. Threshold fixed on validation before test was scored.

Fitted weights: OCR text -0.3595, CNN 1.0908.

| Rule | threshold | TP | FP | FN | TN | recall | FPR | FPR 95% CI |
|---|---|---|---|---|---|---|---|---|
| calibrated fusion | 0.5017 | 5 | 3 | 4 | 6 | 0.5556 | 0.3333 | 0.1206-0.6458 |
| current risk rule | 0.1416 | 5 | 4 | 4 | 5 | 0.5556 | 0.4444 | 0.1888-0.7334 |
| CNN only | 0.354 | 5 | 3 | 4 | 6 | 0.5556 | 0.3333 | 0.1206-0.6458 |

## Verdict

- **Hypothesis supported on the sealed test**: calibrated fusion has the lower FPR (0.3333 vs 0.4444) at recall >= 0.5556.
- Single sealed evaluation, 18 test images: direction and mechanism, not a promotion decision.

## Limits

- Labels feed-derived; 32% of phishing captures flagged by OCR triage.
- Test n=18: one case moves FPR by 11 points.
- The fit uses two features; URL weighting (P-3) remains untested because no
  dataset image carries a URL.
