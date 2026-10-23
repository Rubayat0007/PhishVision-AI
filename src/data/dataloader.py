import torch
from torch.utils.data import DataLoader, Subset

from src.data.dataset import PhishVisionDataset
from src.data.transforms import train_transform, val_transform


def create_dataloaders(
    data_dir,
    batch_size=32,
    train_ratio=0.8,
    seed=42,
):
    """Split a class-folder dataset into deterministic train/validation loaders.

    The split is seeded, and the two subsets use separate dataset instances
    so the training transform (augmentation) is never replaced by the
    validation transform.
    """
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio must be between 0 and 1")

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    total = len(PhishVisionDataset(data_dir))

    train_size = int(total * train_ratio)

    if train_size == 0 or train_size == total:
        raise ValueError(
            "train_ratio produces an empty train or validation split"
        )

    generator = torch.Generator().manual_seed(seed)
    order = torch.randperm(total, generator=generator).tolist()

    train_indices = order[:train_size]
    val_indices = order[train_size:]

    train_dataset = Subset(
        PhishVisionDataset(data_dir, transform=train_transform),
        train_indices,
    )
    val_dataset = Subset(
        PhishVisionDataset(data_dir, transform=val_transform),
        val_indices,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        generator=torch.Generator().manual_seed(seed),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )

    return train_loader, val_loader
