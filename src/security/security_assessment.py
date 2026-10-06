from typing import Any


def _text_findings(text_result: dict[str, Any]) -> list[dict[str, Any]]:
    findings = []

    matches = text_result.get("matches", [])

    credential_keywords = {
        "password",
        "credential",
        "login",
        "sign in",
        "reset password",
    }

    urgency_keywords = {
        "urgent",
        "immediately",
        "account suspended",
        "account locked",
        "security alert",
    }

    account_keywords = {
        "verify your account",
        "verify account",
        "confirm your account",
        "account suspended",
        "account locked",
    }

    payment_keywords = {
        "update payment",
    }

    for match in matches:
        if match in credential_keywords:
            category = "credential_harvesting"
            severity = "HIGH"
        elif match in urgency_keywords:
            category = "urgency"
            severity = "MEDIUM"
        elif match in account_keywords:
            category = "account_verification"
            severity = "MEDIUM"
        elif match in payment_keywords:
            category = "payment_request"
            severity = "HIGH"
        else:
            category = "suspicious_text"
            severity = "LOW"

        findings.append(
            {
                "source": "OCR",
                "category": category,
                "severity": severity,
                "evidence": match,
            }
        )

    return findings


def _url_findings(url_result: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not url_result:
        return []

    findings = []

    indicator_messages = {
        "uses_http": (
            "transport_security",
            "MEDIUM",
            "URL uses HTTP instead of HTTPS",
        ),
        "ip_address": (
            "ip_hostname",
            "HIGH",
            "URL uses an IP address as the hostname",
        ),
        "long_url": (
            "long_url",
            "LOW",
            "URL is unusually long",
        ),
        "many_subdomains": (
            "many_subdomains",
            "MEDIUM",
            "URL contains multiple subdomains",
        ),
        "contains_at_symbol": (
            "url_obfuscation",
            "HIGH",
            "URL contains an @ symbol",
        ),
        "hyphen_in_domain": (
            "domain_structure",
            "LOW",
            "Hostname contains a hyphen",
        ),
        "suspicious_keywords": (
            "suspicious_url_keywords",
            "MEDIUM",
            "URL contains phishing-related keywords",
        ),
    }

    for indicator in url_result.get("indicators", []):
        definition = indicator_messages.get(indicator)

        if definition is None:
            continue

        category, severity, evidence = definition

        findings.append(
            {
                "source": "URL",
                "category": category,
                "severity": severity,
                "evidence": evidence,
            }
        )

    for keyword in url_result.get("matched_keywords", []):
        findings.append(
            {
                "source": "URL",
                "category": "suspicious_url_keyword",
                "severity": "MEDIUM",
                "evidence": keyword,
            }
        )

    return findings


def _cnn_findings(cnn_analysis):
    findings = []

    if not cnn_analysis or not cnn_analysis.get("model_loaded"):
        return findings

    phishing_probability = cnn_analysis.get("phishing_probability")

    if phishing_probability is None:
        return findings

    phishing_probability = float(phishing_probability)
    threshold = float(cnn_analysis.get("threshold", 0.35))

    if phishing_probability >= threshold:
        if phishing_probability >= 0.70:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        findings.append(
            {
                "source": "CNN",
                "category": "visual_phishing_signal",
                "severity": severity,
                "evidence": (
                    "CNN detected a visual phishing signal with "
                    f"p(phishing)={phishing_probability:.4f}"
                ),
            }
        )

    elif phishing_probability >= threshold * 0.75:
        findings.append(
            {
                "source": "CNN",
                "category": "elevated_visual_signal",
                "severity": "MEDIUM",
                "evidence": (
                    "CNN detected an elevated visual phishing signal with "
                    f"p(phishing)={phishing_probability:.4f}, "
                    f"below the decision threshold of {threshold:.2f}"
                ),
            }
        )

    return findings


def build_security_assessment(
    text_result: dict[str, Any],
    url_result: dict[str, Any] | None,
    cnn_result: dict[str, Any],
    risk_result: dict[str, Any],
) -> dict[str, Any]:

    findings = []

    findings.extend(_text_findings(text_result))
    findings.extend(_url_findings(url_result))
    findings.extend(_cnn_findings(cnn_result))

    risk_level = risk_result["risk_level"]

    verdict_map = {
        "MINIMAL": "MINIMAL RISK",
        "LOW": "LOW RISK",
        "MEDIUM": "MEDIUM RISK",
        "HIGH": "HIGH RISK",
    }

    verdict = verdict_map.get(
        risk_level,
        "UNKNOWN",
    )

    if risk_level == "HIGH":
        recommended_action = (
            "Do not enter passwords, payment information, "
            "or other sensitive credentials on this page."
        )
    elif risk_level == "MEDIUM":
        recommended_action = (
            "Exercise caution. Verify the website and its "
            "domain through an independent trusted source "
            "before entering sensitive information."
        )
    elif risk_level == "LOW":
        recommended_action = (
            "No strong phishing signal was established, "
            "but normal security precautions should still "
            "be followed."
        )
    else:
        recommended_action = (
            "No significant phishing indicators were detected "
            "by the current analysis."
        )

    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "overall_score": risk_result["overall_score"],
        "evidence": findings,
        "finding_count": len(findings),
        "recommended_action": recommended_action,
        "component_scores": {
            "text": risk_result["text_score"],
            "url": risk_result["url_score"],
            "cnn": risk_result["cnn_score"],
        },
    }