import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from PIL import Image, UnidentifiedImageError

from src.config import (
    MAX_IMAGE_HEIGHT,
    MAX_IMAGE_PIXELS,
    MAX_IMAGE_WIDTH,
    MAX_UPLOAD_SIZE_BYTES,
)
from src.security.analyzer import PhishVisionAnalyzer
from src.ui.render import render_analysis


st.set_page_config(
    page_title="PhishVision AI",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ PhishVision AI")
st.subheader(
    "AI-Based Phishing Screenshot & Malicious Interface Detection"
)

st.write(
    "Upload a website screenshot and optionally provide its URL "
    "for security analysis."
)


# -------------------------
# Analyzer
# -------------------------

@st.cache_resource
def load_analyzer():
    return PhishVisionAnalyzer()


analyzer = load_analyzer()


# -------------------------
# Input
# -------------------------

uploaded_file = st.file_uploader(
    "Upload Website Screenshot",
    type=["png", "jpg", "jpeg", "webp"],
)

url = st.text_input(
    "Website URL (optional)",
    placeholder="https://example.com",
)


def load_and_validate_image(uploaded_file):
    """
    Decode and validate an uploaded image before displaying or analyzing it.

    The validation is intentionally performed at the application boundary
    so oversized/pathological images are rejected before OCR/CNN processing.
    """
    try:
        if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
            max_size_mib = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            return None, (
                f"Uploaded file exceeds the maximum allowed size "
                f"of {max_size_mib:g} MiB."
            )

        image = Image.open(uploaded_file)

        # Force image metadata and pixel dimensions to be read.
        image.load()

        width, height = image.size

        if width <= 0 or height <= 0:
            raise ValueError(
                "Image dimensions must be greater than zero."
            )

        if width > MAX_IMAGE_WIDTH:
            raise ValueError(
                f"Image width exceeds the maximum allowed width "
                f"of {MAX_IMAGE_WIDTH} pixels."
            )

        if height > MAX_IMAGE_HEIGHT:
            raise ValueError(
                f"Image height exceeds the maximum allowed height "
                f"of {MAX_IMAGE_HEIGHT} pixels."
            )

        pixel_count = width * height

        if pixel_count > MAX_IMAGE_PIXELS:
            raise ValueError(
                f"Image contains {pixel_count:,} pixels, exceeding "
                f"the maximum allowed {MAX_IMAGE_PIXELS:,} pixels."
            )

        # Normalize the image only after the safety checks above.
        image = image.convert("RGB")

        return image, None

    except (UnidentifiedImageError, OSError):
        return None, "The uploaded file could not be decoded as a valid image."

    except ValueError as exc:
        return None, str(exc)

    except Exception:
        return None, "The uploaded image could not be processed safely."


if uploaded_file is not None:

    image, image_error = load_and_validate_image(uploaded_file)

    if image_error:
        st.error(f"Upload rejected: {image_error}")
    else:

        st.image(
            image,
            caption="Uploaded Screenshot",
            width="stretch",
        )

        if st.button("🔍 Analyze", type="primary"):

            with st.spinner("Analyzing screenshot..."):
                result = analyzer.analyze(
                    image,
                    url.strip() if url.strip() else None,
                )

            render_analysis(result)
