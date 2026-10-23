"""Emit one PhishVision analyzer result as JSON, using the production model."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from src.security.analyzer import PhishVisionAnalyzer  # noqa: E402


def main() -> int:
    font = ImageFont.load_default(size=46)
    image = Image.new("RGB", (1200, 520), "white")
    draw = ImageDraw.Draw(image)
    for index, line in enumerate([
        "SECURITY ALERT",
        "Verify your account and enter your password",
    ]):
        draw.text((50, 40 + index * 100), line, fill="black", font=font)

    result = PhishVisionAnalyzer().analyze(image, "http://192.168.1.10/login/verify-account")

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
