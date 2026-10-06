import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from src.config import (
    MAX_IMAGE_HEIGHT,
    MAX_IMAGE_PIXELS,
    MAX_IMAGE_WIDTH,
    MAX_OCR_TEXT_LENGTH,
    MAX_URL_LENGTH,
)
from src.security.analyzer import PhishVisionAnalyzer
from src.models.predictor import CNNPredictor
from src.security.url_analyzer import analyze_url


TEST_IMAGE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "clean_split_v2"
    / "test"
    / "phishing"
    / "phishing_0004.jpg"
)


def check_result(name, result):
    required_keys = {
        "extracted_text",
        "text_analysis",
        "url_analysis",
        "cnn_analysis",
        "risk",
        "security_assessment",
    }

    missing = required_keys - set(result.keys())

    if missing:
        return False, f"missing keys: {sorted(missing)}"

    risk = result["risk"]

    risk_keys = {
        "text_score",
        "url_score",
        "cnn_score",
        "overall_score",
        "risk_level",
    }

    missing_risk = risk_keys - set(risk.keys())

    if missing_risk:
        return False, f"missing risk keys: {sorted(missing_risk)}"

    if not 0 <= float(risk["overall_score"]) <= 100:
        return False, "overall score outside [0, 100]"

    if risk["risk_level"] not in {
        "MINIMAL",
        "LOW",
        "MEDIUM",
        "HIGH",
    }:
        return False, f"invalid risk level: {risk['risk_level']}"

    return True, "valid result"


def run_image_case(analyzer, name, image):
    print(f"\n[{name}]")

    try:
        result = analyzer.analyze(image)

        passed, message = check_result(name, result)

        if passed:
            print("PASS:", message)
            print(
                "  Risk:",
                result["risk"]["risk_level"],
                result["risk"]["overall_score"],
            )
        else:
            print("FAIL:", message)

        return passed

    except Exception as exc:
        print("FAIL: exception raised")
        print(f"  {type(exc).__name__}: {exc}")
        return False


def run_image_limit_case(analyzer, name, image, expected_error):
    print(f"\n[{name}]")
    print(f"Image size: {image.size}")

    try:
        result = analyzer.analyze(image)

        component_errors = result["security_assessment"].get(
            "component_errors",
            [],
        )

        input_errors = [
            item
            for item in component_errors
            if item.get("component") == "INPUT"
        ]

        cnn_result = result["cnn_analysis"]

        matching_input_error = any(
            expected_error in item.get("error", "")
            for item in input_errors
        )

        cnn_skipped = (
            cnn_result.get("prediction") is None
            and cnn_result.get("phishing_probability") is None
            and cnn_result.get("legitimate_probability") is None
            and cnn_result.get("error")
            == "CNN analysis unavailable because image input is invalid"
        )

        if matching_input_error and cnn_skipped:
            print("PASS: image rejected by input boundary")
            print("  Input error:", expected_error)
            print("  CNN: skipped")
            return True

        print("FAIL: expected image rejection behavior was not observed")
        print("  Component errors:", component_errors)
        print("  CNN result:", cnn_result)
        return False

    except Exception as exc:
        print("FAIL: unexpected exception")
        print(f"  {type(exc).__name__}: {exc}")
        return False


def run_image_limit_acceptance_case(analyzer, name, image):
    print(f"\n[{name}]")
    print(f"Image size: {image.size}")

    try:
        result = analyzer.analyze(image)

        passed, message = check_result(name, result)

        if not passed:
            print("FAIL:", message)
            return False

        component_errors = result["security_assessment"].get(
            "component_errors",
            [],
        )

        input_errors = [
            item
            for item in component_errors
            if item.get("component") == "INPUT"
        ]

        if input_errors:
            print("FAIL: exact-limit image was rejected")
            print("  Input errors:", input_errors)
            return False

        cnn_result = result["cnn_analysis"]

        if not cnn_result.get("model_loaded"):
            print("FAIL: CNN was not available for valid exact-limit image")
            return False

        if cnn_result.get("phishing_probability") is None:
            print("FAIL: CNN did not produce a probability")
            return False

        print("PASS: exact image boundary accepted")
        print(
            "  CNN phishing probability:",
            cnn_result["phishing_probability"],
        )

        return True

    except Exception as exc:
        print("FAIL: unexpected exception")
        print(f"  {type(exc).__name__}: {exc}")
        return False



