import sys
from io import BytesIO
from pathlib import Path

import torch
from PIL import Image

from src.models.cnn import PhishVisionCNN
from src.models.integrity import (
    BYPASS_ENV_VAR,
    build_provenance,
    ModelIntegrityError,
    is_verification_bypassed,
    read_verified_checkpoint,
    verify_model_file,
)
from src.data.transforms import val_transform
from src.config import ACTIVE_MODEL_PATH, CNN_THRESHOLD


class CNNPredictor:

    def __init__(
        self,
        model_path=None,
        threshold=CNN_THRESHOLD,
    ):

        threshold = float(threshold)

        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "threshold must be between 0.0 and 1.0."
            )

        self.threshold = threshold

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model = PhishVisionCNN(
            num_classes=2
        ).to(self.device)

        self.model_loaded = False
        self.model_sha256 = None

        # Default to the centralized active model.
        if model_path is None:
            model_path = ACTIVE_MODEL_PATH

        model_path = Path(model_path)

        if model_path.exists():
            try:
                self.load_model(model_path)
            except ModelIntegrityError as exc:
                self.model_loaded = False
                print(f"CNN model rejected: {exc}", file=sys.stderr)
            except Exception:
                self.model_loaded = False
                print(
                    "CNN model unavailable: model could not be loaded safely.",
                    file=sys.stderr,
                )
        else:
            print(
                "CNN model unavailable: configured model file was not found.",
                file=sys.stderr,
            )

    def load_model(self, model_path):
        model_path = Path(model_path)

        allow_unverified = is_verification_bypassed()

        checkpoint_bytes, self.model_sha256 = read_verified_checkpoint(
            model_path,
            allow_unverified=allow_unverified,
        )

        if allow_unverified:
            print(
                "WARNING: model integrity verification bypassed via "
                f"{BYPASS_ENV_VAR}; loaded SHA-256 {self.model_sha256}",
                file=sys.stderr,
            )

        try:
            checkpoint = torch.load(
                BytesIO(checkpoint_bytes),
                map_location=self.device,
                weights_only=True,
            )

            self.model.load_state_dict(checkpoint)
            self.model.eval()
            self.model_loaded = True

            print("CNN model loaded successfully.")

        except Exception as exc:
            self.model_loaded = False
            raise RuntimeError(
                "Failed to load CNN model safely."
            ) from exc

    def provenance(self) -> dict:
        """Return the model identity recorded with analysis results."""
        return build_provenance(
            loaded=self.model_loaded,
            sha256=self.model_sha256,
            threshold=self.threshold,
        )

    def predict(self, image):

        if not self.model_loaded:
            raise RuntimeError(
                "CNN model has not been trained or loaded yet."
            )

        if not isinstance(image, Image.Image):
            raise TypeError(
                "Expected a PIL Image."
            )

        image = image.convert("RGB")

        tensor = val_transform(image)
        tensor = tensor.unsqueeze(0)
        tensor = tensor.to(self.device)

        with torch.no_grad():

            outputs = self.model(tensor)

            probabilities = torch.softmax(
                outputs,
                dim=1,
            )

            phishing_probability = (
                probabilities[0, 1].item()
            )

            legitimate_probability = (
                probabilities[0, 0].item()
            )

        prediction = (
            "phishing"
            if phishing_probability >= self.threshold
            else "legitimate"
        )

        return {
            "prediction": prediction,
            "phishing_probability": phishing_probability,
            "legitimate_probability": legitimate_probability,
            "threshold": self.threshold,
            "model_loaded": True,
        }
