from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset


class PhishVisionDataset(Dataset):
    """
    Dataset for phishing and legitimate website screenshots.

    Expected directory structure:

    data/processed/
    ├── legitimate/
    │   ├── image1.jpg
    │   └── image2.jpg
    │
    └── phishing/
        ├── image1.jpg
        └── image2.jpg
    """

    CLASS_NAMES = ["legitimate", "phishing"]

    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform

        self.samples = []

        for label, class_name in enumerate(self.CLASS_NAMES):
            class_dir = self.root_dir / class_name

            if not class_dir.exists():
                continue

            for image_path in class_dir.rglob("*"):
                if image_path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    self.samples.append((image_path, label))

        if not self.samples:
            raise RuntimeError(
                f"No images found in: {self.root_dir}"
            )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        image_path, label = self.samples[index]

        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label