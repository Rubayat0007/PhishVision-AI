"""Reassign splits per domain, stratified by class.

Hashing a domain into a split keeps a domain whole but can leave a split with no
phishing (or no legitimate) examples, which makes that split useless for
evaluation. This assigns whole domains to splits separately per label, so each
split gets both classes while no domain ever spans two splits.

Rewrites the `split` column of labels.csv in place. Deterministic: the domain
order is fixed by a seeded hash, so re-running changes nothing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path

SHARES = (("train", 0.70), ("validation", 0.15), ("test", 0.15))


def order_key(domain: str) -> str:
    return hashlib.sha256(domain.encode("utf-8")).hexdigest()


def assign(domains: list[str], minimum_per_split: int = 1) -> dict[str, str]:
    """Assign sorted domains to splits by share, guaranteeing >=1 when possible."""
    ordered = sorted(domains, key=order_key)
    total = len(ordered)

    if total == 0:
        return {}

    result: dict[str, str] = {}
    cursor = 0

    for index, (split, share) in enumerate(SHARES):
        remaining_splits = len(SHARES) - index - 1

        if index == len(SHARES) - 1:
            count = total - cursor
        else:
            count = max(minimum_per_split, round(total * share))
            count = min(count, total - cursor - remaining_splits)

        for domain in ordered[cursor:cursor + count]:
            result[domain] = split

        cursor += count

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=Path("captures/labels.csv"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with args.labels.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    domain_labels: dict[str, str] = {}
    for row in rows:
        domain = row["registered_domain"]
        label = row["label"]
        if domain in domain_labels and domain_labels[domain] != label:
            raise SystemExit(f"domain {domain} has conflicting labels")
        domain_labels[domain] = label

    by_label: dict[str, list[str]] = defaultdict(list)
    for domain, label in domain_labels.items():
        by_label[label].append(domain)

    mapping: dict[str, str] = {}
    for label, domains in by_label.items():
        assigned = assign(domains)
        print(f"{label}: {len(domains)} domain(s) -> "
              + ", ".join(f"{split}={sum(1 for s in assigned.values() if s == split)}"
                          for split, _ in SHARES))
        mapping.update(assigned)

    changed = 0
    for row in rows:
        new_split = mapping[row["registered_domain"]]
        if row["split"] != new_split:
            changed += 1
        row["split"] = new_split

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        counts[row["split"]][row["label"]] += 1

    for split, classes in counts.items():
        print(f"  {split}: {dict(classes)}")

    if args.apply:
        with args.labels.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nrewrote {len(rows)} rows ({changed} split values changed)")
    else:
        print(f"\ndry run ({changed} rows would change); re-run with --apply")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
