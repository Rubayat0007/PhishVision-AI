# Leakage-free evaluation on the existing images

555 images, 324 perceptual clusters at Hamming <= 6.
New split: train 389, val 83, test 83 images.
Clusters spanning two splits in the rebuilt assignment: **0** (must be 0).

| Test set | n | accuracy | precision | recall | F1 | AUC |
|---|---|---|---|---|---|---|
| original test (leaky) | 85 | 0.6471 | 0.6094 | 0.8864 | 0.7222 | 0.6946 |
| cluster-split test | 83 | 0.6265 | 0.5333 | 0.7059 | 0.6076 | 0.6573 |

F1 difference (original minus cluster-split): **+0.1146**.

## Reading this

- The cluster-split number is the one to trust: no image in its test set
  shares a near-duplicate cluster with training data.
- The gap quantifies how much of the earlier score came from leakage;
  both are development-set numbers and neither is a sealed-holdout result.
- Clustering by dHash is conservative but imperfect: crops and overlays can
  evade it, so residual leakage cannot be ruled out.
