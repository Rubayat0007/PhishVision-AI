# PhishVision-AI — Phase 4 Robustness Evaluation

## Purpose

Evaluate adversarial robustness of the frozen production PhishVision v2 CNN under deterministic untargeted L-infinity FGSM and PGD attacks.

This experiment is diagnostic. It does not modify the production model, threshold, dataset, preprocessing, or attack implementations.

## Frozen production lineage

- Production model: `models/phishvision_cnn_v2.pth`
- Model SHA-256: `1403582CCE07BE1E36E70E4A0D425CFB152B86C7ABEE5D1074DEF79CBB2FB628`
- Dataset split: `data/clean_split_v2`
- Evaluation split: `test`
- Test samples: 85
- CNN operating threshold: 0.35

## Attack protocol

### FGSM

- Untargeted gradient-sign attack.
- Input attack space: image tensors in `[0, 1]`.
- Perturbation: `x_adv = x + epsilon * sign(gradient)`.
- Final image clipped to `[0, 1]`.

### PGD

- Untargeted L-infinity PGD.
- Initialization: clean image; no random initialization.
- Steps: 10.
- Step size: `alpha = epsilon / 10`.
- Projection: perturbation clipped to `[-epsilon, +epsilon]`.
- Final image clipped to `[0, 1]`.
- Model input is ImageNet-normalized inside the attack implementation.

### Epsilon grid

- 0.005
- 0.010
- 0.020
- 0.040

## Clean baseline

At the frozen threshold of 0.35:

- Clean test samples: 85
- Clean-correct samples: 52/85
- Clean-correct phishing samples: 23

The conditional robustness analysis therefore uses 23 phishing test images that were correctly classified as phishing before attack.

## Results

| Attack | Epsilon | Overall flip rate | Flip count | Conditional ASR | Conditional successes |
|---|---:|---:|---:|---:|---:|
| FGSM | 0.005 | 3.53% | 3/85 | 8.70% | 2/23 |
| FGSM | 0.010 | 4.71% | 4/85 | 8.70% | 2/23 |
| FGSM | 0.020 | 7.06% | 6/85 | 13.04% | 3/23 |
| FGSM | 0.040 | 18.82% | 16/85 | 47.83% | 11/23 |
| PGD | 0.005 | 7.06% | 6/85 | 13.04% | 3/23 |
| PGD | 0.010 | 18.82% | 16/85 | 39.13% | 9/23 |
| PGD | 0.020 | 28.24% | 24/85 | 60.87% | 14/23 |
| PGD | 0.040 | 41.18% | 35/85 | 69.57% | 16/23 |

## Integrity verification

Generated robustness CSV:

`results/v2_robustness_test.csv`

- Records: 680
- Expected records: 85 images × 2 attacks × 4 epsilon values = 680
- Maximum observed L-infinity perturbation matched the requested epsilon for every attack/epsilon combination.

CSV SHA-256:

`16DD5E622BD0E395EDAD297ED03F0EDFDBAB471DBBF7BD928824FE4E6A6E9728`

## Per-image diagnostic

For PGD at epsilon 0.04, among the 23 clean-correct phishing samples:

- 16/23 were flipped.
- 7/23 remained correctly classified.

The flipped group had:

- mean clean p(phishing): 0.549974
- median clean p(phishing): 0.537080
- range: 0.501083–0.677200

The resistant group had:

- mean clean p(phishing): 0.785267
- median clean p(phishing): 0.779203
- range: 0.768160–0.811629

Across the tested PGD strengths, the 15 samples with clean p(phishing) in `[0.50, 0.60)` had conditional attack success rates of:

- epsilon 0.005: 20.0% (3/15)
- epsilon 0.010: 53.3% (8/15)
- epsilon 0.020: 86.7% (13/15)
- epsilon 0.040: 100.0% (15/15)

The `[0.70, 0.80)` group contained 6 samples and had 0 flips at every tested PGD epsilon. The `[0.60, 0.70)` group contained only 1 sample, so its percentages are not treated as a stable subgroup estimate.

## Interpretation

PGD produced more attack-induced classification flips than FGSM at every tested epsilon.

Conditional attack success increased with epsilon for both attack families, reaching 47.83% for FGSM and 69.57% for PGD at epsilon 0.04.

Within the clean-correct phishing subset, vulnerability to the tested PGD perturbations was concentrated among samples with lower clean CNN phishing scores. This is an observed association within this test set and attack protocol; it is not treated as a causal or general relationship.

These results characterize the frozen v2 model under the specified attack protocol. They do not establish robustness against other attack algorithms, perturbation norms, epsilon ranges, random-start PGD, transformations, or model architectures.

## Production decision

Production remains unchanged:

- Model: `models/phishvision_cnn_v2.pth`
- Threshold: 0.35
- Split lineage: `data/clean_split_v2`

No adversarially trained model replaces the production baseline as a result of this experiment.

## Reproducibility artifacts

- `scripts/evaluate_robustness_v2.py`
- `results/v2_robustness_test.csv`
- `models/phishvision_cnn_v2.pth`

The robustness evaluator verifies the frozen production checkpoint SHA-256 before execution.
