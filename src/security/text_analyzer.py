import re


SUSPICIOUS_KEYWORDS = [
    "verify your account",
    "verify account",
    "confirm your account",
    "sign in",
    "login",
    "password",
    "credential",
    "security alert",
    "account suspended",
    "account locked",
    "urgent",
    "immediately",
    "click here",
    "reset password",
    "update payment",
    "license key",
]


def normalize_text(text):
    """Normalize OCR text for analysis."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_suspicious_text(text):
    """
    Detect suspicious keywords in OCR-extracted text.

    Returns:
        dict containing matched keywords and risk score.
    """

    normalized = normalize_text(text)

    matches = []

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in normalized:
            matches.append(keyword)

    # Cap score at 100
    score = min(len(matches) * 10, 100)

    return {
        "matches": matches,
        "score": score,
        "is_suspicious": len(matches) > 0,
    }