def run_ocr_limit_case(name, text_length, should_raise):
    print(f"\n[{name}]")
    print("OCR text length:", text_length)

    class FakeReader:
        def readtext(self, image):
            return [
                (
                    None,
                    "a" * text_length,
                    0.99,
                )
            ]

    try:

        # Avoid initializing EasyOCR. We only need to exercise
        # OCREngine.extract_text() boundary behavior.
        from src.ocr.ocr_engine import OCREngine

        ocr = OCREngine.__new__(OCREngine)
        ocr.reader = FakeReader()

        result = ocr.extract_text(Image.new("RGB", (1, 1)))

        if should_raise:
            print("FAIL: oversized OCR text was accepted")
            print("  Returned length:", len(result))
            return False

        if len(result) != text_length:
            print("FAIL: returned OCR text length changed unexpectedly")
            print("  Expected:", text_length)
            print("  Actual:", len(result))
            return False

        print("PASS: OCR text accepted at maximum boundary")
        return True

    except ValueError as exc:
        if should_raise:
            expected = (
                "OCR text exceeds maximum allowed length of "
                f"{MAX_OCR_TEXT_LENGTH} characters"
            )

            if str(exc) != expected:
                print("FAIL: unexpected OCR validation error")
                print("  Expected:", expected)
                print("  Actual:", str(exc))
                return False

            print("PASS: oversized OCR text rejected")
            print("  Error:", exc)
            return True

        print("FAIL: unexpected ValueError")
        print(f"  {exc}")
        return False

    except Exception as exc:
        print("FAIL: unexpected exception")
        print(f"  {type(exc).__name__}: {exc}")
        return False


def run_url_case(name, url):
    print(f"\n[{name}]")
    print("URL:", repr(url))

    try:
        result = analyze_url(url)

        required_keys = {
            "url",
            "hostname",
            "indicators",
            "matched_keywords",
            "score",
            "is_suspicious",
        }

        missing = required_keys - set(result.keys())

        if missing:
            print("FAIL: missing keys:", sorted(missing))
            return False

        score = float(result["score"])

        if not 0 <= score <= 100:
            print("FAIL: score outside [0, 100]")
            return False

        print("PASS")
        print("  Score:", score)
        print("  Indicators:", result["indicators"])

        return True

    except Exception as exc:
        print("FAIL: exception raised")
        print(f"  {type(exc).__name__}: {exc}")
        return False



def run_url_limit_case(name, url, should_raise):
    print(f"\n[{name}]")
    print("URL length:", len(url))

    try:
        result = analyze_url(url)

        if should_raise:
            print("FAIL: oversized URL was accepted")
            print("  Score:", result["score"])
            return False

        required_keys = {
            "url",
            "hostname",
            "indicators",
            "matched_keywords",
            "score",
            "is_suspicious",
        }

        missing = required_keys - set(result.keys())

        if missing:
            print("FAIL: missing keys:", sorted(missing))
            return False

        print("PASS: URL accepted at maximum boundary")
        print("  Score:", result["score"])
        return True

    except ValueError as exc:
        if should_raise:
            print("PASS: oversized URL rejected")
            print("  Error:", exc)
            return True

        print("FAIL: unexpected ValueError")
        print(f"  {exc}")
        return False

    except Exception as exc:
        print("FAIL: unexpected exception")
        print(f"  {type(exc).__name__}: {exc}")
        return False



def run_analyzer_input_case(name, image, url, expected_component=None):
    print(f"\n[{name}]")
    print("Image type:", type(image).__name__)
    print("URL type:", type(url).__name__)

    try:
        analyzer = PhishVisionAnalyzer()
        result = analyzer.analyze(image, url=url)

        passed, message = check_result(name, result)

        if not passed:
            print("FAIL:", message)
            return False

        component_errors = result["security_assessment"].get(
            "component_errors",
            [],
        )

        if expected_component is None:
            if component_errors:
                print("FAIL: unexpected component errors")
                print("  Errors:", component_errors)
                return False

            print("PASS: input accepted without component errors")
            return True

        matching_errors = [
            item
            for item in component_errors
            if item.get("component") == expected_component
        ]

        if not matching_errors:
            print(
                f"FAIL: expected {expected_component} component error "
                "was not recorded"
            )
            print("  Errors:", component_errors)
            return False

        print(
            f"PASS: {expected_component} input failure handled gracefully"
        )
        print("  Error:", matching_errors[0]["error"])
        return True

    except Exception as exc:
        print("FAIL: unexpected exception")
        print(f"  {type(exc).__name__}: {exc}")
        return False


