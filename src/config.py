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


# Image configuration
IMAGE_SIZE = (224, 224)


# Classification labels
CLASS_NAMES = [
    "legitimate",
    "phishing",
]