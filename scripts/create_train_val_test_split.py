from pathlib import Path
import random
import shutil


SOURCE_DIR = Path("data/clean")
OUTPUT_DIR = Path("data/clean_split_v2")

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SEED = 42


def split_class(class_name):

    source = SOURCE_DIR / class_name

    train_dir = OUTPUT_DIR / "train" / class_name
    val_dir = OUTPUT_DIR / "val" / class_name
    test_dir = OUTPUT_DIR / "test" / class_name

    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(source.glob("*.jpg"))

    random.seed(SEED)
    random.shuffle(files)

    total = len(files)

    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    train_files = files[:train_end]
    val_files = files[train_end:val_end]
    test_files = files[val_end:]

    for file in train_files:
        shutil.copy2(
            file,
            train_dir / file.name,
        )

    for file in val_files:
        shutil.copy2(
            file,
            val_dir / file.name,
        )

    for file in test_files:
        shutil.copy2(
            file,
            test_dir / file.name,
        )

    return (
        len(train_files),
        len(val_files),
        len(test_files),
    )


def main():

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    print("=" * 50)
    print("Creating train / validation / test split")
    print("=" * 50)

    phishing_train, phishing_val, phishing_test = (
        split_class("phishing")
    )

    legitimate_train, legitimate_val, legitimate_test = (
        split_class("legitimate")
    )

    print()
    print("Phishing:")
    print("  Training:   ", phishing_train)
    print("  Validation: ", phishing_val)
    print("  Test:       ", phishing_test)

    print()
    print("Legitimate:")
    print("  Training:   ", legitimate_train)
    print("  Validation: ", legitimate_val)
    print("  Test:       ", legitimate_test)

    print()
    print("Total:")
    print(
        "  Training:   ",
        phishing_train + legitimate_train,
    )
    print(
        "  Validation: ",
        phishing_val + legitimate_val,
    )
    print(
        "  Test:       ",
        phishing_test + legitimate_test,
    )

    print()
    print("Split created successfully.")


if __name__ == "__main__":
    main()