def run_model_failure_case(name, model_path, corrupt=False):
    print(f"\n[{name}]")
    print("Model path:", model_path)

    try:
        model_path = Path(model_path)

        if corrupt:
            model_path.write_bytes(b"not a valid pytorch checkpoint")

        predictor = CNNPredictor(model_path=model_path)

        if predictor.model_loaded:
            print("FAIL: unavailable model was reported as loaded")
            return False

        print("PASS: model failure handled gracefully")
        print("  Model loaded:", predictor.model_loaded)
        return True

    except Exception as exc:
        print("FAIL: unexpected exception")
        print(f"  {type(exc).__name__}: {exc}")
        return False

    finally:
        if corrupt:
            try:
                model_path.unlink(missing_ok=True)
            except OSError as exc:
                print(f"WARNING: could not remove temporary model: {exc}")


def main():
    print("PHISHVISION-AI PRODUCTION HARDENING BASELINE")
    print("=" * 60)

    if not TEST_IMAGE.exists():
        raise FileNotFoundError(TEST_IMAGE)

    analyzer = PhishVisionAnalyzer()

    print("\nMODEL STATUS")
    print("-" * 60)
    print("Model loaded:", analyzer.cnn.model_loaded)
    print("Threshold:", analyzer.cnn.threshold)

    results = []

    # ---------------------------------------------------------
    # Model loading failure handling
    # ---------------------------------------------------------

    missing_model = (
        Path(__file__).resolve().parents[1]
        / "models"
        / "_nonexistent_test_model.pth"
    )

    results.append(
        run_model_failure_case(
            "11. Missing CNN model",
            missing_model,
            corrupt=False,
        )
    )

    corrupt_model = (
        Path(__file__).resolve().parents[1]
        / "models"
        / "_corrupt_test_model.pth"
    )

    results.append(
        run_model_failure_case(
            "12. Corrupt CNN model",
            corrupt_model,
            corrupt=True,
        )
    )

    # ---------------------------------------------------------
    # Image handling
    # ---------------------------------------------------------

    reference = Image.open(TEST_IMAGE).convert("RGB")

    results.append(
        run_image_case(
            analyzer,
            "1. Normal RGB image",
            reference,
        )
    )

    grayscale = reference.convert("L")

    results.append(
        run_image_case(
            analyzer,
            "2. Grayscale image",
            grayscale,
        )
    )

    rgba = reference.convert("RGBA")

    results.append(
        run_image_case(
            analyzer,
            "3. RGBA image",
            rgba,
        )
    )

    tiny = Image.new("RGB", (8, 8), (255, 255, 255))

    results.append(
        run_image_case(
            analyzer,
            "4. Very small image",
            tiny,
        )
    )

    unusual = Image.new("RGB", (2000, 20), (240, 240, 240))

    results.append(
        run_image_case(
            analyzer,
            "5. Extreme aspect ratio",
            unusual,
        )
    )

    blank = Image.new("RGB", (1920, 995), (255, 255, 255))

    results.append(
        run_image_case(
            analyzer,
            "6. Uniform white image",
            blank,
        )
    )

    # ---------------------------------------------------------
    # Image resource boundaries
    # ---------------------------------------------------------

    oversized_width = Image.new(
        "RGB",
        (MAX_IMAGE_WIDTH + 1, 100),
        (255, 255, 255),
    )

    results.append(
        run_image_limit_case(
            analyzer,
            "7. Image width above limit",
            oversized_width,
            f"Image width exceeds maximum allowed width of {MAX_IMAGE_WIDTH} pixels",
        )
    )

    exact_pixel_limit = Image.new(
        "RGB",
        (MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT),
        (255, 255, 255),
    )

    results.append(
        run_image_limit_acceptance_case(
            analyzer,
            "8. Exact maximum pixel boundary",
            exact_pixel_limit,
        )
    )

    oversized_height = Image.new(
        "RGB",
        (MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT + 1),
        (255, 255, 255),
    )

    results.append(
        run_image_limit_case(
            analyzer,
            "9. Image height above limit",
            oversized_height,
            f"Image height exceeds maximum allowed height of {MAX_IMAGE_HEIGHT} pixels",
        )
    )

    # Explicit pixel-count boundary check.
    expected_pixels = MAX_IMAGE_WIDTH * MAX_IMAGE_HEIGHT

    if expected_pixels == MAX_IMAGE_PIXELS:
        print(
            "\n[10. Pixel-limit configuration consistency]\n"
            f"PASS: {MAX_IMAGE_WIDTH} x {MAX_IMAGE_HEIGHT} "
            f"= {MAX_IMAGE_PIXELS:,} pixels"
        )
        results.append(True)
    else:
        print(
            "\n[10. Pixel-limit configuration consistency]\n"
            "FAIL: configured image dimensions do not match "
            "MAX_IMAGE_PIXELS"
        )
        print("  Expected:", expected_pixels)
        print("  Configured:", MAX_IMAGE_PIXELS)
        results.append(False)


        # ---------------------------------------------------------
    # OCR text resource boundaries
    # ---------------------------------------------------------

    results.append(
        run_ocr_limit_case(
            "13. OCR text at maximum length",
            MAX_OCR_TEXT_LENGTH,
            should_raise=False,
        )
    )

    results.append(
        run_ocr_limit_case(
            "14. OCR text above maximum length",
            MAX_OCR_TEXT_LENGTH + 1,
            should_raise=True,
        )
    )

    # ---------------------------------------------------------
    # Analyzer input-type boundaries
    # ---------------------------------------------------------

    results.append(
        run_analyzer_input_case(
            "15. Analyzer with None URL",
            reference,
            None,
            expected_component=None,
        )
    )

    results.append(
        run_analyzer_input_case(
            "16. Analyzer with invalid image type",
            "not an image",
            None,
            expected_component="INPUT",
        )
    )

    results.append(
        run_analyzer_input_case(
            "17. Analyzer with invalid URL type",
            reference,
            12345,
            expected_component="URL",
        )
    )



    # ---------------------------------------------------------
    # URL handling
    # ---------------------------------------------------------

    urls = [
        ("18. Empty URL", ""),
        ("19. HTTPS URL", "https://example.com/"),
        (
            "20. Suspicious HTTP URL",
            "http://192.168.1.10/login/verify-account",
        ),
        (
            "21. Malformed URL",
            "not a valid url",
        ),
        (
            "22. Unsupported scheme",
            "javascript:alert(1)",
        ),
    ]

    for name, url in urls:
        results.append(run_url_case(name, url))

    # ---------------------------------------------------------
    # URL resource boundaries
    # ---------------------------------------------------------

    url_prefix = "https://example.com/"

    max_length_url = url_prefix + (
        "a" * (MAX_URL_LENGTH - len(url_prefix))
    )

    oversized_url = url_prefix + (
        "a" * (MAX_URL_LENGTH + 1 - len(url_prefix))
    )

    results.append(
        run_url_limit_case(
            "23. URL at maximum length boundary",
            max_length_url,
            should_raise=False,
        )
    )

    results.append(
        run_url_limit_case(
            "24. URL above maximum length",
            oversized_url,
            should_raise=True,
        )
    )

    # ---------------------------------------------------------
    # Analyzer + URL integration
    # ---------------------------------------------------------

    print("\n[18. Analyzer with malformed URL]")
    print("-" * 60)

    try:
        result = analyzer.analyze(
            reference,
            url="not a valid url",
        )

        passed, message = check_result(
            "Analyzer with malformed URL",
            result,
        )

        if passed:
            print("PASS:", message)
            print(
                "  Risk:",
                result["risk"]["risk_level"],
                result["risk"]["overall_score"],
            )
        else:
            print("FAIL:", message)

        results.append(passed)

    except Exception as exc:
        print("FAIL: exception raised")
        print(f"  {type(exc).__name__}: {exc}")
        results.append(False)

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    passed_count = sum(results)
    total_count = len(results)

    print("\n")
    print("=" * 60)
    print("HARDENING BASELINE SUMMARY")
    print("=" * 60)
    print(f"Passed:  {passed_count}/{total_count}")
    print(f"Failed:  {total_count - passed_count}/{total_count}")

    if passed_count == total_count:
        print("STATUS: PASS")
    else:
        print("STATUS: FAIL")
        print("Review the failing cases before making hardening changes.")


if __name__ == "__main__":
    main()
