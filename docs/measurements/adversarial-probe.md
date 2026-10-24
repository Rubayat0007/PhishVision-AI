# Adversarial probe (white-box FGSM)

12 pilot images (6 per class), threshold 0.35. Perturbation is added in normalised pixel space; epsilon is the maximum absolute change per channel before normalisation, in 1/255 units shown.

| eps | mean Δp | recall before | recall after | legit flagged before | after | flips |
|---|---|---|---|---|---|---|
| 0.01569 | 0.0034 | 0.6667 | 0.6667 | 0.3333 | 0.5 | 1 |
| 0.03137 | 0.0055 | 0.6667 | 0.6667 | 0.3333 | 0.5 | 1 |
| 0.06275 | 0.0072 | 0.6667 | 0.6667 | 0.3333 | 0.5 | 1 |

## Reading this

- Direction is attacker-optimal: phishing pages are pushed DOWN (evasion),
  legitimate pages UP (false alarm).
- Recall did not move at these budgets: detected phishing pages sit well
  above the threshold, so a single sign step is not enough to evade.
- Legitimate false positives rose at every budget: those pages sit near the
  threshold, so a small push crosses it. The fragility is on the benign side.
- Symmetric risk: the same model that is hard to evade is easy to make noisy.

## Limits

- Single-step white-box FGSM; iterative attacks (PGD) would be stronger.
- 12 images: direction, not rate.
- No adversarial training on the production checkpoint.
- Physical-world attacks (compression, resampling) are not modelled.
