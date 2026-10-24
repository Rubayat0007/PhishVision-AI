# Pre-registered experiments

Written before the v3 pilot and sealed holdout exist, so that later results
cannot be reinterpreted after the fact. Each entry states the hypothesis, the
decision rule, the metric, and the threshold that decides promotion. Nothing here
may be edited after data exists; a change requires a new entry with a date.

Context: the current evaluation set is DEVELOPMENT (555-image v2, 735 cross-split
near-duplicate pairs, leakage-free F1 0.608, component AUCs text 0.638 / CNN
0.657 / combined 0.694). All figures below are hypotheses to test, not results.

---

## P-1 — Decision rule: risk score >= 25/100

**Hypothesis.** Moving the operating point from the current behaviour to
`risk_score >= 25` cuts the false-positive rate substantially at a small recall
cost. Study on cached validation scores (n=83, DEVELOPMENT) predicted
FPR 7.5 %, recall 60.5 %, F1 0.722.

**Primary metric.** False-positive rate on the sealed holdout, at fixed recall
floor.

**Decision.**
- Promote if `FPR <= 0.15` **and** `recall >= 0.50`.
- Reject if `FPR > 0.15` or `recall < 0.50`.
- If rejected, the current operating point stands and this entry is reported as a
  failed hypothesis, not deleted.

**Risks acknowledged in advance.** The candidate was selected on data already used
for earlier choices; regression on new data is the expected outcome unless the
effect is real. n=83 with 40 negatives means a single case moved FPR by 2.5 points.

---

## P-2 — CNN demotion below text

**Hypothesis.** The CNN does not earn its 40 % weight: on leakage-free data its
AUC (0.657) is within noise of the text heuristic's (0.638), and at operating
points the text signal is nearly inactive (recall 0 when required to fire).

**Test.** Three candidates on the sealed holdout, identical preprocessing:
1. current weights (text 30 / URL 30 / CNN 40, URL absent on screenshots);
2. text-weighted (text 60 / CNN 40);
3. CNN-only.

**Primary metric.** F1 and FPR at the P-1 operating point.

**Decision.** The CNN keeps its 40 % weight only if its F1 exceeds the
text-weighted candidate by at least **0.02 absolute** (the existing
`MIN_F1_GAIN` rule). Otherwise weights are rebalanced and the production profile
is republished.

---

## P-3 — Fusion weighting with a URL present

**Hypothesis.** The documented 30/30/40 weighting has never been exercised on a
dataset image, because dataset images carry no URL. The URL component's real
contribution is unknown.

**Test.** Capture 100 phishing screenshots *with* their URLs, 100 without, and
compare F1. Report both, never only the better one.

**Decision.** Publish two profiles — with and without URL — rather than one
profile that silently mixes conditions. A consumer that supplies no URL must not
inherit a number measured with one.

---

## Access protocol for the sealed holdout

- Written before first access; the file lists who, when, and which commit.
- Read exactly once, by `scripts/evaluate_predictor.py --split sealed`.
- The result is recorded verbatim in the ledger, including a negative result.
- After reading, the split is marked CONSUMED and may never be re-read for
  tuning. Any further experiment needs newly captured data.

## Stopping rules

- No threshold may be chosen after seeing sealed results.
- No experiment may be re-run on the sealed split with a modified hypothesis.
- A failed hypothesis is reported with the same prominence as a passing one.

## What would falsify this whole document

If the sealed results contradict every prediction here, the correct conclusion is
that the development set is unrepresentative — not that the hypotheses were
"nearly right" and need a small adjustment.
