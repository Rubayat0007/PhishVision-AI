import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path

import torch
from PIL import Image
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from src.config import IMAGE_SIZE
from src.models.cnn import PhishVisionCNN
from robustness.attacks.fgsm import fgsm_attack


MODEL_PATH = PROJECT_ROOT / "models" / "phishvision_cnn.pth"
VAL_DIR = PROJECT_ROOT / "data" / "clean_split" / "val"

# FGSM perturbation strengths in [0, 1] image space.
EPSILONS = [0.0, 0.005, 0.01, 0.02, 0.04]

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_image(path):
    """Load an RGB image and convert it to an unnormalized tensor."""
    image = Image.open(path).convert("RGB")
    image = image.resize((IMAGE_SIZE, IMAGE_SIZE))

    tensor = torch.from_numpy(
        __import__("numpy").array(image)
    ).float() / 255.0

    tensor = tensor.permute(2, 0, 1)

    return tensor


def normalize(images):
    """Apply the same normalization used by the PhishVision model."""
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
    """Return predicted class and phishing probability."""
    normalized = normalize(images)

    with torch.no_grad():
        outputs = model(normalized)
        probabilities = torch.softmax(outputs, dim=1)

    predictions = torch.argmax(probabilities, dim=1)

    phishing_probabilities = probabilities[:, 1]

    return predictions, phishing_probabilities


def collect_phishing_images():
    """Collect validation images whose ground-truth class is phishing."""
    phishing_dir = VAL_DIR / "phishing"

    image_paths = sorted(
        path
        for path in phishing_dir.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    return image_paths


def main():
    print(f"Evaluation device: {DEVICE}")
    print(f"Model: {MODEL_PATH}")
    print(f"Validation phishing directory: {VAL_DIR / 'phishing'}")

    model = PhishVisionCNN(num_classes=2)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
    )

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.to(DEVICE)
    model.eval()

    image_paths = collect_phishing_images()

    print(f"Phishing validation images: {len(image_paths)}")

    # Ground-truth phishing label.
    labels = torch.ones(1, dtype=torch.long, device=DEVICE)

    # First identify images correctly classified as phishing on clean inputs.
    eligible_samples = []

    for image_path in image_paths:
        image = load_image(image_path).unsqueeze(0).to(DEVICE)

        clean_prediction, clean_probability = predict(
            model,
            image,
        )

        if clean_prediction.item() == 1:
            eligible_samples.append(
                {
                    "path": image_path,
                    "image": image,
                    "clean_probability": clean_probability.item(),
                }
            )

    print(
        f"Correctly classified phishing images: "
        f"{len(eligible_samples)} / {len(image_paths)}"
    )

    if not eligible_samples:
        print("No correctly classified phishing images available.")
        return

    print()
    print("===== FGSM ROBUSTNESS EVALUATION =====")

    for epsilon in EPSILONS:
        clean_predictions = []
        adversarial_predictions = []
        clean_probabilities = []
        adversarial_probabilities = []

        successful_attacks = 0
        total_eligible = len(eligible_samples)
        perturbation_values = []

        for sample in eligible_samples:
            image = sample["image"]
            clean_probability = sample["clean_probability"]

            # epsilon=0 gives the clean reference.
            if epsilon == 0.0:
                adversarial_image = image.clone()
            else:
                adversarial_image = fgsm_attack(
                    model=model,
                    images=image,
                    labels=labels,
                    epsilon=epsilon,
                )

            adversarial_prediction, adversarial_probability = predict(
                model,
                adversarial_image,
            )

            clean_predictions.append(1)
            adversarial_predictions.append(
                adversarial_prediction.item()
            )

            clean_probabilities.append(clean_probability)
            adversarial_probabilities.append(
                adversarial_probability.item()
            )

            perturbation = (
                adversarial_image - image
            ).abs()

            perturbation_values.append(
                perturbation.max().item()
            )

            # Successful targeted flip:
            # correctly classified phishing -> legitimate.
            if adversarial_prediction.item() == 0:
                successful_attacks += 1

        accuracy = accuracy_score(
            [1] * total_eligible,
            adversarial_predictions,
        )

        precision = precision_score(
            [1] * total_eligible,
            adversarial_predictions,
            zero_division=0,
        )

        recall = recall_score(
            [1] * total_eligible,
            adversarial_predictions,
            zero_division=0,
        )

        f1 = f1_score(
            [1] * total_eligible,
            adversarial_predictions,
            zero_division=0,
        )

        attack_success_rate = (
            successful_attacks / total_eligible
        )

        avg_clean_probability = sum(clean_probabilities) / len(
            clean_probabilities
        )

        avg_adversarial_probability = (
            sum(adversarial_probabilities)
            / len(adversarial_probabilities)
        )

        max_perturbation = max(perturbation_values)

        print()
        print(f"Epsilon: {epsilon:.3f}")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-score: {f1:.4f}")
        print(
            f"Successful phishing -> legitimate flips: "
            f"{successful_attacks}/{total_eligible}"
        )
        print(
            f"Attack Success Rate: "
            f"{attack_success_rate:.4f}"
        )
        print(
            f"Average phishing probability "
            f"(clean): {avg_clean_probability:.4f}"
        )
        print(
            f"Average phishing probability "
            f"(adversarial): {avg_adversarial_probability:.4f}"
        )
        print(
            f"Maximum observed perturbation: "
            f"{max_perturbation:.6f}"
        )


if __name__ == "__main__":
    main()