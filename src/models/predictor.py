import torch
from PIL import Image

from src.models.cnn import PhishVisionCNN
from src.data.transforms import val_transform


class CNNPredictor:

    def __init__(self, model_path=None):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model = PhishVisionCNN(num_classes=2)
        self.model.to(self.device)

        self.model_loaded = False

        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path):
        checkpoint = torch.load(
            model_path,
            map_location=self.device,
            weights_only=True,
        )

        self.model.load_state_dict(checkpoint)

        self.model.eval()
        self.model_loaded = True

    def predict(self, image):
        if not self.model_loaded:
            raise RuntimeError(
                "CNN model has not been trained or loaded yet."
            )

        if not isinstance(image, Image.Image):
            raise TypeError("Expected a PIL Image.")

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

            prediction = probabilities.argmax(
                dim=1
            ).item()

        class_names = [
            "legitimate",
            "phishing",
        ]

        return {
            "prediction": class_names[prediction],
            "phishing_probability": float(
                probabilities[0][1]
            ),
            "legitimate_probability": float(
                probabilities[0][0]
            ),
        }