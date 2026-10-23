# Evidence ledger — PhishVision-AI

Rows are append-only. Replaced rows are marked superseded, never deleted.
A number without a row does not go in a README or report.

| ID | commit | date | script / command | data | n | model digest | thr | metrics | CI | status |
|---|---|---|---|---|---|---|---|---|---|---|
| R-PV-dataset-01 | 7b474ed | 2026-10-24 | `scripts/validate_dataset.py data/clean_split_v2` | clean_split_v2 (555; 387/83/85) | 555 | — | — | valid true, no cross-split duplicates, no corrupt | — | RECORDED |
| R-PV-integrity-01 | 7b474ed | 2026-10-24 | `scripts/provision_model.py` then predictor load | v2 release artifact, 103,141,173 bytes | — | `1403582C…B2FB628` (match) | — | digest match, forward pass ok | — | RECORDED |
| R-PV-v2-val-035 | 7b474ed | 2026-10-24 | `scripts/compare_models.py` | val | 83 | `1403582C…` | 0.35 | prec .5938 rec .8837 F1 .7103 acc .6265 | — | RECORDED |
| R-PV-v2-test-035 | 7b474ed | 2026-10-24 | `evaluate_predictor.py --split test` + Unified metrics tool | test (44 ph / 41 legit) | 85 | `1403582C…` | 0.35 | acc .6471 prec .6094 rec .8864 F1 .7222 AUC .6946; TP39 FP25 FN5 TN16 | bootstrap 5,000, seed 42: acc .541–.753, F1 .617–.810, AUC .578–.801 | RECORDED, DEVELOPMENT |
| R-PV-advtrained-val | 7b474ed | 2026-10-24 | `scripts/compare_models.py` | val | 83 | candidate (nids) | 0.35 | F1 .7959 rec .9070 prec .7091 | — | RECORDED |
| R-PV-advtrained-test | 7b474ed | 2026-10-24 | `scripts/compare_models.py` | test | 85 | candidate | 0.35 | F1 .6990 prec .6102 rec .8182 | — | RECORDED, DEVELOPMENT |
| R-PV-threshold-01 | 7b474ed | 2026-10-24 | `scripts/threshold_study.py` | val → test | 83 / 85 | `1403582C…` | 0.35 vs 0.50 | val selected 0.50 by Youden J; test F1 .5823 at 0.50 vs .7222 at 0.35 | — | RECORDED, DEVELOPMENT |
| R-PV-components-01 | 7b474ed | 2026-10-24 | `scripts/component_diagnostics.py` | val, no URL | 83 (40 legit / 43 phish) | `1403582C…` | 0.35 | AUC: text .7419, CNN .7424, combined .8041; Brier .206, ECE .0821; bins 0.2–0.4 predicted .313 observed .421, 0.4–0.6 .498/.462, 0.6–0.8 .704/.842 | bootstrap 2,000: text .650–.830, CNN .638–.836, combined .705–.890 | RECORDED, DEVELOPMENT |
| R-PV-tests-01 | 7b474ed | 2026-10-24 | `python -m pytest -q` | — | 159 | — | — | 131 fast + 28 slow, all pass | — | RECORDED |

Notes:
- `val` and `test` are DEVELOPMENT; `test` is burned (see `docs/evaluation-register.md`).
- No row here is a sealed-holdout result; none may be described as unseen.
