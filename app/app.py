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


st.set_page_config(
    page_title="PhishVision AI",
    page_icon="ðŸ›¡ï¸",
    layout="wide",
)

st.title("ðŸ›¡ï¸ PhishVision AI")
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
        st.error(f"âŒ Upload rejected: {image_error}")
    else:

        st.image(
            image,
            caption="Uploaded Screenshot",
            width="stretch",
        )

        if st.button("ðŸ” Analyze", type="primary"):

            with st.spinner("Analyzing screenshot..."):
                result = analyzer.analyze(
                    image,
                    url.strip() if url.strip() else None,
                )

            risk = result["risk"]
            assessment = result["security_assessment"]
            cnn_result = result["cnn_analysis"]
            text_analysis = result["text_analysis"]
            url_result = result["url_analysis"]

            st.divider()

            # -------------------------
            # Security Verdict
            # -------------------------

            st.header("Security Verdict")

            verdict = assessment["verdict"]
            overall_score = assessment["overall_score"]

            if risk["risk_level"] == "HIGH":
                st.error(
                    f"ðŸš¨ {verdict} â€” Score: {overall_score}/100"
                )

            elif risk["risk_level"] == "MEDIUM":
                st.warning(
                    f"âš ï¸ {verdict} â€” Score: {overall_score}/100"
                )

            elif risk["risk_level"] == "LOW":
                st.info(
                    f"â„¹ï¸ {verdict} â€” Score: {overall_score}/100"
                )

            else:
                st.success(
                    f"âœ… {verdict} â€” Score: {overall_score}/100"
                )

            st.write(
                f"**Recommended action:** "
                f"{assessment['recommended_action']}"
            )

            # -------------------------
            # Component Scores
            # -------------------------

            st.header("Component Analysis")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Screenshot / CNN",
                    f"{assessment['component_scores']['cnn']:.2f}",
                )

            with col2:
                st.metric(
                    "Text / OCR",
                    f"{assessment['component_scores']['text']:.2f}",
                )

            with col3:
                st.metric(
                    "URL",
                    f"{assessment['component_scores']['url']:.2f}",
                )

            # -------------------------
            # Security Evidence
            # -------------------------

            st.header("Security Evidence")

            findings = assessment["evidence"]

            if findings:

                for finding in findings:

                    source = finding["source"]
                    category = finding["category"]
                    severity = finding["severity"]
                    evidence = finding["evidence"]

                    title = (
                        f"{severity} â€” "
                        f"{category.replace('_', ' ').title()}"
                    )

                    if severity == "HIGH":
                        st.error(
                            f"**{title}**  \n"
                            f"Source: {source}  \n"
                            f"{evidence}"
                        )

                    elif severity == "MEDIUM":
                        st.warning(
                            f"**{title}**  \n"
                            f"Source: {source}  \n"
                            f"{evidence}"
                        )

                    else:
                        st.info(
                            f"**{title}**  \n"
                            f"Source: {source}  \n"
                            f"{evidence}"
                        )

            else:
                st.success(
                    "No structured security findings were generated."
                )

            # -------------------------
            # OCR
            # -------------------------

            with st.expander("OCR Analysis", expanded=False):

                extracted_text = result["extracted_text"]

                if extracted_text:
                    st.text_area(
                        "Detected Text",
                        extracted_text,
                        height=180,
                    )
                else:
                    st.info("No readable text detected.")

                st.subheader("Suspicious Text Indicators")

                if text_analysis["matches"]:

                    for keyword in text_analysis["matches"]:
                        st.warning(
                            f"âš ï¸ {keyword}"
                        )

                else:
                    st.success(
                        "No suspicious keywords detected."
                    )

            # -------------------------
            # URL Analysis
            # -------------------------

            with st.expander("URL Analysis", expanded=False):

                if url_result:

                    st.write(
                        "**Hostname:**",
                        url_result["hostname"],
                    )

                    st.metric(
                        "URL Risk Score",
                        url_result["score"],
                    )

                    if url_result["indicators"]:

                        st.write("**Indicators:**")

                        for indicator in url_result["indicators"]:
                            st.warning(
                                f"âš ï¸ {indicator}"
                            )

                    else:
                        st.success(
                            "No suspicious URL indicators detected."
                        )

                else:
                    st.info(
                        "No URL was provided. URL analysis was skipped."
                    )

            # -------------------------
            # CNN Analysis
            # -------------------------

            with st.expander("CNN Image Analysis", expanded=False):

                if cnn_result["model_loaded"]:

                    prediction = cnn_result["prediction"]

                    if prediction == "phishing":
                        st.error(
                            f"ðŸš¨ CNN prediction: "
                            f"{prediction.upper()}"
                        )
                    else:
                        st.success(
                            f"âœ… CNN prediction: "
                            f"{prediction.upper()}"
                        )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Phishing Probability",
                            (
                                f"{cnn_result['phishing_probability'] * 100:.2f}%"
                            ),
                        )

                    with col2:
                        st.metric(
                            "Legitimate Probability",
                            (
                                f"{cnn_result['legitimate_probability'] * 100:.2f}%"
                            ),
                        )

                    st.caption(
                        f"Decision threshold: "
                        f"{cnn_result.get('threshold', 0.35):.2f}"
                    )

                else:
                    st.warning(
                        "CNN model is not available. "
                        "Image-based analysis could not be performed."
                    )

            # -------------------------
            # Risk Calculation
            # -------------------------

            with st.expander("Risk Calculation", expanded=False):

                st.write(
                    "The overall risk score is a heuristic combination "
                    "of the available security signals."
                )

                st.code(
                    "0.30 Ã— Text + 0.30 Ã— URL + 0.40 Ã— CNN"
                )

                st.write(
                    f"**Text:** {risk['text_score']:.2f}"
                )

                st.write(
                    f"**URL:** {risk['url_score']:.2f}"
                )

                st.write(
                    f"**CNN:** {risk['cnn_score']:.2f}"
                )

                st.write(
                    f"**Overall:** {risk['overall_score']:.2f}"
                )

                st.caption(
                    "This score is a heuristic security score, "
                    "not a calibrated probability of phishing."
                )
