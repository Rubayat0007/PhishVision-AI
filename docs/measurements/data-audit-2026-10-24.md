# Data audit — 555-image dataset

Images 555: train 387, val 83, test 85; legitimate 268, phishing 287.

## Near-duplicates (dHash, Hamming <= 6)

- within a split: **839** pairs
- across splits: **735** pairs
  - legitimate_0004.jpg ↔ legitimate_0024.jpg (distance 5)
  - legitimate_0004.jpg ↔ legitimate_0142.jpg (distance 4)
  - legitimate_0004.jpg ↔ phishing_0054.jpg (distance 1)
  - legitimate_0004.jpg ↔ phishing_0181.jpg (distance 6)
  - legitimate_0004.jpg ↔ phishing_0259.jpg (distance 3)
  - legitimate_0006.jpg ↔ legitimate_0050.jpg (distance 6)
  - legitimate_0006.jpg ↔ phishing_0091.jpg (distance 5)
  - legitimate_0006.jpg ↔ phishing_0138.jpg (distance 5)
  - legitimate_0006.jpg ↔ phishing_0207.jpg (distance 5)
  - legitimate_0014.jpg ↔ legitimate_0021.jpg (distance 0)

## Shortcut check (metadata only)

Train CV-5 accuracy 0.5581, val accuracy 0.5783 against majority baseline 0.5181 → **no strong metadata shortcut on this split**.

## Open items

- Hard-negative coverage: needs human review of the legitimate images.
- Label noise: needs a re-labelled sample; not estimated here.

## Limits

- dHash catches re-encodes and small edits, not crops or overlays; a low
  count is not proof of independence.
- The shortcut check uses only coarse metadata; a null result does not
  prove there is no shortcut in finer pixel statistics.

## What the duplicate counts mean

839 near-duplicate pairs inside a split and **735 pairs across splits** is not
a mild redundancy: for 555 images it means clusters of near-identical
screenshots span train/val/test. Exact-duplicate checking (validate_dataset.py)
missed all of them, so the earlier "no cross-split duplicates" statement was
true only at byte level.

Consequences:

- The development-set metrics (acc 64.7 %, F1 72.2 %) are optimistically biased:
  validation and test share near-identical images with training data.
- The component AUCs (text .742, CNN .742, combined .804) inherit the same bias.
- Any new dataset must be split by *perceptual cluster and source*, not by file,
  and the split must be verified with this script before any evaluation.

This does not retroactively invalidate the engineering findings (integrity,
pipeline behaviour, calibration shape), but it does bound every quality claim
to "development set with near-duplicate leakage".

Open: whether the 735 pairs are true duplicates or merely similar-looking
screenshots. A human must review a sample before the threshold (Hamming <= 6)
is trusted; that review is listed as BLOCKED, not assumed.
