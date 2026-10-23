"""Loader mechanics tests using synthetic images.

Content is irrelevant here: these assertions cover the split, transform
isolation, determinism, and batch shape — code we own — not detector
quality. Real-data acceptance lives in docs/dataset-acceptance.md.
"""

import pytest

pytest.importorskip("torch")
pytest.importorskip("torchvision")

from PIL import Image  # noqa: E402
import torch  # noqa: E402

pytestmark = pytest.mark.slow

from src.data.dataloader import create_dataloaders  # noqa: E402
from src.data.transforms import train_transform, val_transform  # noqa: E402

CLASSES = ("legitimate", "phishing")


@pytest.fixture
def dataset_root(tmp_path):
    root = tmp_path / "dataset"

    for label, name in enumerate(CLASSES):
        folder = root / name
        folder.mkdir(parents=True)

        for index in range(10):
            image = Image.new("RGB", (24, 24), (label * 200, index * 20, 40))
            image.save(folder / f"{name}_{index:02d}.png")

    return root


@pytest.fixture
def loaders(dataset_root):
    return create_dataloaders(dataset_root, batch_size=4, train_ratio=0.5, seed=42)


def indices(loader):
    return list(loader.dataset.indices)


def test_split_partitions_the_dataset(loaders):
    train, val = loaders
    train_indices, val_indices = indices(train), indices(val)

    assert len(train_indices) == 10
    assert len(val_indices) == 10
    assert not set(train_indices) & set(val_indices)
    assert sorted(train_indices + val_indices) == list(range(20))


def test_split_is_reproducible_for_a_seed(dataset_root):
    first = create_dataloaders(dataset_root, batch_size=4, train_ratio=0.5, seed=7)
    second = create_dataloaders(dataset_root, batch_size=4, train_ratio=0.5, seed=7)

    assert indices(first[0]) == indices(second[0])
    assert indices(first[1]) == indices(second[1])


def test_different_seeds_produce_different_splits(dataset_root):
    first = create_dataloaders(dataset_root, batch_size=4, train_ratio=0.5, seed=1)
    second = create_dataloaders(dataset_root, batch_size=4, train_ratio=0.5, seed=2)

    assert indices(first[0]) != indices(second[0])


def test_subset_transforms_are_isolated(loaders):
    train, val = loaders

    assert train.dataset.dataset.transform is train_transform
    assert val.dataset.dataset.transform is val_transform


def test_batches_have_expected_shape_and_labels(loaders):
    train, _ = loaders
    images, labels = next(iter(train))

    assert images.shape == (4, 3, 224, 224)
    assert images.dtype is torch.float32
    assert set(labels.tolist()) <= {0, 1}


@pytest.mark.parametrize("ratio", [0.0, 1.0, -0.5, 1.5])
def test_invalid_train_ratio_is_rejected(dataset_root, ratio):
    with pytest.raises(ValueError):
        create_dataloaders(dataset_root, train_ratio=ratio)
