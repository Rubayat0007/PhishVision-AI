import torch
import torch.nn as nn
import torch.optim as optim

from src.data.dataloader import create_dataloaders
from src.models.cnn import PhishVisionCNN


DATA_DIR = "data/processed"
MODEL_PATH = "models/phishvision_cnn.pth"

BATCH_SIZE = 32
EPOCHS = 5
LEARNING_RATE = 0.001


def train():
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)

    train_loader, val_loader = create_dataloaders(
        DATA_DIR,
        batch_size=BATCH_SIZE,
    )

    model = PhishVisionCNN(num_classes=2)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    for epoch in range(EPOCHS):
        # --------------------
        # Training
        # --------------------
        model.train()

        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item()

            _, predicted = torch.max(outputs, 1)

            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_accuracy = 100 * correct / total

        # --------------------
        # Validation
        # --------------------
        model.eval()

        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)

                outputs = model(images)

                _, predicted = torch.max(outputs, 1)

                val_total += labels.size(0)
                val_correct += (
                    predicted == labels
                ).sum().item()

        val_accuracy = 100 * val_correct / val_total

        print(
            f"Epoch [{epoch + 1}/{EPOCHS}] "
            f"Loss: {running_loss / len(train_loader):.4f} "
            f"Train Acc: {train_accuracy:.2f}% "
            f"Val Acc: {val_accuracy:.2f}%"
        )

    torch.save(model.state_dict(), MODEL_PATH)

    print()
    print("Model saved to:", MODEL_PATH)


if __name__ == "__main__":
    train()