# Evaluation run

How to produce a defensible evaluation result for the frozen v2 model, and
what makes it traceable. Blocked until the dataset exists; the procedure is
recorded now so the run is mechanical when the data arrives.

## Preconditions

1. `data/clean_split_v2/` present in the accepted layout
   (`<split>/<legitimate|phishing>/<image>`).
2. Dataset accepted per `docs/dataset-acceptance.md`, with
   `results/dataset_manifest.json` committed.
3. Production checkpoint provisioned and verified:

   ```powershell
   python scripts/provision_model.py
   ```

   Expected digest: `1403582CCE07BE1E36E70E4A0D425CFB152B86C7ABEE5D1074DEF79CBB2FB628`.
4. Clean working tree, so the recorded commit identifies the exact code.

## Procedure

```powershell
# 1. Dataset gate
python scripts/validate_dataset.py data/clean_split_v2 `
    --json-output results/dataset_manifest.json

# 2. Per-image evaluation on the test split
python scripts/evaluate_predictor.py --split test `
    --model models/phishvision_cnn_v2.pth `
    --threshold 0.35 `
    --output results/evaluation/v2-test-035/predictions.csv

# 3. Metrics from those predictions
python ../Unified-Cybersecurity-Platform/tools/evaluate_predictions.py
    results/evaluation/v2-test-035/predictions.csv `
    --score-column p_phish --threshold 0.35 `
    --positive-name phishing `
    --output-dir results/evaluation/v2-test-035
```

Step 2 needs the PhishVision virtual environment (torch, torchvision,
EasyOCR). Step 3 is stdlib-only. The metrics CLI lives in the Unified platform repository; PhishVision does not duplicate it. `evaluate_predictions.py` refuses to
overwrite; use a new directory per run.

## What to record with the result

| Item | Where it comes from |
|---|---|
| Code version | `git rev-parse HEAD` at run time |
| Dataset identity | SHA-256 inside `results/dataset_manifest.json` |
| Model identity | digest printed by the predictor (`model_sha256`) |
| Threshold | the `--threshold` passed to both steps (must match) |
| Per-image predictions | `predictions.csv` from step 2 |
| Metrics | `summary.json`, `per_class_metrics.csv`, `roc_curve.csv` |

A report without dataset digest, model digest, and commit is an anecdote.

## Acceptance criteria

- Exit code `0` from the validator and both evaluation steps.
- Dataset manifest `valid: true`, no cross-split duplicates.
- `predictions.csv` row count equals the test-split image count.
- Metrics recorded, with the threshold stated in the report.
- Any comparison against a previously recorded run names both runs' digests
  and thresholds; a result produced at a different threshold is not a
  regression.

## What this run does not establish

- Generalisation beyond this split and this dataset.
- That the threshold is optimal: 0.35 is the frozen production threshold,
  and it is reported, not tuned.
- Robustness. Adversarial results live in `results/phase4_*` and
  `results/phase5_*` and were produced by the dedicated evaluators.
- Fusion value. That requires paired events (`docs/research/`).

## Rules

- Never tune the threshold on the test split and report it as held-out.
- Never refresh a recorded result to make a comparison look better; record a
  new run with its own provenance.
- Do not commit `predictions.csv` or metric CSVs (`results/*.csv` is
  ignored); commit the manifest and the human-written report.
