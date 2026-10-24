# Project status — PhishVision-AI

Single entry point. Every number states its evidence label; every claim links to
the file that produced it. Last updated 2026-10-24.

## What this system is

A screenshot-based phishing detector: OCR text heuristics + a CNN, combined into a
risk score, with integrity-checked model loading and an evidence ledger.

## Headline numbers (read the labels)

| Claim | Value | Label | Source |
|---|---|---|---|
| Production model digest | `1403582C…FB628` | VERIFIED | `docs/models/registry.json` |
| Leakage-free dev F1 | 0.608 | RECORDED | `R-PV-leakagefree-01` |
| Leak-free component AUCs | text .638 / CNN .657 / combined .694 | RECORDED | `R-PV-components-cluster-01` |
| Pilot FPR (n=18 test) | 0.333 (CI 0.12–0.65) | HYPOTHESIS | `docs/measurements/pilot-eval.md` |
| Pilot recall (n=18 test) | 0.600 (CI 0.31–0.83) | HYPOTHESIS | same |
| Pilot phishing labels doubtful | 32% (21/65) | RECORDED | `docs/measurements/pilot-triage.md` |
| Near-duplicate leakage in old data | 735 cross-split pairs | RECORDED | `R-PV-dataaudit-01` |
| Old-data F1 overstatement | 0.722 → 0.608 | RECORDED | `R-PV-leakagefree-01` |

## Hypotheses tested, and their verdicts

| ID | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| P-1 | risk ≥ 25/100 cuts FPR at small recall cost | **REJECTED**: FPR 0.33→0.11 but recall 0.60→0.20 | `docs/measurements/pilot-rule-check.md` |
| P-2 | CNN does not earn its 40% weight | **UNTESTED** (needs sealed holdout) | `docs/pre-registered-experiments.md` |
| P-3 | URL weighting was never exercised | **UNTESTED** (no URL in any dataset image) | same |
| 4.2 | frozen embedding + new head improves benign side | **NO EVIDENCE**: probe AUC 0.50 vs baseline 0.56 | `docs/measurements/linear-probe.md` |
| 7.2 | evasion is the main adversarial risk | **NO**: recall stable, FPR rises; fragility is benign-side | `docs/measurements/adversarial-probe.md` |

## What is known to work

- Model integrity: digest verified before every load; registry with 7 distinct
  artifacts, one production (`src/models/registry.py`).
- Deterministic, shape-robust inference: 8 property tests
  (`tests/test_predictor_properties.py`).
- Data pipeline with guards that earned their keep: interstitial rejection (39
  URLs), blank rejection, exact and perceptual duplicate removal, cluster+domain
  +brand curation, OCR triage (`scripts/capture_pages.py`, `curate_pilot.py`,
  `triage_phishing.py`).
- Manifest validation and pilot build (`validate_manifest.py`, `build_manifest.py`).
- Claims-to-ledger check enforced in CI.

## What is blocked, and on what

| Blocked item | Blocked on |
|---|---|
| Reliability profile for v3 | ~50 images/class with *reviewed* labels |
| P-2, P-3 | sealed holdout (deferred until v3 volume exists) |
| More phishing captures | a URL-level feed with fresh data (PhishTank key; URLhaus 410; OpenPhish exhausted) |
| Label verification | human review of 64 phishing captures (declined; consequence recorded in `docs/measurements/pilot-label-status.md`) |

## Current dataset

`manifests/v3-pilot.json` — 121 images (63 phishing / 58 legitimate), valid,
0 clusters spanning splits, 0 cross-label clusters. Test split 9/9. Labels are
feed-derived, not reviewed.

## Reproduce every number

```powershell
python -m pytest -q                     # 165 fast, 36 slow
python scripts/leakage_free_eval.py     # leakage-free F1 (old data)
python scripts/component_diagnostics_cluster.py  # AUCs (slow: OCR)
python scripts/data_audit.py            # duplicate/shortcut audit
python scripts/evaluate_pilot.py        # pilot metrics
python scripts/pilot_rule_check.py      # P-1 dry run (slow)
python scripts/triage_phishing.py       # OCR label triage (slow)
python scripts/adversarial_probe.py     # FGSM probe
python scripts/linear_probe.py          # frozen-backbone probe
python scripts/check_claims.py          # README claims -> ledger rows
```

## The honest summary

Engineering is complete for the current scope: integrity, provenance, leakage
controls, uncertainty reporting, robustness tests, and a working data pipeline. The
model is **not** fit to certify benign pages: FPR 0.33–0.44 across three
independent measurements, and every cheap fix (threshold, head, calibration shape)
has been tested and failed. The binding constraint is labelled data volume and
quality, not code.
