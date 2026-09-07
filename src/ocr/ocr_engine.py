import easyocr
import numpy as np
from PIL import Image


class OCREngine:
    def __init__(self, languages=None):
        if languages is None:
            languages = ["en"]

        self.reader = easyocr.Reader(
            languages,
            gpu=False,
        )

    def extract_text(self, image):
        """
        Extract text from a PIL image.

        Returns:
            str: Detected text joined into a single string.
        """

        if isinstance(image, Image.Image):
            image = np.array(image)

        results = self.reader.readtext(image)

        detected_text = []

        for _, text, confidence in results:
            if confidence >= 0.4:
                detected_text.append(text)

        return " ".join(detected_text)