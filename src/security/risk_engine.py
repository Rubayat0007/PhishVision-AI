def calculate_risk(text_score, url_score):
    """
    Combine text and URL security signals.

    Text analysis contributes 60%.
    URL analysis contributes 40%.

    The final score is a heuristic security score,
    not an ML probability.
    """

    combined_score = (
        text_score * 0.60
        + url_score * 0.40
    )

    combined_score = round(combined_score, 2)

    # Risk classification
    if combined_score >= 70:
        risk_level = "HIGH"
    elif combined_score >= 30:
        risk_level = "MEDIUM"
    elif text_score > 0 or url_score > 0:
        risk_level = "LOW"
    else:
        risk_level = "MINIMAL"

    return {
        "text_score": text_score,
        "url_score": url_score,
        "overall_score": combined_score,
        "risk_level": risk_level,
    }