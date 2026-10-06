from pathlib import Path

import torch
from PIL import Image

from src.models.cnn import PhishVisionCNN
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

        # Default to the centralized active model.
        if model_path is None:
            model_path = ACTIVE_MODEL_PATH

        model_path = Path(model_path)

        if model_path.exists():
            try:
                self.load_model(model_path)
            except Exception as exc:
                self.model_loaded = False
                print("CNN model unavailable: model could not be loaded safely.")
        else:
            print(
                "CNN model unavailable: configured model file was not found."
            )

    def load_model(self, model_path):
        model_path = Path(model_path)

        try:
            checkpoint = torch.load(
                model_path,
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
