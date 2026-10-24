# Pilot label status — decision record

Date: 2026-10-24
Decision by: project owner
Recorded by: engineering

## The decision

Visual review of the 64 phishing captures was declined as unnecessary
("not a big deal"). Engineering advised that it matters, for the reasons below.
The decision stands; this note records the consequence so that later results are
read correctly.

## What the labels currently mean

`label = phishing` means **the URL appeared in the OpenPhish feed**, not that the
screenshot shows a phishing page. The capture tool already rejects:

- blank renders (bot walls, JS failures);
- known interstitials ("just a moment", "suspected malware", "suspected
  phishing", "verify you are human", Cloudflare Ray ID);
- byte-identical duplicates;
- clusters that mix labels (a page near-identical to both classes cannot carry
  either label honestly).

It cannot detect a parked domain, a dead campaign, or a brand-less dashboard
that renders without any challenge text.

## Evidence that this risk is real, not theoretical

| Observation | Number |
|---|---|
| Feed URLs rejected as blocked interstitials | 39 of 99 |
| Images dropped as cross-label contradictions | 9 |
| Old dataset: cross-split near-duplicate pairs | 735 |
| Old dataset: F1 overstatement from that contamination | 0.722 → 0.608 |

## Consequence for results

- Any metric computed on `manifests/v3-pilot.json` is labelled
  **UNVERIFIED-LABELS** in the ledger.
- No reliability profile may be published from this manifest, because the
  profile feeds the platform's benign-verdict gate. A wrong profile makes the
  system certify unsafe pages as safe.
- The pre-registered experiments (P-1, P-2) require the sealed holdout, not this
  pilot, and are unaffected.

## The cheap alternative offered

Automated triage: OCR each phishing capture and flag images with no brand token
and no credential vocabulary. It reduces, but does not eliminate, the need for a
human glance. It was offered on 2026-10-24; status: not yet run.
