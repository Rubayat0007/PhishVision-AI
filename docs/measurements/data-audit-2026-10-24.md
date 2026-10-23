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
