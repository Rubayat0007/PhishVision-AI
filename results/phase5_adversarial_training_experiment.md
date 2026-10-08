# Phase 5 — Adversarial Training Experiment

## Status

Completed as an isolated experiment. Production model and production threshold were not changed.

## Candidate

- Model: `models/phishvision_cnn_v2_advtrained_eps001.pth`
- SHA-256: `7515557602AEE404FAC297E8E6A14A1CFBE854DD719AE332275DB05CF99BAE2D`
- Architecture: `PhishVisionCNN`
- Dataset: `data/clean_split_v2`
- Training split: `train`
- Validation split: `val`
- Test split: `test`

## Training protocol

The historical adversarial-training recipe was reproduced against the frozen v2 lineage:

- Batch size: 32
- Learning rate: 0.0003
- Weight decay: 0.0001
- Maximum epochs: 20
- Early-stopping patience: 5
- Optimizer: Adam
- Scheduler: ReduceLROnPlateau, factor 0.5, patience 2
- Attack: FGSM
- Training epsilon: 0.01
- Loss: class-weighted cross-entropy
- Checkpoint selection: validation phishing F1
- Validation performed on clean images

Best checkpoint:

- Best epoch: 4
- Validation F1: 0.7126
- Validation recall: 0.7209
- Training stopped at epoch 9 due to early stopping

## Clean test evaluation

The candidate was evaluated on the frozen v2 test set at the frozen operating threshold of 0.35.

| Metric | Production v2 | Adv-trained candidate |
|---|---:|---:|
| Accuracy | 0.6471 | 0.6000 |
| Precision | 0.6094 | 0.5714 |
| Recall | 0.8864 | 0.9091 |
| F1 | 0.7222 | 0.7018 |
| TN | 16 | 11 |
| FP | 25 | 30 |
| FN | 5 | 4 |
| TP | 39 | 40 |

The candidate reduced false negatives by one and increased true positives by one, while increasing false positives by five. Accuracy and F1 were lower than production.

These test results are evaluation results only; the candidate was selected using validation F1 rather than test performance.

## Robustness evaluation

The candidate was evaluated using the same Phase 4 robustness protocol:

- Dataset: frozen `clean_split_v2/test`
- Samples: 85
- Threshold: 0.35
- Attacks: FGSM and PGD
- Epsilon values: 0.005, 0.01, 0.02, 0.04
- PGD steps: 10
- PGD alpha: epsilon / 10
- PGD start: clean image (zero-start)
- Attack objective: untargeted L-infinity

Candidate robustness artifact:

- File: `results/v2_advtrained_eps001_robustness_test.csv`
- Rows: 680
- SHA-256: `717DDC251EE9921B182080D1A7767B6C613B839A7BA7A07F8D3ED28DB3FED6D3`

### Candidate results

| Attack | Epsilon | Flip rate | Conditional ASR | Conditional n |
|---|---:|---:|---:|---:|
| FGSM | 0.005 | 3.53% | 7.14% | 28 |
| FGSM | 0.010 | 5.88% | 14.29% | 28 |
| FGSM | 0.020 | 17.65% | 42.86% | 28 |
| FGSM | 0.040 | 27.06% | 57.14% | 28 |
| PGD | 0.005 | 9.41% | 25.00% | 28 |
| PGD | 0.010 | 23.53% | 53.57% | 28 |
| PGD | 0.020 | 36.47% | 67.86% | 28 |
| PGD | 0.040 | 45.88% | 75.00% | 28 |

Production conditional ASR for comparison:

| Attack | Epsilon | Production ASR | Candidate ASR |
|---|---:|---:|---:|
| FGSM | 0.005 | 8.70% | 7.14% |
| FGSM | 0.010 | 8.70% | 14.29% |
| FGSM | 0.020 | 13.04% | 42.86% |
| FGSM | 0.040 | 47.83% | 57.14% |
| PGD | 0.005 | 13.04% | 25.00% |
| PGD | 0.010 | 39.13% | 53.57% |
| PGD | 0.020 | 60.87% | 67.86% |
| PGD | 0.040 | 69.57% | 75.00% |

The clean-correct phishing denominator differed:

- Production: 23
- Candidate: 28

Therefore conditional ASR should be interpreted together with the clean baseline rather than as an isolated percentage.

### Perturbation integrity

Maximum observed L-infinity perturbations were:

- epsilon 0.005: 0.005000025
- epsilon 0.010: 0.010000020
- epsilon 0.020: 0.020000011
- epsilon 0.040: 0.040000021

The small excesses are floating-point numerical error and are consistent with the requested epsilon bounds.

## Interpretation

The adversarially trained candidate did not demonstrate an improvement over the frozen production model under this evaluation.

On clean test data at threshold 0.35, the candidate had slightly higher phishing recall (90.91% vs 88.64%) but lower accuracy (60.00% vs 64.71%) and lower F1 (70.18% vs 72.22%).

Under the tested adversarial protocol, the candidate generally had higher conditional attack-success rates, particularly under PGD. The candidate therefore does not provide evidence of improved robustness for this experiment.

## Production decision

Production remains:

- Model: `models/phishvision_cnn_v2.pth`
- SHA-256: `1403582CCE07BE1E36E70E4A0D425CFB152B86C7ABEE5D1074DEF79CBB2FB628`
- CNN threshold: 0.35

The adversarial checkpoint remains an experimental artifact and is not used by the application.

## Methodological note

The historical FGSM implementation used by the reproduced training recipe operates on the supplied image tensor before the explicit normalization step used for model inference. This behavior was preserved for protocol fidelity rather than silently changing the historical training method. The robustness evaluation itself uses the established Phase 4 evaluator protocol.

## Conclusion

Phase 5.1 adversarial training is complete. The experiment is reproducible, the candidate and robustness artifacts are hash-recorded, and the production lineage remains frozen.
