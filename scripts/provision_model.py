from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "phishvision_cnn_v2.pth"

MODEL_URL = (
    "https://github.com/Rubayat0007/PhishVision-AI/"
    "releases/download/v1.0.0-model/phishvision_cnn_v2-release.pth"
)

EXPECTED_SHA256 = (
    "1403582CCE07BE1E36E70E4A0D425CFB152B86C7ABEE5D1074DEF79CBB2FB628"
)


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def download_model(destination: Path) -> None:
    request = Request(
        MODEL_URL,
        headers={
            "User-Agent": "PhishVision-AI-model-provisioner/1.0",
        },
    )

    with urlopen(request, timeout=120) as response:
        with destination.open("wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)


def main() -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        prefix="phishvision_model_",
        suffix=".pth",
        dir=MODELS_DIR,
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        print("Downloading production CNN model...")
        download_model(temp_path)

        print("Verifying SHA-256...")
        actual_sha256 = calculate_sha256(temp_path)

        if actual_sha256 != EXPECTED_SHA256:
            print("ERROR: Model SHA-256 verification failed.")
            print(f"Expected: {EXPECTED_SHA256}")
            print(f"Received: {actual_sha256}")
            return 1

        temp_path.replace(MODEL_PATH)

        print("Production CNN model provisioned successfully.")
        print(f"Model path: {MODEL_PATH}")
        print(f"SHA-256: {actual_sha256}")

        return 0

    except Exception:
        print("ERROR: Production CNN model provisioning failed.")
        return 1

    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
