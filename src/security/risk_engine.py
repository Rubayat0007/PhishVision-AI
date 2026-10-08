def calculate_risk(text_score, url_score, cnn_score=0):
    """
    Combine text, URL, and CNN security signals.

    Text analysis: 30%
    URL analysis: 30%
    CNN image analysis: 40%

    cnn_score is the CNN phishing confidence from 0 to 100.

    The final score is a heuristic security score,
    not a calibrated probability.
    """

    # Ensure all inputs stay within the expected range.
    text_score = max(0.0, min(float(text_score), 100.0))
    url_score = max(0.0, min(float(url_score), 100.0))
    cnn_score = max(0.0, min(float(cnn_score), 100.0))

    # Weighted evidence fusion.
    combined_score = (
        text_score * 0.30
        + url_score * 0.30
        + cnn_score * 0.40
    )

    combined_score = round(
        min(combined_score, 100.0),
        2,
    )

    # Risk classification.
    if combined_score >= 70:
        risk_level = "HIGH"
    elif combined_score >= 30:
        risk_level = "MEDIUM"
    elif combined_score > 0:
        risk_level = "LOW"
    else:
        risk_level = "MINIMAL"

    return {
        "text_score": round(text_score, 2),
        "url_score": round(url_score, 2),
        "cnn_score": round(cnn_score, 2),
        "overall_score": combined_score,
        "risk_level": risk_level,
    }