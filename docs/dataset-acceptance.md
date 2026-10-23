# Dataset acceptance

How to accept the local screenshot dataset before any data-dependent result
(loader behaviour, evaluation numbers, robustness study) is treated as
valid.

## Why this exists

The tests prove the *loader mechanics* and the *metric maths* without any
dataset. Neither proves anything about the data itself. This procedure is
the missing gate, and it is deliberately a runbook rather than a unit test:
the dataset is not committed, so CI cannot check it.

## Expected layout

```text
data/clean_split_v2/
├── train/
│   ├── legitimate/
│   └── phishing/
├── validation/
│   ├── legitimate/
│   └── phishing/
└── test/
    ├── legitimate/
    └── phishing/
```

Split names are discovered as the immediate subdirectories of the root.
Only `.jpg`, `.jpeg`, `.png`, and `.webp` files are counted. `data/` is
ignored by Git; it must never be committed.

## Procedure

1. Record where the data came from (source, collection date, any cleaning
   steps). Provenance that is only in someone's memory is not provenance.
2. Run the validator from the repository root:

   ```powershell
   python scripts/validate_dataset.py data/clean_split_v2 `
       --json-output results/dataset_manifest.json
   ```

3. Treat the run as accepted only when all of the following hold:
   - exit code `0`, and `valid: true` in the manifest;
   - `cross_split_duplicates` is empty — identical images across train /
     validation / test invalidate any evaluation that follows;
   - `corrupt_files` is empty;
   - every split contains both classes with a non-zero count;
   - the class ratio per split is recorded and a deliberate decision, not
     an accident.
4. Commit `results/dataset_manifest.json` when the data is accepted, so the
   counts and hashes are tied to a commit. Regenerate it whenever the data
   changes.

## What the manifest contains

| Field | Meaning |
|---|---|
| `splits` | images per split and class |
| `totals` | images per class and overall |
| `cross_split_duplicates` | identical content spanning splits — hard failure |
| `identical_content` | all duplicate groups, including within a split |
| `filename_collisions` | same basename in more than one place |
| `corrupt_files` | files that could not be decoded |
| `valid`, `errors` | verdict and every reason it failed |

Paths are POSIX-style so the manifest is identical on every platform.

## What this does not establish

- That labels are correct. The validator checks structure, not truth.
- That the split is stratified or representative; it only checks that the
  same image does not appear twice.
- Anything about detection quality. A clean manifest is a precondition for
  an evaluation, not a result.
- That the production model is suitable for this data. That requires an
  evaluation run on the accepted split, recorded under `results/` with the
  model digest from `src/models/integrity.py`.

## Rules

- Do not synthesise a dataset to make the pipeline look validated. Synthetic
  images are appropriate for loader mechanics tests; they are not evidence
  about phishing detection.
- Do not commit `data/`. Do not commit generated evaluation CSVs (already
  ignored); commit the manifest and the reports that interpret it.
