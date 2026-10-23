# Component diagnostics — cluster-disjoint test split

n=83 (legitimate 49, phishing 34); 324 perceptual clusters, none spanning splits.

| Signal | ROC AUC | 95% bootstrap CI |
|---|---|---|
| text | 0.6375 | 0.5292-0.7433 |
| cnn | 0.6573 | 0.5372-0.7721 |
| combined | 0.6942 | 0.5658-0.8078 |

URL component absent: no URLs for dataset images.

Calibration: Brier 0.2304, ECE 0.0407.

| Bin | n | Mean predicted | Observed rate |
|---|---|---|---|
| 0.0-0.2 | 17 | 0.1112 | 0.2353 |
| 0.2-0.4 | 24 | 0.2938 | 0.3333 |
| 0.4-0.6 | 33 | 0.4853 | 0.4848 |
| 0.6-0.8 | 9 | 0.7006 | 0.6667 |

## Comparison with the leaky split

| Signal | leaky test AUC | cluster-disjoint AUC |
|---|---|---|
| text | 0.7419 | 0.6375 |
| CNN | 0.7424 | 0.6573 |
| combined | 0.8041 | 0.6942 |

Residual leakage cannot be excluded: crops and overlays survive dHash.
