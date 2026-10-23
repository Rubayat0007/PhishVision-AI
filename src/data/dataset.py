from pathlib import Path

from torch.utils.data import Dataset

from src.data.image_utils import SUPPORTED_EXTENSIONS, load_image
from src.data.samples import CLASS_NAMES, discover_samples


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

    Sample order is deterministic: classes are visited in
    ``class_names`` order and files are sorted by path.
    """

    CLASS_NAMES = list(CLASS_NAMES)

    IMAGE_EXTENSIONS = set(SUPPORTED_EXTENSIONS)

    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform

        self.samples = discover_samples(
            self.root_dir,
            tuple(self.CLASS_NAMES),
            self.IMAGE_EXTENSIONS,
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        image_path, label = self.samples[index]

        image = load_image(image_path)

        if self.transform:
            image = self.transform(image)

        return image, label
