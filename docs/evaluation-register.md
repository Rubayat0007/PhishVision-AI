# Evaluation register and evidence reconciliation

Phase 0 output for the PhishVision-AI repository. Purpose: make every reported
number traceable and stop treating consulted data as unseen.

## 0.7 Verification re-run — actual outputs

Recorded 2026-10-24 on `D:\Projects\PhishVision-AI`, commit `6ff3d52`.

| Command | Actual output | Exit |
|---|---|---|
| `python -m pytest -q -m "not slow"` | `131 passed, 28 deselected` | 0 |
| `python -m pytest -q` | `159 passed` | 0 |
| `python scripts/validate_dataset.py data/clean_split_v2` | `"images": 555`, `"valid": true` | 0 |

Unified platform: unit and integration discovery both `OK`, exit 0 (`7d66c7c`).
AI-NIDS: `102 passed`, exit 0 (`a0147f9`).

Incidental finding: generated CSVs under `results/evaluation/**` were untracked
but not ignored (`results/*.csv` only matched one level). Ignore rules were
widened to `results/**/*.csv` and `results/**/*.jpg` so evaluation artifacts
cannot accumulate as noise.

## Evaluation-set register — PhishVision

| Set | n | Status | Since |
|---|---|---|---|
| `train` | 387 | training data | creation |
| `val` | 83 | **DEVELOPMENT** — used for threshold selection, candidate comparison | v0.3.1 |
| `test` | 85 | **DEVELOPMENT (burned)** — used for reporting *and* two decisions (ID-1) | v0.3.2 |

No set in this repository is SEALED. Until a fresh sealed holdout exists, every
result is a **development-set result** and must be labelled as such.

## 0.1 Access history of `data/clean_split_v2/test`

| # | Access | Script | Purpose | Decision-influencing |
|---|---|---|---|---|
| 1 | baseline | `scripts/evaluate_predictor.py --split test` | produce `predictions.csv` at 0.35 | no |
| 2 | metrics | Unified `tools/evaluate_predictions.py` | F1 0.7222, AUC 0.6946 | no |
| 3 | uncertainty | `scripts/bootstrap_ci.py` | CIs for reported metrics | no |
| 4 | comparison | `scripts/compare_models.py` (test block) | v2 vs advtrained_v2 | **yes** |
| 5 | threshold | `scripts/threshold_study.py` (test block) | 0.35 vs 0.5 | **yes** |
| 6 | UI tests | `tests/test_app_ui.py` | rendering only; synthetic fixture | no |

Accesses 1–3 are report-only. 4 and 5 each produced a decision that was then
reported, which is why the set is burned. Any pre-session access is **unknown**
and must be supplied by the owner before this table is called complete.

## 0.2 Threshold narrative (ID-2 resolved)

The v0.3.1 study selected on validation by **Youden's J** (sensitivity +
specificity − 1), with F1 as tie-break. That objective chose **0.50**.

The older ledger recorded "highest F1 at 0.35 (0.7103), highest accuracy at 0.50
(0.6988)" — a different objective, which is the source of the apparent conflict.
Both statements are true of their own metric.

Honest wording for reports:

> The production threshold 0.35 was **retained after the test set was
> consulted**. A validation study using Youden's J selected 0.50; on the test
> split 0.50 scored F1 0.5823 against 0.7222 at 0.35, so 0.35 was kept. That
> comparison used test data and is therefore a development-set result, not an
> unseen evaluation.

## 0.3 Candidate-comparison narrative (ID-3)

Pre-registered rule (in `src/evaluation/model_selection.py`, tested): promote
only if validation F1 improves by ≥ 2 points and validation recall does not
drop. `phishvision_cnn_advtrained_v2.pth` passed on validation (F1 0.7959 vs
0.7103, recall 0.907 vs 0.884) and was evaluated **once** on test, where it
scored F1 0.6990 against 0.7222 for v2. Production stayed on v2.

Checkpoint-by-set matrix:

| Checkpoint | Val | Test |
|---|---|---|
| `phishvision_cnn_v2.pth` | yes | **yes** (baseline, study, bootstrap, comparison) |
| `phishvision_cnn_advtrained_v2.pth` | yes | **yes** (comparison only) |
| `cnn`, `backup`, `baseline_73`, `old`, `advtrained`, `v2_advtrained_eps001`, `v2-release` | yes | no |
| `phishvision_cnn_v3.pth` | load failed (architecture mismatch) | no |

## 0.4 Reclassification

`val` and `test` are recorded as DEVELOPMENT from this commit onward. Reports
that cite them must say "development-set". The next evaluation that informs a
decision requires a **new sealed holdout** (Phase 2), read once by one script
that logs the access.

## Consequences to carry forward

1. No further threshold or model selection on this dataset.
2. The reported 64.7 % accuracy / 72.2 % F1 / 0.695 AUC remain valid as
   *development-set* numbers with bootstrap CIs (F1 0.617–0.810).
3. A sealed holdout is now a prerequisite for any new claim, not a nicety.
