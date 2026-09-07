from torch.utils.data import DataLoader, random_split

from src.data.dataset import PhishVisionDataset
from src.data.transforms import train_transform, val_transform


def create_dataloaders(
    data_dir,
    batch_size=32,
    train_ratio=0.8,
):
    # Full dataset
    full_dataset = PhishVisionDataset(
        data_dir,
        transform=train_transform,
    )

    train_size = int(len(full_dataset) * train_ratio)
    val_size = len(full_dataset) - train_size

    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
    )

    # Validation dataset should not use training augmentation
    val_dataset.dataset.transform = val_transform

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )

    return train_loader, val_loader