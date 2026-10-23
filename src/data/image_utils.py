from pathlib import Path

from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_image(image_path: str | Path) -> Image.Image:
    """
    Load an image from disk and return it as an RGB PIL Image.

    The file handle is closed before returning, and decode failures are
    reported with the offending path so a corrupt sample is diagnosable.
    """
    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {image_path.suffix}"
        )

    try:
        with Image.open(image_path) as image:
            return image.convert("RGB")
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"Could not decode image: {image_path}"
        ) from exc


def get_image_size(image: Image.Image) -> tuple[int, int]:
    """
    Return image dimensions as (width, height).
    """
    return image.size
