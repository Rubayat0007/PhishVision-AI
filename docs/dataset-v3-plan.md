# Dataset v3 — collection and split plan (Phase 2.1)

The 555-image set cannot support quality claims: 735 near-duplicate pairs span
its splits, and leakage-free F1 is 0.608 against a leaky 0.722. v3 exists to
replace it, not to extend it. The v2 files stay untouched; v3 gets a new name.

## Sources

| Class | Source | Rule |
|---|---|---|
| phishing | Public phishing feeds, URL ranking lists | Check terms and licence per feed; record the licence in the manifest; respect takedowns |
| legitimate | Public popularity rankings **plus deliberately chosen hard negatives** | Include real login, banking, mail, e-commerce pages. Easy negatives inflate every score |

Hard negatives are mandatory: if the legitimate class is mostly simple brochure
pages, the audit in 1.4 and the AUC in 1.2 will not transfer to the pages that
actually matter.

## Capture protocol

- Isolated VM or container, no credentials entered, no downloads executed,
  snapshot discarded afterwards.
- Fixed viewport set (e.g. 1280×720 and 1920×1080), full-page and viewport
  screenshots, recorded in the manifest.
- One row per image; never overwrite a captured file.

## Manifest (enforced by `scripts/validate_manifest.py`)

Required per image: `filename`, `sha256`, `phash`, `label`
(`phishing|legitimate`), `label_basis`, `label_confidence`, `registered_domain`,
`brand_cluster`, `kit_cluster`, `captured_at` (ISO-8601), `source`, `license`,
`split` (`train|validation|test|sealed`).

The validator rejects: duplicate filenames or content hashes, malformed digests,
invalid labels or splits, bad timestamps, missing fields, any
`(registered_domain, kit_cluster)` group spanning splits, any brand appearing in
train and test/sealed, and a sealed holdout below 100 images (pilot floor).

## Split rules

1. **Cluster first.** Exact duplicates by SHA-256, near-duplicates by perceptual
   hash (Hamming ≤ 6), and kit/domain groupings decide the unit of splitting.
2. **Whole clusters only.** A cluster, domain, or brand appears in exactly one
   split. The validator enforces it; the 555-image set failed this rule.
3. **Time-aware.** Older captures train; newer validation and test. Splits are
   recorded with their date ranges.
4. **Sealed holdout.** Target 300 images per class. At p≈0.75 that is roughly
   ±5 percentage points; at 100 per class it is ±9. Read once, by one script,
   access logged; after reading it becomes CONSUMED.

## Acceptance for the pilot

- A 50-image pilot manifest exists and passes `validate_manifest.py`.
- Both classes present in every split; sealed slice reserved (≥100 for the
  pilot, 300/class for the full set).
- No cluster spans splits: verified by re-running the perceptual-hash audit on
  the pilot images, not only on the manifest.
- The v2 set is untouched and its ledger rows remain as recorded.

## What would invalidate v3

- Any split built by shuffling rows rather than clusters.
- Any hard-negative review skipped.
- Any tuning against the sealed holdout, or reading it more than once.
- Reporting v3 numbers without the manifest hash and cluster audit.

## Ethics

Capture only pages you are entitled to view; never authenticate; treat every
capture as hostile content; store hashes and features where possible, and
delete raw captures that are not needed. Record the licence for every feed used.

## Capture attempt on this host (2026-10-24)

Before asking for manual collection, an automated attempt was made to capture
legitimate pages with the browsers already installed:

| Attempt | Result |
|---|---|
| `msedge.exe --headless=new --screenshot=...` | no file produced, no error output |
| `chrome.exe --headless --user-data-dir=... --screenshot=...` | no file produced |
| `urllib` GET of `https://www.wikipedia.org/` | HTTP 403 through the proxy |

Reachable hosts (pypi, github, stratosphereips) are allowlisted by the proxy;
general browsing is blocked, and headless capture produces nothing on this host.

Consequence: **neither class can be captured here.** The pilot needs a machine
with normal browsing and an isolated VM for the phishing half. The tooling
(`build_manifest.py`, `validate_manifest.py`) is ready and tested against
synthetic images; it has not yet been run on real captures.
