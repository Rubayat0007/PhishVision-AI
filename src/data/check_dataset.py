from pathlib import Path


DATA_DIR = Path("data/processed")

CLASSES = {
    "legitimate": 0,
    "phishing": 1,
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def count_images(folder):
    if not folder.exists():
        return 0

    return sum(
        1
        for path in folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def main():
    counts = {}

    for class_name in CLASSES:
        folder = DATA_DIR / class_name
        counts[class_name] = count_images(folder)

    legitimate = counts["legitimate"]
    phishing = counts["phishing"]
    total = legitimate + phishing

    print("=== PhishVision AI Dataset ===")
    print(f"Legitimate images: {legitimate}")
    print(f"Phishing images:   {phishing}")
    print(f"Total images:      {total}")

    if legitimate == 0 or phishing == 0:
        print()
        print("WARNING: Both classes are required for binary training.")
        return

    print()
    print("Dataset is ready for binary classification.")

    if legitimate == phishing:
        print("Class balance: PERFECT")
    else:
        print("Class balance: IMBALANCED")


if __name__ == "__main__":
    main()