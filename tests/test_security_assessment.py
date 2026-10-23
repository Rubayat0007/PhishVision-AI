"""Contract tests for the security assessment layer.

``build_security_assessment`` is a pure function: it turns component
results plus the risk engine output into a verdict, an evidence list,
and a recommended action. These tests exercise it without importing the
analyzer (and therefore without requiring torch, OCR, or a model file).
"""

import pytest

from src.security.security_assessment import build_security_assessment


def make_text(matches=()):
    return {
        "matches": list(matches),
        "score": 10.0 * len(matches),
        "is_suspicious": bool(matches),
    }


def make_url(indicators=(), matched_keywords=()):
    return {
        "url": "http://192.168.1.10/login",
        "hostname": "192.168.1.10",
        "indicators": list(indicators),
        "matched_keywords": list(matched_keywords),
        "score": 15.0 * (len(indicators) + len(matched_keywords)),
        "is_suspicious": bool(indicators or matched_keywords),
    }


def make_cnn(probability=None, model_loaded=True, threshold=0.35):
    return {
        "prediction": (
            None
            if probability is None
            else ("phishing" if probability >= threshold else "legitimate")
        ),
        "phishing_probability": probability,
        "legitimate_probability": (
            None if probability is None else 1.0 - probability
        ),
        "threshold": threshold,
        "model_loaded": model_loaded,
    }


def make_risk(level="MINIMAL", text=0.0, url=0.0, cnn=0.0):
    return {
        "text_score": text,
        "url_score": url,
        "cnn_score": cnn,
        "overall_score": round(text * 0.3 + url * 0.3 + cnn * 0.4, 2),
        "risk_level": level,
    }


def assess(text=None, url=None, cnn=None, risk=None):
    return build_security_assessment(
        text if text is not None else make_text(),
        url,
        cnn if cnn is not None else make_cnn(),
        risk if risk is not None else make_risk(),
    )


@pytest.mark.parametrize(
    ("level", "verdict"),
    [
        ("MINIMAL", "MINIMAL RISK"),
        ("LOW", "LOW RISK"),
        ("MEDIUM", "MEDIUM RISK"),
        ("HIGH", "HIGH RISK"),
        ("UNEXPECTED", "UNKNOWN"),
    ],
)
def test_verdict_follows_risk_level(level, verdict):
    result = assess(risk=make_risk(level=level))

    assert result["verdict"] == verdict
    assert result["risk_level"] == level


@pytest.mark.parametrize(
    ("level", "phrase"),
    [
        ("HIGH", "Do not enter passwords"),
        ("MEDIUM", "Exercise caution"),
        ("LOW", "No strong phishing signal"),
        ("MINIMAL", "No significant phishing indicators"),
        ("UNEXPECTED", "No significant phishing indicators"),
    ],
)
def test_recommended_action_follows_risk_level(level, phrase):
    result = assess(risk=make_risk(level=level))

    assert phrase in result["recommended_action"]


@pytest.mark.parametrize(
    ("match", "category", "severity"),
    [
        ("password", "credential_harvesting", "HIGH"),
        ("login", "credential_harvesting", "HIGH"),
        ("urgent", "urgency", "MEDIUM"),
        ("immediately", "urgency", "MEDIUM"),
        ("verify your account", "account_verification", "MEDIUM"),
        ("update payment", "payment_request", "HIGH"),
        ("click here", "suspicious_text", "LOW"),
    ],
)
def test_text_findings_are_categorised(match, category, severity):
    result = assess(text=make_text([match]))

    assert result["finding_count"] == 1
    finding = result["evidence"][0]
    assert finding["source"] == "OCR"
    assert finding["category"] == category
    assert finding["severity"] == severity
    assert finding["evidence"] == match


@pytest.mark.parametrize(
    ("indicator", "category", "severity"),
    [
        ("uses_http", "transport_security", "MEDIUM"),
        ("ip_address", "ip_hostname", "HIGH"),
        ("long_url", "long_url", "LOW"),
        ("many_subdomains", "many_subdomains", "MEDIUM"),
        ("contains_at_symbol", "url_obfuscation", "HIGH"),
        ("hyphen_in_domain", "domain_structure", "LOW"),
        ("suspicious_keywords", "suspicious_url_keywords", "MEDIUM"),
    ],
)
def test_url_indicators_are_categorised(indicator, category, severity):
    result = assess(url=make_url(indicators=[indicator]))

    assert result["finding_count"] == 1
    finding = result["evidence"][0]
    assert finding["source"] == "URL"
    assert finding["category"] == category
    assert finding["severity"] == severity


def test_unknown_url_indicator_is_ignored():
    result = assess(url=make_url(indicators=["invented_indicator"]))

    assert result["finding_count"] == 0


def test_url_matched_keywords_each_add_a_finding():
    result = assess(url=make_url(matched_keywords=["login", "verify"]))

    assert result["finding_count"] == 2
    assert {finding["category"] for finding in result["evidence"]} == {
        "suspicious_url_keyword"
    }
    assert all(
        finding["severity"] == "MEDIUM" for finding in result["evidence"]
    )


def test_absent_url_produces_no_url_findings():
    result = assess(url=None)

    assert result["finding_count"] == 0


@pytest.mark.parametrize(
    ("probability", "severity", "category"),
    [
        (0.90, "HIGH", "visual_phishing_signal"),
        (0.70, "HIGH", "visual_phishing_signal"),
        (0.50, "MEDIUM", "visual_phishing_signal"),
        (0.35, "MEDIUM", "visual_phishing_signal"),
        (0.30, "MEDIUM", "elevated_visual_signal"),
        # Just above the elevated band floor (threshold * 0.75 = 0.2625).
        (0.27, "MEDIUM", "elevated_visual_signal"),
        (0.10, None, None),
    ],
)
def test_cnn_findings_follow_probability_bands(
    probability, severity, category
):
    result = assess(cnn=make_cnn(probability))

    if severity is None:
        assert result["finding_count"] == 0
        return

    assert result["finding_count"] == 1
    finding = result["evidence"][0]
    assert finding["source"] == "CNN"
    assert finding["severity"] == severity
    assert finding["category"] == category


def test_unloaded_model_produces_no_cnn_findings():
    result = assess(cnn=make_cnn(probability=0.99, model_loaded=False))

    assert result["finding_count"] == 0


def test_missing_probability_produces_no_cnn_findings():
    result = assess(cnn=make_cnn(probability=None))

    assert result["finding_count"] == 0


def test_evidence_from_all_components_is_aggregated():
    result = assess(
        text=make_text(["password", "urgent"]),
        url=make_url(indicators=["ip_address"], matched_keywords=["login"]),
        cnn=make_cnn(0.90),
        risk=make_risk(level="HIGH", text=20, url=30, cnn=90),
    )

    assert result["finding_count"] == 5
    assert {finding["source"] for finding in result["evidence"]} == {
        "OCR",
        "URL",
        "CNN",
    }


def test_component_scores_and_overall_score_are_preserved():
    risk = make_risk(level="MEDIUM", text=20.0, url=30.0, cnn=40.0)

    result = assess(risk=risk)

    assert result["component_scores"] == {
        "text": 20.0,
        "url": 30.0,
        "cnn": 40.0,
    }
    assert result["overall_score"] == pytest.approx(31.0)
    assert result["risk_level"] == "MEDIUM"
