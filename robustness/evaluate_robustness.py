import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import csv

import numpy as np
import torch
from PIL import Image

from src.config import IMAGE_SIZE
from src.models.cnn import PhishVisionCNN
from robustness.attacks.fgsm import fgsm_attack
from robustness.attacks.pgd import pgd_attack


MODEL_PATH = PROJECT_ROOT / "models" / "phishvision_cnn.pth"
VAL_DIR = PROJECT_ROOT / "data" / "clean_split" / "val"
RESULTS_DIR = PROJECT_ROOT / "results"

EPSILONS = [0.005, 0.01, 0.02, 0.04]
PGD_STEPS = 10

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def load_image(path):
    image = Image.open(path).convert("RGB")
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))

    array = np.asarray(image).copy()

    tensor = torch.from_numpy(array).float() / 255.0
    tensor = tensor.permute(2, 0, 1)

    return tensor


def normalize(images):
    mean = torch.tensor(
        [0.485, 0.456, 0.406],
        device=images.device,
    ).view(1, 3, 1, 1)

    std = torch.tensor(
        [0.229, 0.224, 0.225],
        device=images.device,
    ).view(1, 3, 1, 1)

    return (images - mean) / std


def predict(model, images):
    normalized = normalize(images)

    with torch.no_grad():
        outputs = model(normalized)
        probabilities = torch.softmax(outputs, dim=1)

    prediction = torch.argmax(
        probabilities,
        dim=1,
    )

    phishing_probability = probabilities[:, 1]

    return (
        prediction.item(),
        phishing_probability.item(),
    )


def load_model():
    model = PhishVisionCNN(num_classes=2)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
    )

    if (
        isinstance(checkpoint, dict)
        and "model_state_dict" in checkpoint
    ):
        model.load_state_dict(
            checkpoint["model_state_dict"]
        )
    else:
        model.load_state_dict(checkpoint)

    model.to(DEVICE)
    model.eval()

    return model


def get_eligible_samples(model):
    phishing_dir = VAL_DIR / "phishing"

    paths = sorted(
        path
        for path in phishing_dir.iterdir()
        if path.suffix.lower()
        in {".jpg", ".jpeg", ".png"}
    )

    eligible = []

    for path in paths:
        image = (
            load_image(path)
            .unsqueeze(0)
            .to(DEVICE)
        )

        prediction, probability = predict(
            model,
            image,
        )

        if prediction == 1:
            eligible.append(
                {
                    "path": path,
                    "image": image,
                    "clean_probability": probability,
                }
            )

    return eligible


def evaluate_attack(
    model,
    sample,
    attack_name,
    epsilon,
):
    image = sample["image"]

    label = torch.ones(
        1,
        dtype=torch.long,
        device=DEVICE,
    )

    if attack_name == "FGSM":
        adversarial_image = fgsm_attack(
            model=model,
            images=image,
            labels=label,
            epsilon=epsilon,
        )

    elif attack_name == "PGD":
        alpha = epsilon / PGD_STEPS

        adversarial_image = pgd_attack(
            model=model,
            images=image,
            labels=label,
            epsilon=epsilon,
            alpha=alpha,
            steps=PGD_STEPS,
        )

    else:
        raise ValueError(
            f"Unknown attack: {attack_name}"
        )

    prediction, probability = predict(
        model,
        adversarial_image,
    )

    perturbation = (
        adversarial_image - image
    ).abs()

    return {
        "attack": attack_name,
        "epsilon": epsilon,
        "image": sample["path"].name,
        "clean_phishing_probability":
            sample["clean_probability"],
        "adversarial_phishing_probability":
            probability,
        "adversarial_prediction":
            prediction,
        "successful_flip":
            int(prediction == 0),
        "max_perturbation":
            perturbation.max().item(),
    }


def main():
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Evaluation device: {DEVICE}")
    print(f"Model: {MODEL_PATH}")

    model = load_model()

    samples = get_eligible_samples(model)

    print(
        f"Eligible correctly classified "
        f"phishing images: {len(samples)}"
    )

    if not samples:
        print("No eligible samples found.")
        return

    rows = []

    for attack_name in ["FGSM", "PGD"]:
        for epsilon in EPSILONS:

            print(
                f"Running {attack_name}, "
                f"epsilon={epsilon:.3f}..."
            )

            for sample in samples:
                result = evaluate_attack(
                    model,
                    sample,
                    attack_name,
                    epsilon,
                )

                rows.append(result)

    output_path = (
        RESULTS_DIR / "adversarial_robustness.csv"
    )

    fieldnames = [
        "attack",
        "epsilon",
        "image",
        "clean_phishing_probability",
        "adversarial_phishing_probability",
        "adversarial_prediction",
        "successful_flip",
        "max_perturbation",
    ]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("===== ROBUSTNESS SUMMARY =====")

    for attack_name in ["FGSM", "PGD"]:
        for epsilon in EPSILONS:

            matching = [
                row
                for row in rows
                if row["attack"] == attack_name
                and row["epsilon"] == epsilon
            ]

            successful = sum(
                row["successful_flip"]
                for row in matching
            )

            total = len(matching)

            asr = successful / total

            avg_probability = sum(
                row[
                    "adversarial_phishing_probability"
                ]
                for row in matching
            ) / total

            print(
                f"{attack_name:4s} | "
                f"epsilon={epsilon:.3f} | "
                f"flips={successful}/{total} | "
                f"ASR={asr:.4f} | "
                f"avg phishing probability="
                f"{avg_probability:.4f}"
            )

    print()
    print(f"Saved results to: {output_path}")


if __name__ == "__main__":
    main()