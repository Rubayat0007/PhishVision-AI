# PhishVision-AI — v3 Architecture Experiment Record

## Experiment

Date: 2026-10-04

Purpose:
Evaluate whether replacing the parameter-heavy v2 classifier with
AdaptiveAvgPool-based global feature aggregation improves performance
while substantially reducing model size.

## Frozen controls

Dataset:
- data/clean_split_v2
- Train: 387 images
- Validation: 83 images
- Test: 85 images
- Split: 70/15/15
- Seed: 42

Input:
- 224x224 RGB
- ImageNet normalization
- Same preprocessing as v2

Feature extractor:
- Conv 3 -> 32
- Conv 32 -> 64
- Conv 64 -> 128
- ReLU + 2x2 max pooling after each convolution

## v2 baseline

Model:
- models/phishvision_cnn_v2.pth

SHA-256:
- 1403582CCE07BE1E36E70E4A0D425CFB152B86C7ABEE5D1074DEF79CBB2FB628

Parameters:
- 25,784,130

Production threshold:
- 0.35

Test results:
- Accuracy: 64.71%
- Precision: 60.94%
- Recall: 88.64%
- F1: 0.7222
- TN/FP/FN/TP: 16/25/5/39

95% Wilson CIs:
- Accuracy: 54.11% - 74.03%
- Recall: 76.02% - 95.05%

## v3 architecture

Model:
- models/phishvision_cnn_v3.pth

SHA-256:
- 9D5B904C0806D0D27AD52A4CCA946F642CFCAA4FE7486C0C1572DE86D3671829

Parameters:
- 93,506

Classifier change:
- v2:
  128x28x28 -> Flatten -> Linear(100352,256)
  -> ReLU -> Dropout(0.5) -> Linear(256,2)
- v3:
  128x28x28 -> AdaptiveAvgPool(1,1)
  -> Flatten -> Linear(128,2)

Training controls:
- Batch size: 32
- Learning rate: 0.0003
- Adam optimizer
- Weight decay: 1e-4
- Maximum epochs: 20
- ReduceLROnPlateau scheduler
- Early stopping patience: 5
- Class-weighted cross-entropy
- Best checkpoint selected by validation phishing F1

Validation threshold selection:
- Validation only
- Best observed validation F1 at threshold 0.50
- Validation F1: 0.7216
- Test set was not used for threshold selection

## v3 validation

At threshold 0.50:
- Accuracy: 67.47%
- Precision: 64.81%
- Recall: 81.40%
- F1: 0.7216

At threshold 0.35:
- Accuracy: 55.42%
- Precision: 53.85%
- Recall: 97.67%
- F1: 0.6942

## v3 final test

Frozen threshold:
- 0.50

Results:
- Accuracy: 63.53%
- Precision: 61.82%
- Recall: 77.27%
- F1: 0.6869
- TN/FP/FN/TP: 20/21/10/34

95% Wilson CIs:
- Accuracy: 52.92% - 72.97%
- Recall: 63.01% - 87.16%

## Observed comparison

Relative to v2 @ 0.35 on the same frozen test set:

- Accuracy: -1.18 percentage points
- Precision: +0.88 percentage points
- Recall: -11.37 percentage points
- F1: -0.0353
- False positives: 25 -> 21
- False negatives: 5 -> 10

## Decision

Retain v2 as the production baseline.

Do not change:
- src/config.py
- ACTIVE_MODEL_PATH
- CNN_THRESHOLD
- production analyzer
- production predictor

Keep v3 as an experimental checkpoint for research comparison.

## Interpretation and limitations

The v3 architecture reduced parameter count by approximately 276x,
but did not improve the selected test metrics relative to the frozen
v2 production baseline.

The experiment demonstrates a performance tradeoff, not a causal
explanation of why v3 performs differently.

The test set was evaluated only after the v3 checkpoint and threshold
were frozen. The test results were not used to select the architecture
or threshold.

The confidence intervals describe uncertainty around the observed
test proportions. They do not establish statistical significance of
the difference between v2 and v3.

No conclusion is made about generalization beyond this dataset.

Status:
- v2 remains production baseline
- v3 remains experimental
- Architecture experiment complete
