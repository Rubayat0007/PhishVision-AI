from pathlib import Path

from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_image(image_path: str | Path) -> Image.Image:
    """
    Load an image from disk and return it as a PIL Image.
    """
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {image_path.suffix}"
        )

    return Image.open(image_path).convert("RGB")


def get_image_size(image: Image.Image) -> tuple[int, int]:
    """
    Return image dimensions as (width, height).
    """
    return image.size