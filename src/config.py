from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Main directories
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
APP_DIR = PROJECT_ROOT / "app"


# Dataset directories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"


# Model configuration
MODEL_DIR = MODELS_DIR

ACTIVE_MODEL_PATH = MODEL_DIR / "phishvision_cnn_v2.pth"
CNN_THRESHOLD = 0.35


# Image configuration
IMAGE_SIZE = 224

# Production input safety limits.
# These limits protect expensive OCR/CNN processing from pathological inputs.
MAX_IMAGE_WIDTH = 4096
MAX_IMAGE_HEIGHT = 4096
MAX_IMAGE_PIXELS = 16_777_216
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


# URL and OCR/text input safety limits.
MAX_URL_LENGTH = 2048
MAX_OCR_TEXT_LENGTH = 100_000


# Classification labels
CLASS_NAMES = [
    "legitimate",
    "phishing",
]
