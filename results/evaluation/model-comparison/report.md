# Candidate model comparison

Rule fixed before seeing test results: promote only if validation F1
improves by at least 0.02 and validation recall does not drop.

## Validation split

| Model | Precision | Recall | Specificity | F1 | Accuracy |
|---|---|---|---|---|---|
| phishvision_cnn_advtrained_v2.pth | 0.7091 | 0.907 | 0.6 | 0.7959 | 0.759 |
| phishvision_cnn_old.pth | 0.6613 | 0.9535 | 0.475 | 0.781 | 0.7229 |
| phishvision_cnn.pth | 0.7292 | 0.814 | 0.675 | 0.7692 | 0.747 |
| phishvision_cnn_backup.pth | 0.7292 | 0.814 | 0.675 | 0.7692 | 0.747 |
| phishvision_cnn_baseline_73.pth | 0.7292 | 0.814 | 0.675 | 0.7692 | 0.747 |
| phishvision_cnn_v2-release.pth | 0.5938 | 0.8837 | 0.35 | 0.7103 | 0.6265 |
| phishvision_cnn_v2.pth | 0.5938 | 0.8837 | 0.35 | 0.7103 | 0.6265 |
| phishvision_cnn_advtrained.pth | 0.5309 | 1.0 | 0.05 | 0.6935 | 0.5422 |
| phishvision_cnn_v2_advtrained_eps001.pth | 0.5325 | 0.9535 | 0.1 | 0.6833 | 0.5422 |

## Decision

Promote **phishvision_cnn_advtrained_v2.pth** (validation F1 0.7959 vs baseline 0.7103).

## Test split (evaluated once)

| Model | Precision | Recall | Specificity | F1 | Accuracy |
|---|---|---|---|---|---|
| phishvision_cnn_advtrained_v2.pth | 0.6102 | 0.8182 | 0.439 | 0.699 | 0.6353 |
| phishvision_cnn_v2.pth | 0.6094 | 0.8864 | 0.3902 | 0.7222 | 0.6471 |

## Skipped checkpoints

- `phishvision_cnn_v3.pth` — RuntimeError: Error(s) in loading state_dict for PhishVisionCNN:
	Missing key(s) in state_dict: "classifier.1.weight", "

## Limits

- 83 validation and 85 test images: differences under ~3 points are noise.
- Clean images only; adversarial robustness is measured by the dedicated
  evaluators in `robustness/`, not here.
- Promotion changes production only via `src/config.py` `CNN_THRESHOLD`
  and `ACTIVE_MODEL_PATH`, plus the digest in `src/models/integrity.py` —
  a separate, deliberate change.
