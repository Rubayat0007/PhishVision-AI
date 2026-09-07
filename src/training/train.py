import torch
import torch.nn as nn
import torch.optim as optim

from src.models.cnn import PhishVisionCNN
from src.data.dataset import PhishVisionDataset
from src.data.transforms import train_transform, val_transform
from torch.utils.data import DataLoader


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        predictions = outputs.argmax(dim=1)

        total += labels.size(0)
        correct += (predictions == labels).sum().item()

    return running_loss / len(dataloader), 100.0 * correct / total


def validate(model, dataloader, criterion, device):
    model.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item()

            predictions = outputs.argmax(dim=1)

            total += labels.size(0)
            correct += (predictions == labels).sum().item()

    return running_loss / len(dataloader), 100.0 * correct / total


if __name__ == "__main__":

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Training device:", device)

    # Current dataset: phishing only
    dataset = PhishVisionDataset(
        root_dir="data/processed",
        transform=train_transform,
    )

    print("Dataset size:", len(dataset))

    dataloader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=True,
        num_workers=0,
    )

    print("Training batches:", len(dataloader))

    model = PhishVisionCNN(num_classes=2).to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=0.001,
    )

    print("Model created successfully")
    print("Starting training-loop test...")

    # Only test one batch for now.
    images, labels = next(iter(dataloader))

    images = images.to(device)
    labels = labels.to(device)

    outputs = model(images)

    loss = criterion(outputs, labels)

    print("Batch image shape:", images.shape)
    print("Batch label shape:", labels.shape)
    print("Model output shape:", outputs.shape)
    print("Test loss:", loss.item())

    print("Training pipeline test successful!")