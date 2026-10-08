import argparse
import hashlib
from pathlib import Path
import sys

from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.predictor import CNNPredictor


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

CLASS_NAMES = {
    "legitimate": 0,
    "phishing": 1,
}


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate CNNPredictor on a frozen dataset split."
    )

    parser.add_argument(
        "--split",
        required=True,
        choices=["val", "test"],
        help="Dataset split under data/clean_split_v2.",
    )

    parser.add_argument(
        "--model",
        required=True,
        help="Path to the model checkpoint.",
    )

    parser.add_argument(
        "--threshold",
        required=True,
        type=float,
        help="Phishing decision threshold in [0, 1].",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="CSV path for per-image probabilities.",
    )

    return parser.parse_args()


def collect_images(split_dir):
    samples = []

    for class_name, label in CLASS_NAMES.items():

        class_dir = split_dir / class_name

        if not class_dir.exists():
            raise FileNotFoundError(
                f"Class directory not found: {class_dir}"
            )

        for image_path in sorted(class_dir.iterdir()):

            if image_path.is_file() and (
                image_path.suffix.lower()
                in IMAGE_EXTENSIONS
            ):
                samples.append(
                    (
                        image_path,
                        label,
                        class_name,
                    )
                )

    return samples


def main():

    args = parse_args()

    model_path = Path(args.model)

    if not model_path.is_absolute():
        model_path = (
            PROJECT_ROOT / model_path
        )

    model_path = model_path.resolve()

    split_dir = (
        PROJECT_ROOT
        / "data"
        / "clean_split_v2"
        / args.split
    )

    output_path = Path(args.output)

    if not output_path.is_absolute():
        output_path = (
            PROJECT_ROOT / output_path
        )

    output_path = output_path.resolve()

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

    if not split_dir.exists():
        raise FileNotFoundError(
            f"Split not found: {split_dir}"
        )

    if not 0.0 <= args.threshold <= 1.0:
        raise ValueError(
            "threshold must be between 0.0 and 1.0."
        )

    samples = collect_images(split_dir)

    model_hash = sha256_file(model_path)

    predictor = CNNPredictor(
        model_path=model_path,
        threshold=args.threshold,
    )

    rows = []
    errors = []

    for image_path, true_label, true_class in samples:

        try:

            image = Image.open(
                image_path
            ).convert("RGB")

            result = predictor.predict(image)

            p_phish = result[
                "phishing_probability"
            ]

            predicted_label = (
                1
                if p_phish >= args.threshold
                else 0
            )

            predicted_class = (
                "phishing"
                if predicted_label == 1
                else "legitimate"
            )

            rows.append(
                {
                    "filename": str(
                        image_path.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                    "true_label": true_label,
                    "true_class": true_class,
                    "p_phish": p_phish,
                    "predicted_label": predicted_label,
                    "predicted_class": predicted_class,
                }
            )

        except Exception as error:

            errors.append(
                (
                    str(
                        image_path.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                    str(error),
                )
            )

    if not rows:
        raise RuntimeError(
            "No images were successfully evaluated."
        )

    y_true = [
        row["true_label"]
        for row in rows
    ]

    y_pred = [
        row["predicted_label"]
        for row in rows
    ]

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        file.write(
            "filename,true_label,true_class,"
            "p_phish,predicted_label,predicted_class\n"
        )

        for row in rows:

            file.write(
                f'{row["filename"]},'
                f'{row["true_label"]},'
                f'{row["true_class"]},'
                f'{row["p_phish"]:.10f},'
                f'{row["predicted_label"]},'
                f'{row["predicted_class"]}\n'
            )

    print()
    print("===== CNN PREDICTOR EVALUATION =====")
    print(f"Model:     {model_path}")
    print(f"SHA-256:   {model_hash}")
    print(f"Split:     {args.split}")
    print(f"Split dir: {split_dir}")
    print(f"Threshold: {args.threshold:.4f}")
    print(f"Images:    {len(rows)}")
    print(f"Errors:    {len(errors)}")
    print(f"Output:    {output_path}")

    print()
    print("===== METRICS =====")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    print()
    print("===== CONFUSION MATRIX =====")
    print("                 Predicted")
    print("              Legit  Phishing")
    print()
    print(
        f"Actual Legit     {cm[0][0]:5d}   {cm[0][1]:5d}"
    )
    print(
        f"Actual Phishing  {cm[1][0]:5d}   {cm[1][1]:5d}"
    )

    print()
    print("===== CLASSIFICATION REPORT =====")

    print(
        classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=[
                "legitimate",
                "phishing",
            ],
            zero_division=0,
        )
    )

    if errors:

        print()
        print("===== ERRORS =====")

        for filename, error in errors:
            print(
                f"{filename}: {error}"
            )


if __name__ == "__main__":
    main()
