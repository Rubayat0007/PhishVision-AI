"""Curate the pilot: drop cross-label clusters, split by cluster.

Two operations, both structural rather than case-by-case:

1. A perceptual-hash cluster containing both labels is a contradiction: two
   near-identical images cannot be both legitimate and phishing. All images in
   such a cluster are removed, because the data cannot say which label is wrong.
2. Splits are then assigned per cluster (not per domain), so no cluster can span
   two splits even when one phishing kit appears under several domains.

Dry run by default; pass --apply to delete images and rewrite labels.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

HAMMING = 6
SHARES = (("train", 0.70), ("validation", 0.15), ("test", 0.15))


def dhash(path: Path) -> int:
    with Image.open(path) as handle:
        small = handle.convert("L").resize((9, 8), Image.LANCZOS)
        pixels = np.asarray(small, dtype=np.int16)

    value = 0
    for bit in (pixels[:, 1:] > pixels[:, :-1]).flatten():
        value = (value << 1) | int(bit)
    return value


def clusters_of(items):
    """Union images that are near-identical OR share a domain OR a brand.

    All three are leakage channels; a group that violates any of them must stay
    in one split, so they are merged into a single super-cluster.
    """
    parent = list(range(len(items)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(left, right):
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            same_hash = bin(items[i]["hash"] ^ items[j]["hash"]).count("1") <= HAMMING
            same_domain = (items[i]["domain"] and items[i]["domain"] == items[j]["domain"])
            same_brand = (items[i]["brand"] and items[i]["brand"] == items[j]["brand"])

            if same_hash or same_domain or same_brand:
                union(i, j)

    groups = defaultdict(list)
    for index in range(len(items)):
        groups[find(index)].append(index)
    return list(groups.values())


def assign_clusters(cluster_labels, cluster_sizes) -> dict[int, str]:
    """Stratified across labels; whole clusters to one split; >=1 per split."""
    mapping: dict[int, str] = {}

    for label in sorted(set(cluster_labels.values())):
        indices = [i for i, value in cluster_labels.items() if value == label]
        indices.sort(key=lambda i: -cluster_sizes[i])

        total = sum(cluster_sizes[i] for i in indices)
        targets = {split: total * share for split, share in SHARES}
        filled = {split: 0 for split, _ in SHARES}

        for index in indices:
            split = max(SHARES, key=lambda s: targets[s[0]] - filled[s[0]])[0]
            mapping[index] = split
            filled[split] += cluster_sizes[index]

    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, default=Path("captures"))
    parser.add_argument("--labels", type=Path, default=Path("captures/labels.csv"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with args.labels.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    items = []
    for row in rows:
        path = args.captures / row["filename"]
        items.append({"filename": row["filename"], "label": row["label"],
                      "domain": row["registered_domain"],
                      "brand": row["brand_cluster"],
                      "hash": dhash(path)})

    groups = clusters_of(items)

    contradictory = []
    for group in groups:
        labels = {items[i]["label"] for i in group}
        if len(labels) > 1:
            contradictory.extend(items[i]["filename"] for i in group)

    print(f"images {len(items)}, clusters {len(groups)}, "
          f"contradictory images {len(contradictory)}")

    keep = [row for row in rows if row["filename"] not in set(contradictory)]
    kept_names = {row["filename"] for row in keep}
    kept_items = [item for item in items if item["filename"] in kept_names]
    kept_groups = clusters_of(kept_items)

    cluster_labels = {index: kept_items[group[0]]["label"]
                      for index, group in enumerate(kept_groups)}
    cluster_sizes = {index: len(group) for index, group in enumerate(kept_groups)}
    mapping = assign_clusters(cluster_labels, cluster_sizes)

    split_of = {}
    for index, group in enumerate(kept_groups):
        for item_index in group:
            split_of[kept_items[item_index]["filename"]] = mapping[index]

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in keep:
        row["split"] = split_of[row["filename"]]
        counts[row["split"]][row["label"]] += 1

    for split in ("train", "validation", "test"):
        print(f"  {split}: {dict(counts[split])}")

    if not args.apply:
        print("\ndry run: re-run with --apply to delete the contradictory images "
              "and rewrite splits")
        return 0

    for name in contradictory:
        (args.captures / name).unlink(missing_ok=True)

    with args.labels.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(keep)

    print(f"\nremoved {len(contradictory)} contradictory image(s); "
          f"{len(keep)} row(s) remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
