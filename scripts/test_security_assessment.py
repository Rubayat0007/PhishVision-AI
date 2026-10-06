import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from PIL import Image

from src.security.analyzer import PhishVisionAnalyzer


TEST_DIR = Path("data/clean_split_v2/test")


def main():
    analyzer = PhishVisionAnalyzer()

    total = 0
    successful = 0
    failures = []

    risk_counts = {
        "MINIMAL": 0,
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
    }

    finding_total = 0

    for class_dir in sorted(TEST_DIR.iterdir()):
        if not class_dir.is_dir():
            continue

        for image_path in sorted(class_dir.glob("*.jpg")):
            total += 1

            try:
                with Image.open(image_path) as image:
                    result = analyzer.analyze(image)

                assessment = result["security_assessment"]

                required_fields = [
                    "verdict",
                    "risk_level",
                    "overall_score",
                    "evidence",
                    "finding_count",
                    "recommended_action",
                    "component_scores",
                ]

                missing = [
                    field
                    for field in required_fields
                    if field not in assessment
                ]

                if missing:
                    raise ValueError(
                        f"Missing fields: {missing}"
                    )

                risk_level = assessment["risk_level"]

                if risk_level not in risk_counts:
                    raise ValueError(
                        f"Invalid risk level: {risk_level}"
                    )

                score = assessment["overall_score"]

                if not 0 <= score <= 100:
                    raise ValueError(
                        f"Invalid overall score: {score}"
                    )

                finding_total += assessment["finding_count"]
                risk_counts[risk_level] += 1
                successful += 1

            except Exception as exc:
                failures.append(
                    {
                        "file": str(image_path),
                        "error": str(exc),
                    }
                )

    print()
    print("SECURITY ASSESSMENT REGRESSION")
    print("=" * 40)
    print(f"Total images:       {total}")
    print(f"Successful:         {successful}")
    print(f"Failures:           {len(failures)}")
    print(f"Total findings:     {finding_total}")
    print()
    print("Risk levels:")

    for level, count in risk_counts.items():
        print(f"  {level:<8}: {count}")

    if failures:
        print()
        print("FAILURES:")

        for failure in failures:
            print(f"  {failure['file']}")
            print(f"    {failure['error']}")

        raise SystemExit(1)

    print()
    print("STATUS: PASS")


if __name__ == "__main__":
    main()