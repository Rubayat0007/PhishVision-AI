import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from PIL import Image

from src.security.analyzer import PhishVisionAnalyzer


st.set_page_config(
    page_title="PhishVision AI",
    page_icon="🛡️",
    layout="wide",
)


st.title("🛡️ PhishVision AI")
st.subheader("AI-Based Phishing Screenshot & Malicious Interface Detection")

st.write(
    "Upload a website screenshot and optionally provide its URL "
    "for security analysis."
)


# Initialize analyzer
@st.cache_resource
def load_analyzer():
    return PhishVisionAnalyzer()


analyzer = load_analyzer()


# Input section
uploaded_file = st.file_uploader(
    "Upload Website Screenshot",
    type=["png", "jpg", "jpeg", "webp"],
)

url = st.text_input(
    "Website URL (optional)",
    placeholder="https://example.com",
)


if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    st.image(
        image,
        caption="Uploaded Screenshot",
        width="stretch",
    )

    if st.button("🔍 Analyze", type="primary"):

        with st.spinner("Analyzing screenshot..."):
            result = analyzer.analyze(
                image,
                url if url.strip() else None,
            )

        st.divider()

        # -------------------------
        # Risk Summary
        # -------------------------

        st.header("Security Analysis")

        risk = result["risk"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Overall Risk Score",
                risk["overall_score"],
            )

        with col2:
            st.metric(
                "Risk Level",
                risk["risk_level"],
            )

        with col3:
            st.metric(
                "Text Risk",
                risk["text_score"],
            )

        # -------------------------
        # OCR
        # -------------------------

        st.header("OCR Extracted Text")

        extracted_text = result["extracted_text"]

        if extracted_text:
            st.text_area(
                "Detected Text",
                extracted_text,
                height=180,
            )
        else:
            st.info("No readable text detected.")

        # -------------------------
        # Suspicious Text
        # -------------------------

        st.header("Suspicious Text Indicators")

        text_analysis = result["text_analysis"]

        if text_analysis["matches"]:
            for keyword in text_analysis["matches"]:
                st.warning(f"⚠️ {keyword}")
        else:
            st.success("No suspicious keywords detected.")

        # -------------------------
        # URL Analysis
        # -------------------------

        if result["url_analysis"]:

            st.header("URL Analysis")

            url_result = result["url_analysis"]

            st.write(
                "**Hostname:**",
                url_result["hostname"],
            )

            st.write(
                "**URL Risk Score:**",
                url_result["score"],
            )

            if url_result["indicators"]:

                st.write("**Indicators:**")

                for indicator in url_result["indicators"]:
                    st.warning(f"⚠️ {indicator}")

            else:
                st.success(
                    "No suspicious URL indicators detected."
                )

        # -------------------------
        # CNN Analysis
        # -------------------------

        st.header("CNN Image Analysis")

        cnn_result = result["cnn_analysis"]

        if cnn_result["model_loaded"]:

            prediction = cnn_result["prediction"]

            if prediction == "phishing":
                st.error(
                    f"🚨 CNN Prediction: {prediction.upper()}"
                )
            else:
                st.success(
                    f"✅ CNN Prediction: {prediction.upper()}"
                )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Phishing Probability",
                    f"{cnn_result['phishing_probability'] * 100:.2f}%"
                )

            with col2:
                st.metric(
                    "Legitimate Probability",
                    f"{cnn_result['legitimate_probability'] * 100:.2f}%"
                )

        else:
            st.info(
                "🤖 CNN model is not trained yet. "
                "Image-based ML prediction will be available "
                "after model training."
            )        

        # -------------------------
        # Final Assessment
        # -------------------------

        st.divider()

        st.header("Final Assessment")

        if risk["risk_level"] == "HIGH":
            st.error(
                "🚨 HIGH RISK: The interface contains "
                "multiple suspicious indicators."
            )

        elif risk["risk_level"] == "MEDIUM":
            st.warning(
                "⚠️ MEDIUM RISK: The interface contains "
                "potentially suspicious characteristics."
            )

        elif risk["risk_level"] == "LOW":
            st.info(
                "ℹ️ LOW RISK: Some suspicious indicators "
                "were detected, but the evidence is limited."
            )

        else:
            st.success(
                "✅ MINIMAL RISK: No significant suspicious "
                "indicators were detected."
            )

else:
    st.info(
        "Upload a screenshot to begin the analysis."
    )