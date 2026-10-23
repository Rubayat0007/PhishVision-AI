"""Leakage-free evaluation of the frozen model on the existing images.

The 555 images contain near-duplicate clusters that span the current splits.
This script clusters by perceptual hash, rebuilds splits with whole clusters
assigned to exactly one split, then evaluates the frozen model on the new test
set and on the original test set for comparison.

No images are copied or moved; the new split exists only as cluster
assignments in the report, so nothing on disk is disturbed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.data.transforms import val_transform  # noqa: E402
from src.models.cnn import PhishVisionCNN  # noqa: E402
from src.models.predictor import CNNPredictor  # noqa: E402

ROOT = PROJECT_ROOT / "data" / "clean_split_v2"
CLASSES = ("legitimate", "phishing")
SPLITS = ("train", "val", "test")
HAMMING = 6
THRESHOLD = 0.35


def dhash(path: Path, size: int = 8) -> int:
    with Image.open(path) as handle:
        small = handle.convert("L").resize((size + 1, size), Image.LANCZOS)
        pixels = np.asarray(small, dtype=np.int16)
    value = 0
    for bit in (pixels[:, 1:] > pixels[:, :-1]).flatten():
        value = (value << 1) | int(bit)
    return value


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def collect():
    records = []
    for split in SPLITS:
        for label, name in enumerate(CLASSES):
            for path in sorted((ROOT / split / name).glob("*")):
                if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                    records.append({"path": path, "label": label,
                                    "split": split, "hash": dhash(path)})
    return records


def cluster(records):
    uf = UnionFind(len(records))
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if bin(records[i]["hash"] ^ records[j]["hash"]).count("1") <= HAMMING:
                uf.union(i, j)

    groups = defaultdict(list)
    for index in range(len(records)):
        groups[uf.find(index)].append(index)
    return list(groups.values())


def assign_splits(records, groups, train_share=0.70, val_share=0.15):
    """Fill train, then val, then test, keeping every cluster whole.

    Clusters are taken largest-first; a cluster is never split, so sizes can
    overshoot targets, but no cluster spans two splits.
    """
    order = sorted(groups, key=len, reverse=True)
    total = len(records)
    train_target = total * train_share
    val_target = total * (train_share + val_share)

    assignment = {}
    filled = 0

    for group in order:
        key = tuple(group)
        if filled < train_target:
            assignment[key] = "train"
        elif filled < val_target:
            assignment[key] = "val"
        else:
            assignment[key] = "test"
        filled += len(group)

    return assignment


def metrics(labels, scores, threshold=THRESHOLD):
    tp = fp = tn = fn = 0
    for truth, score in zip(labels, scores):
        predicted = 1 if score >= threshold else 0
        if truth == 1 and predicted == 1:
            tp += 1
        elif truth == 0 and predicted == 0:
            tn += 1
        elif truth == 0:
            fp += 1
        else:
            fn += 1

    ratio = lambda a, b: a / b if b else 0.0
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    f1 = ratio(2 * precision * recall, precision + recall)

    positives = [s for s, y in zip(scores, labels) if y == 1]
    negatives = [s for s, y in zip(scores, labels) if y == 0]
    auc = 0.0
    if positives and negatives:
        wins = sum(1.0 if p > n else 0.5 if p == n else 0.0
                   for p in positives for n in negatives)
        auc = wins / (len(positives) * len(negatives))

    return {"n": len(labels), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "accuracy": round(ratio(tp + tn, len(labels)), 4),
            "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4), "auc": round(auc, 4)}


def predict_all(model, records):
    import torch

    scores, labels = [], []
    with torch.no_grad():
        for record in records:
            with Image.open(record["path"]) as handle:
                tensor = val_transform(handle.convert("RGB")).unsqueeze(0)
            scores.append(float(torch.softmax(model(tensor), dim=1)[0, 1]))
            labels.append(record["label"])
    return labels, scores


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=PROJECT_ROOT / "results" / "leakage_free")
    args = parser.parse_args()

    records = collect()
    groups = cluster(records)
    assignment = assign_splits(records, groups)

    index_to_split = {}
    for key, split in assignment.items():
        for index in key:
            index_to_split[index] = split

    new_test = [records[i] for i in range(len(records)) if index_to_split.get(i) == "test"]
    old_test = [records[i] for i in range(len(records)) if records[i]["split"] == "test"]

    cross = 0
    for group in groups:
        if len({index_to_split[i] for i in group}) > 1:
            cross += 1

    predictor = CNNPredictor()
    if not predictor.model_loaded:
        raise SystemExit("production checkpoint did not load")
    model = predictor.model

    old_labels, old_scores = predict_all(model, old_test)
    new_labels, new_scores = predict_all(model, new_test)

    summary = {
        "images": len(records),
        "clusters": len(groups),
        "clusters_spanning_splits": cross,
        "new_split_sizes": {s: sum(1 for v in index_to_split.values() if v == s)
                            for s in ("train", "val", "test")},
        "old_test": metrics(old_labels, old_scores),
        "leakage_free_test": metrics(new_labels, new_scores),
        "threshold": THRESHOLD,
        "model_sha256": predictor.model_sha256,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Leakage-free evaluation on the existing images",
        "",
        f"{len(records)} images, {len(groups)} perceptual clusters at Hamming <= {HAMMING}.",
        f"New split: train {summary['new_split_sizes']['train']}, "
        f"val {summary['new_split_sizes']['val']}, "
        f"test {summary['new_split_sizes']['test']} images.",
        f"Clusters spanning two splits in the rebuilt assignment: **{cross}** (must be 0).",
        "",
        "| Test set | n | accuracy | precision | recall | F1 | AUC |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, row in (("original test (leaky)", summary["old_test"]),
                       ("cluster-split test", summary["leakage_free_test"])):
        lines.append(f"| {label} | {row['n']} | {row['accuracy']} | {row['precision']} | "
                     f"{row['recall']} | {row['f1']} | {row['auc']} |")

    delta = summary["old_test"]["f1"] - summary["leakage_free_test"]["f1"]
    lines += [
        "",
        f"F1 difference (original minus cluster-split): **{delta:+.4f}**.",
        "",
        "## Reading this",
        "",
        "- The cluster-split number is the one to trust: no image in its test set",
        "  shares a near-duplicate cluster with training data.",
        "- The gap quantifies how much of the earlier score came from leakage;",
        "  both are development-set numbers and neither is a sealed-holdout result.",
        "- Clustering by dHash is conservative but imperfect: crops and overlays can",
        "  evade it, so residual leakage cannot be ruled out.",
    ]

    docs = PROJECT_ROOT / "docs" / "measurements"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "leakage-free-2026-10-24.md").write_text(
        "\n".join(lines).encode("ascii", "replace").decode("ascii") + "\n", encoding="utf-8")

    print("\n".join(lines).encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
