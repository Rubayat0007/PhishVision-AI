import re
from urllib.parse import urlparse


SUSPICIOUS_URL_KEYWORDS = [
    "login",
    "verify",
    "account",
    "secure",
    "update",
    "password",
    "signin",
    "confirm",
    "bank",
    "paypal",
]


def analyze_url(url):
    """
    Analyze a URL for basic phishing-related indicators.
    """

    parsed = urlparse(url)

    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    full_url = url.lower()

    indicators = []

    # HTTP instead of HTTPS
    if parsed.scheme.lower() == "http":
        indicators.append("uses_http")

    # IP address used as hostname
    if re.fullmatch(
        r"\d{1,3}(\.\d{1,3}){3}",
        hostname,
    ):
        indicators.append("ip_address")

    # Very long URL
    if len(url) > 100:
        indicators.append("long_url")

    # Many subdomains
    if hostname.count(".") >= 3:
        indicators.append("many_subdomains")

    # Suspicious characters
    if "@" in url:
        indicators.append("contains_at_symbol")

    if "-" in hostname:
        indicators.append("hyphen_in_domain")

    # Suspicious keywords
    matched_keywords = []

    for keyword in SUSPICIOUS_URL_KEYWORDS:
        if keyword in full_url:
            matched_keywords.append(keyword)

    if matched_keywords:
        indicators.append("suspicious_keywords")

    # Calculate simple risk score
    score = min(len(indicators) * 15, 100)

    return {
        "url": url,
        "hostname": hostname,
        "indicators": indicators,
        "matched_keywords": matched_keywords,
        "score": score,
        "is_suspicious": score > 0,
    }