from pathlib import Path

from src.models.predictor import CNNPredictor
from src.ocr.ocr_engine import OCREngine
from src.security.text_analyzer import detect_suspicious_text
from src.security.url_analyzer import analyze_url
from src.security.risk_engine import calculate_risk


class PhishVisionAnalyzer:

    def __init__(self):
        self.ocr = OCREngine()

        model_path = Path("models/phishvision_cnn.pth")

        if model_path.exists():
            self.cnn = CNNPredictor(
                model_path=str(model_path)
            )
        else:
            self.cnn = CNNPredictor()

    def analyze(self, image, url=None):

        # --------------------
        # OCR
        # --------------------

        extracted_text = self.ocr.extract_text(image)

        # --------------------
        # Text analysis
        # --------------------

        text_result = detect_suspicious_text(
            extracted_text
        )

        # --------------------
        # URL analysis
        # --------------------

        if url:
            url_result = analyze_url(url)
            url_score = url_result["score"]
        else:
            url_result = None
            url_score = 0

        # --------------------
        # CNN image analysis
        # --------------------

        if self.cnn.model_loaded:
            cnn_result = self.cnn.predict(image)
        else:
            cnn_result = {
                "prediction": None,
                "phishing_probability": None,
                "legitimate_probability": None,
                "model_loaded": False,
            }

        # --------------------
        # Risk engine
        # --------------------

        risk_result = calculate_risk(
            text_result["score"],
            url_score,
        )

        # --------------------
        # Final result
        # --------------------

        return {
            "extracted_text": extracted_text,
            "text_analysis": text_result,
            "url_analysis": url_result,
            "cnn_analysis": cnn_result,
            "risk": risk_result,
        }