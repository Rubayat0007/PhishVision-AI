from pathlib import Path
import ast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = PROJECT_ROOT / "app" / "app.py"
CONFIG_PATH = PROJECT_ROOT / "src" / "config.py"

passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed

    if condition:
        print(f"PASS: {name}")
        passed += 1
    else:
        print(f"FAIL: {name}")
        if detail:
            print(f"  {detail}")
        failed += 1


# ------------------------------------------------------------------
# Load source without importing app.py.
#
# Importing app.py would execute the Streamlit application, so this
# test extracts only load_and_validate_image().
# ------------------------------------------------------------------

app_source = APP_PATH.read_text(encoding="utf-8-sig")
tree = ast.parse(app_source)

function_node = next(
    (
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "load_and_validate_image"
    ),
    None,
)

check(
    "load_and_validate_image function exists",
    function_node is not None,
)

if function_node is None:
    print()
    print("UPLOAD BOUNDARY TEST SUMMARY")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("STATUS: FAIL")
    raise SystemExit(1)


# Verify the function contains the expected upload-size boundary.
function_source = ast.get_source_segment(app_source, function_node)

check(
    "MAX_UPLOAD_SIZE_BYTES is enforced",
    "MAX_UPLOAD_SIZE_BYTES" in function_source,
)

check(
    "Size check occurs before Image.open",
    function_source.find("uploaded_file.size") <
    function_source.find("Image.open"),
    "The upload size must be checked before image decoding.",
)


# ------------------------------------------------------------------
# Extract and execute only the validator.
# ------------------------------------------------------------------

module = ast.Module(
    body=[function_node],
    type_ignores=[],
)

namespace = {
    "Image": __import__("PIL.Image", fromlist=["Image"]),
    "UnidentifiedImageError": __import__(
        "PIL",
        fromlist=["UnidentifiedImageError"],
    ).UnidentifiedImageError,
    "OSError": OSError,
    "ValueError": ValueError,
    "MAX_UPLOAD_SIZE_BYTES": 10 * 1024 * 1024,
    "MAX_IMAGE_WIDTH": 4096,
    "MAX_IMAGE_HEIGHT": 4096,
    "MAX_IMAGE_PIXELS": 16_777_216,
}

exec(compile(module, str(APP_PATH), "exec"), namespace)

validator = namespace["load_and_validate_image"]


class FakeUpload:
    def __init__(self, size):
        self.size = size


# ------------------------------------------------------------------
# Boundary tests.
#
# The first two cases use a valid image because they are expected to
# reach decoding. The oversized case deliberately uses invalid bytes
# because it must be rejected before Image.open() is reached.
# ------------------------------------------------------------------

from io import BytesIO
from PIL import Image


def valid_upload(size):
    image = Image.new("RGB", (1, 1), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    upload = FakeUpload(size)
    upload.seek = buffer.seek
    upload.read = buffer.read
    upload.tell = buffer.tell
    return upload


# Below maximum.
upload = valid_upload((10 * 1024 * 1024) - 1)
image, error = validator(upload)

check(
    "10 MiB - 1 byte is accepted by size boundary",
    error is None,
    str(error),
)


# Exactly maximum.
upload = valid_upload(10 * 1024 * 1024)
image, error = validator(upload)

check(
    "Exactly 10 MiB is accepted by size boundary",
    error is None,
    str(error),
)


# Above maximum. This must fail before Image.open().
class OversizedInvalidUpload:
    size = (10 * 1024 * 1024) + 1

    def read(self, *args, **kwargs):
        raise AssertionError(
            "Image decoding was reached for an oversized upload."
        )


upload = OversizedInvalidUpload()
image, error = validator(upload)

check(
    "10 MiB + 1 byte is rejected",
    image is None and error is not None,
    str(error),
)

check(
    "Oversized upload is rejected before image decoding",
    "maximum allowed size" in str(error).lower(),
    str(error),
)


print()
print("UPLOAD BOUNDARY TEST SUMMARY")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"STATUS: {'PASS' if failed == 0 else 'FAIL'}")

raise SystemExit(0 if failed == 0 else 1)

