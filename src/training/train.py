import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader

from src.models.cnn import PhishVisionCNN
from src.data.dataset import PhishVisionDataset
from src.data.transforms import train_transform, val_transform


BATCH_SIZE = 32
LEARNING_RATE = 0.001
NUM_EPOCHS = 10

TRAIN_DIR = "data/split/train"
VAL_DIR = "data/split/val"

MODEL_PATH = "models/phishvision_cnn.pth"


def train_one_epoch(
    model,
    dataloader,
    criterion,
    optimizer,
    device,
):
    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(
            outputs,
            labels,
        )

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        predictions = outputs.argmax(dim=1)

        total += labels.size(0)
        correct += (
            predictions == labels
        ).sum().item()

    epoch_loss = running_loss / len(dataloader)
    epoch_accuracy = 100.0 * correct / total

    return epoch_loss, epoch_accuracy


def validate(
    model,
    dataloader,
    criterion,
    device,
):
    model.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():

        for images, labels in dataloader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(
                outputs,
                labels,
            )

            running_loss += loss.item()

            predictions = outputs.argmax(dim=1)

            total += labels.size(0)
            correct += (
                predictions == labels
            ).sum().item()

    val_loss = running_loss / len(dataloader)
    val_accuracy = 100.0 * correct / total

    return val_loss, val_accuracy


def main():

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Training device:", device)

    # -------------------------
    # Load datasets
    # -------------------------

    train_dataset = PhishVisionDataset(
        root_dir=TRAIN_DIR,
        transform=train_transform,
    )

    val_dataset = PhishVisionDataset(
        root_dir=VAL_DIR,
        transform=val_transform,
    )

    print(
        "Training dataset size:",
        len(train_dataset),
    )

    print(
        "Validation dataset size:",
        len(val_dataset),
    )

    # -------------------------
    # Check both classes
    # -------------------------

    train_labels = [
        label
        for _, label in train_dataset.samples
    ]

    val_labels = [
        label
        for _, label in val_dataset.samples
    ]

    train_classes = set(train_labels)
    val_classes = set(val_labels)

    if train_classes != {0, 1}:
        raise RuntimeError(
            "Training dataset must contain "
            "both legitimate and phishing classes."
        )

    if val_classes != {0, 1}:
        raise RuntimeError(
            "Validation dataset must contain "
            "both legitimate and phishing classes."
        )

    print("Both classes detected successfully.")

    # -------------------------
    # DataLoaders
    # -------------------------

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
    )

    print(
        "Training batches:",
        len(train_loader),
    )

    print(
        "Validation batches:",
        len(val_loader),
    )

    # -------------------------
    # Model
    # -------------------------

    model = PhishVisionCNN(
        num_classes=2
    ).to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    print("Model created successfully")
    print("Loss function:", criterion)
    print("Optimizer: Adam")

    # -------------------------
    # Training
    # -------------------------

    best_val_accuracy = 0.0

    for epoch in range(NUM_EPOCHS):

        train_loss, train_accuracy = (
            train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device,
            )
        )

        val_loss, val_accuracy = validate(
            model,
            val_loader,
            criterion,
            device,
        )

        print(
            f"Epoch [{epoch + 1}/{NUM_EPOCHS}] "
            f"Train Loss: {train_loss:.4f} "
            f"Train Acc: {train_accuracy:.2f}% "
            f"Val Loss: {val_loss:.4f} "
            f"Val Acc: {val_accuracy:.2f}%"
        )

        # Save best model
        if val_accuracy > best_val_accuracy:

            best_val_accuracy = val_accuracy

            torch.save(
                model.state_dict(),
                MODEL_PATH,
            )

            print(
                f"Best model saved: "
                f"{MODEL_PATH}"
            )

    print()
    print("Training complete.")
    print(
        f"Best validation accuracy: "
        f"{best_val_accuracy:.2f}%"
    )


if __name__ == "__main__":
    main()