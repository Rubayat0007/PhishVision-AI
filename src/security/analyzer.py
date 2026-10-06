from PIL import Image

from src.config import (
    ACTIVE_MODEL_PATH,
    CNN_THRESHOLD,
    MAX_IMAGE_HEIGHT,
    MAX_IMAGE_PIXELS,
    MAX_IMAGE_WIDTH,
)
from src.models.predictor import CNNPredictor
from src.ocr.ocr_engine import OCREngine
from src.security.text_analyzer import detect_suspicious_text
from src.security.url_analyzer import analyze_url
from src.security.risk_engine import calculate_risk
from src.security.security_assessment import build_security_assessment


class PhishVisionAnalyzer:
    def __init__(self):
        self.ocr = OCREngine()
        self.cnn = CNNPredictor(
            model_path=ACTIVE_MODEL_PATH,
            threshold=CNN_THRESHOLD,
        )

    @staticmethod
    def _validate_image(image):
        if not isinstance(image, Image.Image):
            raise TypeError("Input image must be a PIL.Image.Image")

        width, height = image.size

        if width <= 0 or height <= 0:
            raise ValueError("Image dimensions must be greater than zero")

        if width > MAX_IMAGE_WIDTH:
            raise ValueError(
                f"Image width exceeds maximum allowed width of "
                f"{MAX_IMAGE_WIDTH} pixels"
            )

        if height > MAX_IMAGE_HEIGHT:
            raise ValueError(
                f"Image height exceeds maximum allowed height of "
                f"{MAX_IMAGE_HEIGHT} pixels"
            )

        pixel_count = width * height

        if pixel_count > MAX_IMAGE_PIXELS:
            raise ValueError(
                f"Image contains {pixel_count:,} pixels, exceeding the "
                f"maximum allowed {MAX_IMAGE_PIXELS:,} pixels"
            )

    def analyze(self, image, url=None):
        component_errors = []

        # ---------------------------------------------------------
        # Input validation
        # ---------------------------------------------------------
        try:
            self._validate_image(image)
            image_valid = True
        except Exception as exc:
            image_valid = False
            component_errors.append(
                {
                    "component": "INPUT",
                    "error": str(exc),
                }
            )

        # ---------------------------------------------------------
        # OCR / text analysis
        # ---------------------------------------------------------
        if image_valid:
            try:
                extracted_text = self.ocr.extract_text(image)
                text_result = detect_suspicious_text(extracted_text)
            except Exception as exc:
                extracted_text = ""
                text_result = {
                    "score": 0.0,
                    "matches": [],
                    "error": "Text analysis unavailable",
                }

                component_errors.append(
                    {
                        "component": "OCR",
                        "error": "OCR analysis unavailable.",
                    }
                )
        else:
            extracted_text = ""
            text_result = {
                "score": 0.0,
                "matches": [],
                "error": "Text analysis unavailable because image input is invalid",
            }

        # ---------------------------------------------------------
        # URL analysis
        # ---------------------------------------------------------
        if url:
            try:
                url_result = analyze_url(url)
                url_score = url_result["score"]
            except Exception as exc:
                url_result = {
                    "url": url,
                    "hostname": "",
                    "indicators": [],
                    "matched_keywords": [],
                    "score": 0.0,
                    "is_suspicious": False,
                    "error": "URL analysis unavailable",
                }

                url_score = 0.0

                component_errors.append(
                    {
                        "component": "URL",
                        "error": "URL analysis unavailable.",
                    }
                )
        else:
            url_result = None
            url_score = 0.0

        # ---------------------------------------------------------
        # CNN analysis
        # ---------------------------------------------------------
        if self.cnn.model_loaded and image_valid:
            try:
                cnn_result = self.cnn.predict(image)
            except Exception as exc:
                cnn_result = {
                    "prediction": None,
                    "phishing_probability": None,
                    "legitimate_probability": None,
                    "threshold": self.cnn.threshold,
                    "model_loaded": True,
                    "error": "CNN analysis unavailable",
                }

                component_errors.append(
                    {
                        "component": "CNN",
                        "error": "CNN analysis unavailable.",
                    }
                )
        elif self.cnn.model_loaded:
            cnn_result = {
                "prediction": None,
                "phishing_probability": None,
                "legitimate_probability": None,
                "threshold": self.cnn.threshold,
                "model_loaded": True,
                "error": "CNN analysis unavailable because image input is invalid",
            }

            component_errors.append(
                {
                    "component": "CNN",
                    "error": "CNN analysis skipped because image input is invalid",
                }
            )
        else:
            cnn_result = {
                "prediction": None,
                "phishing_probability": None,
                "legitimate_probability": None,
                "threshold": CNN_THRESHOLD,
                "model_loaded": False,
                "error": "CNN model unavailable",
            }

            component_errors.append(
                {
                    "component": "CNN",
                    "error": "CNN model is not loaded",
                }
            )

        if (
            cnn_result.get("model_loaded")
            and cnn_result.get("phishing_probability") is not None
        ):
            cnn_score = float(cnn_result["phishing_probability"]) * 100
        else:
            cnn_score = 0.0

        # ---------------------------------------------------------
        # Risk calculation
        # ---------------------------------------------------------
        risk_result = calculate_risk(
            text_result["score"],
            url_score,
            cnn_score,
        )

        # ---------------------------------------------------------
        # Security assessment
        # ---------------------------------------------------------
        security_assessment = build_security_assessment(
            text_result,
            url_result,
            cnn_result,
            risk_result,
        )

        # ---------------------------------------------------------
        # Attach component availability information
        # ---------------------------------------------------------
        security_assessment["component_errors"] = component_errors

        return {
            "extracted_text": extracted_text,
            "text_analysis": text_result,
            "url_analysis": url_result,
            "cnn_analysis": cnn_result,
            "risk": risk_result,
            "security_assessment": security_assessment,
        }
