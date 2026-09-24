import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
from PIL import Image

from src.config import IMAGE_SIZE
from src.models.cnn import PhishVisionCNN
from robustness.attacks.pgd import pgd_attack


MODEL_PATH = PROJECT_ROOT / "models" / "phishvision_cnn.pth"
VAL_DIR = PROJECT_ROOT / "data" / "clean_split" / "val"

# Same epsilon values used in the FGSM experiment.
EPSILONS = [0.005, 0.01, 0.02, 0.04]

# PGD iterations and step size.
STEPS = 10

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


def load_image(path):
    """Load an RGB image as an unnormalized [0, 1] tensor."""
    image = Image.open(path).convert("RGB")
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))

    array = np.asarray(image).copy()

    tensor = torch.from_numpy(array).float() / 255.0
    tensor = tensor.permute(2, 0, 1)

    return tensor


def normalize(images):
    """Apply PhishVision's image normalization."""
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
    """Return prediction and phishing probability."""
    normalized = normalize(images)

    with torch.no_grad():
        outputs = model(normalized)
        probabilities = torch.softmax(outputs, dim=1)

    prediction = torch.argmax(
        probabilities,
        dim=1,
    )

    phishing_probability = probabilities[:, 1]

    return prediction, phishing_probability


def collect_phishing_images():
    phishing_dir = VAL_DIR / "phishing"

    return sorted(
        path
        for path in phishing_dir.iterdir()
        if path.suffix.lower()
        in {".jpg", ".jpeg", ".png"}
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


def main():
    print(f"Evaluation device: {DEVICE}")
    print(f"Model: {MODEL_PATH}")
    print(
        f"Validation phishing directory: "
        f"{VAL_DIR / 'phishing'}"
    )

    model = load_model()

    image_paths = collect_phishing_images()

    print(
        f"Phishing validation images: "
        f"{len(image_paths)}"
    )

    phishing_label = torch.ones(
        1,
        dtype=torch.long,
        device=DEVICE,
    )

    # Only attack phishing images that the clean model
    # already classifies correctly.
    eligible_samples = []

    for image_path in image_paths:
        image = (
            load_image(image_path)
            .unsqueeze(0)
            .to(DEVICE)
        )

        clean_prediction, clean_probability = predict(
            model,
            image,
        )

        if clean_prediction.item() == 1:
            eligible_samples.append(
                {
                    "path": image_path,
                    "image": image,
                    "clean_probability":
                        clean_probability.item(),
                }
            )

    print(
        "Correctly classified phishing images: "
        f"{len(eligible_samples)} / "
        f"{len(image_paths)}"
    )

    if not eligible_samples:
        print(
            "No correctly classified phishing "
            "images available."
        )
        return

    print()
    print("===== PGD ROBUSTNESS EVALUATION =====")
    print(f"PGD steps: {STEPS}")

    for epsilon in EPSILONS:

        # Use epsilon / steps as a conservative PGD step size.
        alpha = epsilon / STEPS

        successful_attacks = 0

        clean_probabilities = []
        adversarial_probabilities = []
        perturbation_values = []

        for sample in eligible_samples:
            image = sample["image"]

            adversarial_image = pgd_attack(
                model=model,
                images=image,
                labels=phishing_label,
                epsilon=epsilon,
                alpha=alpha,
                steps=STEPS,
            )

            adversarial_prediction, adversarial_probability = (
                predict(
                    model,
                    adversarial_image,
                )
            )

            clean_probabilities.append(
                sample["clean_probability"]
            )

            adversarial_probabilities.append(
                adversarial_probability.item()
            )

            perturbation = (
                adversarial_image - image
            ).abs()

            perturbation_values.append(
                perturbation.max().item()
            )

            # Successful attack:
            # phishing -> legitimate.
            if adversarial_prediction.item() == 0:
                successful_attacks += 1

        total = len(eligible_samples)

        attack_success_rate = (
            successful_attacks / total
        )

        adversarial_recall = (
            (total - successful_attacks) / total
        )

        avg_clean_probability = (
            sum(clean_probabilities)
            / len(clean_probabilities)
        )

        avg_adversarial_probability = (
            sum(adversarial_probabilities)
            / len(adversarial_probabilities)
        )

        max_perturbation = max(
            perturbation_values
        )

        print()
        print(f"Epsilon: {epsilon:.3f}")
        print(f"PGD step size: {alpha:.6f}")
        print(f"PGD steps: {STEPS}")
        print(
            "Successful phishing -> legitimate flips: "
            f"{successful_attacks}/{total}"
        )
        print(
            f"Attack Success Rate: "
            f"{attack_success_rate:.4f}"
        )
        print(
            f"Adversarial phishing recall: "
            f"{adversarial_recall:.4f}"
        )
        print(
            "Average phishing probability "
            f"(clean): {avg_clean_probability:.4f}"
        )
        print(
            "Average phishing probability "
            f"(adversarial): "
            f"{avg_adversarial_probability:.4f}"
        )
        print(
            "Maximum observed perturbation: "
            f"{max_perturbation:.6f}"
        )


if __name__ == "__main__":
    main()