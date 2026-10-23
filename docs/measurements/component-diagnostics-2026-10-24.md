# Component diagnostics — PhishVision validation split

n=83 (legitimate 40, phishing 43). Majority-class accuracy 0.5181.

| Signal | ROC AUC | 95% bootstrap CI |
|---|---|---|
| text | 0.7419 | 0.6495–0.8298 |
| cnn | 0.7424 | 0.6375–0.8357 |
| combined | 0.8041 | 0.7051–0.8895 |

URL component: **absent** — dataset images have no URL, so its AUC is
undefined. The combined score is therefore 0.30·text + 0.40·CNN rescaled,
not the full 30/30/40.

## CNN calibration

Brier 0.206, ECE 0.0821 (5 bins).

| Bin | n | Mean predicted | Observed rate |
|---|---|---|---|
| 0.0-0.2 | 5 | 0.1012 | 0.0 |
| 0.2-0.4 | 19 | 0.3128 | 0.4211 |
| 0.4-0.6 | 39 | 0.4981 | 0.4615 |
| 0.6-0.8 | 19 | 0.7036 | 0.8421 |
| 0.8-1.0 | 1 | 0.8025 | 1.0 |

## Reading this

- Chance AUC is 0.5; the text heuristic scores 0.742, the CNN 0.742.
- Whether the CNN earns its 40% weight is a decision for Phase 4 under the
  pre-registered demotion rule, not a conclusion from this table alone.
- ECE with n=83 across 5 bins is a coarse estimate; the interval is wide.

## Limits

- CNN selected on this split: mildly optimistic.
- Samples not independent (source/kit clustering): bootstrap CIs optimistic.
- No URL component exists here, so the platform's full weighting is untested.
