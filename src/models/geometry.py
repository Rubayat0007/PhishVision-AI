"""Spatial geometry of the CNN backbone, independent of torch.

The backbone applies three 2x2 max-pooling stages, so the classifier sees
``128`` channels of ``IMAGE_SIZE / 8`` square. Keeping the arithmetic here
makes the coupling explicit and keeps it testable without torch.
"""

POOLING_FACTOR = 8
BACKBONE_CHANNELS = 128


def spatial_size(image_size: int) -> int:
    """Return the spatial extent reaching the classifier."""
    if not isinstance(image_size, int) or isinstance(image_size, bool):
        raise TypeError("image_size must be an integer")

    if image_size <= 0:
        raise ValueError("image_size must be greater than zero")

    if image_size % POOLING_FACTOR:
        raise ValueError(
            f"image_size must be a multiple of {POOLING_FACTOR}; "
            f"got {image_size}"
        )

    return image_size // POOLING_FACTOR


def flattened_feature_count(
    image_size: int,
    channels: int = BACKBONE_CHANNELS,
) -> int:
    """Return the flattened feature count for a given input size."""
    if channels <= 0:
        raise ValueError("channels must be greater than zero")

    side = spatial_size(image_size)

    return channels * side * side
