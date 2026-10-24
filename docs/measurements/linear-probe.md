# Frozen-backbone linear probe (Phase 4.2)

Train n=84, validation n=19, 256 features. Test split untouched.

| Model | train CV AUC | validation AUC |
|---|---|---|
| frozen features + logistic (C=0.05) | 0.6701 ± 0.1035 | 0.5 |
| tuned production head | — | 0.5556 |

## Operating point at recall >= 0.50 (chosen on validation)

| Model | threshold | recall | FPR | FPR 95% CI |
|---|---|---|---|---|
| probe | 0.5887 | 0.5 | 0.4444 | 0.1888-0.7334 |
| baseline | 0.4435 | 0.5 | 0.4444 | 0.1888-0.7334 |

## Reading this

- Probe AUC 0.500 vs baseline 0.556 on validation.
- Train CV AUC 0.670 collapsing to 0.500 on validation is the signature of over-fitting on 84 rows, not of a better head.
- With n=15-19 validation images, neither outcome can be distinguished from noise; this experiment cannot settle the question it was designed for.

## Limits

- Linear probe on 256-dim features with ~80 training rows: strong
  regularisation, but over-fitting risk remains and CV is optimistic.
- Feed-derived labels; pilot only; no promotion decision follows.
