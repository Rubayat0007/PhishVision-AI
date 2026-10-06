import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from PIL import Image

from src.security.analyzer import PhishVisionAnalyzer


TEST_DIR = Path("data/clean_split_v2/test")


def find_image(class_name, filename):
    path = TEST_DIR / class_name / filename

    if not path.exists():
        raise FileNotFoundError(path)

    return path


SCENARIOS = [
    {
        "name": "Phishing screenshot without URL",
        "class_name": "phishing",
        "filename": "phishing_0004.jpg",
        "url": None,
    },
    {
        "name": "Phishing screenshot with normal HTTPS URL",
        "class_name": "phishing",
        "filename": "phishing_0004.jpg",
        "url": "https://example.com/",
    },
    {
        "name": "Phishing screenshot with suspicious URL",
        "class_name": "phishing",
        "filename": "phishing_0004.jpg",
        "url": "http://192.168.1.10/login/verify-account",
    },
    {
        "name": "Legitimate screenshot without URL",
        "class_name": "legitimate",
        "filename": "legitimate_0002.jpg",
        "url": None,
    },
    {
        "name": "Legitimate screenshot with HTTPS URL",
        "class_name": "legitimate",
        "filename": "legitimate_0002.jpg",
        "url": "https://example.com/",
    },
    {
        "name": "Legitimate screenshot with suspicious URL",
        "class_name": "legitimate",
        "filename": "legitimate_0002.jpg",
        "url": "http://192.168.1.10/login/verify-account",
    },
]


def print_findings(findings):
    if not findings:
        print("    Findings: none")
        return

    for finding in findings:
        print(
            "    "
            f"[{finding['severity']}] "
            f"{finding['source']} / "
            f"{finding['category']}: "
            f"{finding['evidence']}"
        )


def main():
    analyzer = PhishVisionAnalyzer()

    print()
    print("PHISHVISION-AI SECURITY SCENARIO TEST")
    print("=" * 60)

    failures = 0

    for index, scenario in enumerate(SCENARIOS, start=1):

        print()
        print(f"[{index}] {scenario['name']}")
        print("-" * 60)

        image_path = find_image(
            scenario["class_name"],
            scenario["filename"],
        )

        try:
            with Image.open(image_path) as image:
                result = analyzer.analyze(
                    image,
                    scenario["url"],
                )

            risk = result["risk"]
            assessment = result["security_assessment"]

            print(f"Image:       {image_path}")
            print(f"URL:         {scenario['url']}")
            print()
            print(
                f"Verdict:     {assessment['verdict']}"
            )
            print(
                f"Risk level:  {assessment['risk_level']}"
            )
            print(
                f"Risk score:  {assessment['overall_score']:.2f}"
            )
            print()
            print("Component scores:")
            print(
                f"  Text:      {risk['text_score']:.2f}"
            )
            print(
                f"  URL:       {risk['url_score']:.2f}"
            )
            print(
                f"  CNN:       {risk['cnn_score']:.2f}"
            )

            print()
            print("Security findings:")
            print_findings(
                assessment["evidence"]
            )

            print()
            print(
                "Recommended action:"
            )
            print(
                f"  {assessment['recommended_action']}"
            )

        except Exception as exc:
            failures += 1

            print()
            print("STATUS: FAIL")
            print(f"Error: {exc}")

    print()
    print("=" * 60)

    if failures:
        print(
            f"SCENARIO TEST: FAIL "
            f"({failures} scenario(s) failed)"
        )
        raise SystemExit(1)

    print(
        f"SCENARIO TEST: PASS "
        f"({len(SCENARIOS)} scenarios)"
    )


if __name__ == "__main__":
    main()