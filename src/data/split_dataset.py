from pathlib import Path
import random
import shutil


RANDOM_SEED = 42
TRAIN_RATIO = 0.8


def split_class(class_name, source_root, output_root):
    source_dir = Path(source_root) / class_name

    if not source_dir.exists():
        print(f"Skipping {class_name}: directory not found")
        return

    images = [
        path
        for path in source_dir.rglob("*")
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]

    random.shuffle(images)

    split_index = int(len(images) * TRAIN_RATIO)

    train_images = images[:split_index]
    val_images = images[split_index:]

    train_dir = Path(output_root) / "train" / class_name
    val_dir = Path(output_root) / "val" / class_name

    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    for image in train_images:
        shutil.copy2(image, train_dir / image.name)

    for image in val_images:
        shutil.copy2(image, val_dir / image.name)

    print(f"{class_name}:")
    print(f"  Total:      {len(images)}")
    print(f"  Training:   {len(train_images)}")
    print(f"  Validation: {len(val_images)}")


def main():
    random.seed(RANDOM_SEED)

    source_root = "data/processed"
    output_root = "data/split"

    print("=== Dataset Split ===")

    for class_name in ["legitimate", "phishing"]:
        split_class(
            class_name,
            source_root,
            output_root,
        )


if __name__ == "__main__":
    main()