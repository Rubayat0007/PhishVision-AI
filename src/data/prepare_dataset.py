from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = PROJECT_ROOT / "data" / "raw" / "phishing" / "sample_0001_0500"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "phishing"


def prepare_phishing_screenshots():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    screenshots = SOURCE_DIR.glob("*/screenshots/original_js_on.jpg")

    copied = 0

    for screenshot in screenshots:
        sample_id = screenshot.parent.parent.name
        destination = OUTPUT_DIR / f"{sample_id}.jpg"

        shutil.copy2(screenshot, destination)
        copied += 1

    print(f"Phishing screenshots copied: {copied}")


if __name__ == "__main__":
    prepare_phishing_screenshots()