import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image
from src.security.analyzer import PhishVisionAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEST_IMAGE = (
    PROJECT_ROOT
    / "data"
    / "clean_split_v2"
    / "test"
    / "phishing"
    / "phishing_0004.jpg"
)


def validate_result(result):
    required = {
        "extracted_text",
        "text_analysis",
        "url_analysis",
        "cnn_analysis",
        "risk",
        "security_assessment",
    }

    missing = required - set(result.keys())

    if missing:
        return False, f"missing keys: {sorted(missing)}"

    risk = result["risk"]

    if not 0 <= float(risk["overall_score"]) <= 100:
        return False, "risk score outside [0, 100]"

    return True, "valid security assessment"


def run_normal_case(name, analyzer, image, url=None):
    print(f"\n[{name}]")
    print("-" * 60)

    try:
        result = analyzer.analyze(image, url=url)

        passed, message = validate_result(result)

        if passed:
            print("PASS:", message)
            print(
                "Risk:",
                result["risk"]["risk_level"],
                result["risk"]["overall_score"],
            )
        else:
            print("FAIL:", message)

        return passed

    except Exception as exc:
        print("FAIL: unhandled exception")
        print(f"{type(exc).__name__}: {exc}")
        return False


def run_ocr_failure_case(analyzer, image):
    print("\n[2. Simulated OCR failure]")
    print("-" * 60)

    try:
        with patch.object(
            analyzer.ocr,
            "extract_text",
            side_effect=RuntimeError("simulated OCR failure"),
        ):
            result = analyzer.analyze(image)

        passed, message = validate_result(result)

        if not passed:
            print("FAIL:", message)
            return False

        component_errors = result["security_assessment"].get(
            "component_errors",
            []
        )

        ocr_errors = [
            error
            for error in component_errors
            if error.get("component") == "OCR"
        ]

        if not ocr_errors:
            print("FAIL: OCR failure was not recorded")
            return False

        if result["text_analysis"].get("error") != "Text analysis unavailable":
            print("FAIL: OCR unavailable state not recorded")
            return False

        print("PASS:", message)
        print(
            "Risk:",
            result["risk"]["risk_level"],
            result["risk"]["overall_score"],
        )
        print("OCR failure recorded: True")

        return True

    except Exception as exc:
        print("FAIL: unhandled exception")
        print(f"{type(exc).__name__}: {exc}")
        return False


def run_url_failure_case(analyzer, image):
    print("\n[3. Simulated URL analyzer failure]")
    print("-" * 60)

    try:
        with patch(
            "src.security.analyzer.analyze_url",
            side_effect=RuntimeError("simulated URL analyzer failure"),
        ):
            result = analyzer.analyze(
                image,
                url="https://example.com/",
            )

        passed, message = validate_result(result)

        if not passed:
            print("FAIL:", message)
            return False

        component_errors = result["security_assessment"].get(
            "component_errors",
            []
        )

        url_errors = [
            error
            for error in component_errors
            if error.get("component") == "URL"
        ]

        if not url_errors:
            print("FAIL: URL failure was not recorded")
            return False

        if result["url_analysis"].get("error") != "URL analysis unavailable":
            print("FAIL: URL unavailable state not recorded")
            return False

        print("PASS:", message)
        print(
            "Risk:",
            result["risk"]["risk_level"],
            result["risk"]["overall_score"],
        )
        print("URL failure recorded: True")

        return True

    except Exception as exc:
        print("FAIL: unhandled exception")
        print(f"{type(exc).__name__}: {exc}")
        return False


def run_cnn_failure_case(analyzer, image):
    print("\n[4. Simulated CNN failure]")
    print("-" * 60)

    try:
        with patch.object(
            analyzer.cnn,
            "predict",
            side_effect=RuntimeError("simulated CNN failure"),
        ):
            result = analyzer.analyze(image)

        passed, message = validate_result(result)

        if not passed:
            print("FAIL:", message)
            return False

        component_errors = result["security_assessment"].get(
            "component_errors",
            []
        )

        cnn_errors = [
            error
            for error in component_errors
            if error.get("component") == "CNN"
        ]

        if not cnn_errors:
            print("FAIL: CNN failure was not recorded")
            return False

        if result["cnn_analysis"].get("error") != "CNN analysis unavailable":
            print("FAIL: CNN unavailable state not recorded")
            return False

        print("PASS:", message)
        print(
            "Risk:",
            result["risk"]["risk_level"],
            result["risk"]["overall_score"],
        )
        print("CNN failure recorded: True")
        print(
            "CNN analysis error:",
            result["cnn_analysis"]["error"],
        )

        return True

    except Exception as exc:
        print("FAIL: unhandled exception")
        print(f"{type(exc).__name__}: {exc}")
        return False


def main():
    print("PHISHVISION-AI FAILURE-INJECTION TEST")
    print("=" * 60)

    if not TEST_IMAGE.exists():
        raise FileNotFoundError(TEST_IMAGE)

    image = Image.open(TEST_IMAGE).convert("RGB")
    analyzer = PhishVisionAnalyzer()

    results = []

    # 1. Normal baseline
    results.append(
        run_normal_case(
            "1. Normal baseline",
            analyzer,
            image,
        )
    )

    # 2. OCR failure
    results.append(
        run_ocr_failure_case(
            analyzer,
            image,
        )
    )

    # 3. URL analyzer failure
    results.append(
        run_url_failure_case(
            analyzer,
            image,
        )
    )

    # 4. CNN failure
    results.append(
        run_cnn_failure_case(
            analyzer,
            image,
        )
    )

    passed = sum(results)
    total = len(results)

    print("\n")
    print("=" * 60)
    print("FAILURE-INJECTION SUMMARY")
    print("=" * 60)
    print(f"Passed:  {passed}/{total}")
    print(f"Failed:  {total - passed}/{total}")

    if passed == total:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")


if __name__ == "__main__":
    main()