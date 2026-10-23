"""Discovery of labelled image samples, independent of torch."""

from pathlib import Path

from src.data.image_utils import SUPPORTED_EXTENSIONS

CLASS_NAMES = ("legitimate", "phishing")


def discover_samples(
    root_dir,
    class_names=CLASS_NAMES,
    extensions=SUPPORTED_EXTENSIONS,
):
    """Return deterministic ``(path, label)`` pairs for a class-folder dataset.

    Each class folder is walked recursively, files are sorted by path, and
    classes are emitted in ``class_names`` order. The ordering is stable
    across filesystems, which makes splits and evaluation reproducible.
    """
    root = Path(root_dir)

    samples = []

    for label, class_name in enumerate(class_names):
        class_dir = root / class_name

        if not class_dir.is_dir():
            continue

        for path in sorted(
            candidate
            for candidate in class_dir.rglob("*")
            if candidate.is_file()
        ):
            if path.suffix.lower() in extensions:
                samples.append((path, label))

    if not samples:
        raise RuntimeError(f"No images found in: {root}")

    return samples
