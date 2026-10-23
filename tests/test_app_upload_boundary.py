"""Upload-boundary tests for the Streamlit application.

Importing ``app/app.py`` would execute the Streamlit page, so the
validator is extracted from the module source and executed in isolation.
This keeps the security boundary (size limits before decoding) under
test without importing torch, the model, or Streamlit.
"""

import ast
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, UnidentifiedImageError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "app" / "app.py"

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


class FakeUpload:
    def __init__(self, size):
        self.size = size


def _load_source():
    return APP_PATH.read_text(encoding="utf-8-sig")


def _load_function_node(source):
    tree = ast.parse(source)

    return next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "load_and_validate_image"
        ),
        None,
    )


def _load_validator(source, node):
    module = ast.Module(body=[node], type_ignores=[])

    namespace = {
        "Image": Image,
        "UnidentifiedImageError": UnidentifiedImageError,
        "OSError": OSError,
        "ValueError": ValueError,
        "MAX_UPLOAD_SIZE_BYTES": MAX_UPLOAD_SIZE_BYTES,
        "MAX_IMAGE_WIDTH": 4096,
        "MAX_IMAGE_HEIGHT": 4096,
        "MAX_IMAGE_PIXELS": 16_777_216,
    }

    exec(compile(module, str(APP_PATH), "exec"), namespace)

    return namespace["load_and_validate_image"]


@pytest.fixture(scope="module")
def source():
    return _load_source()


@pytest.fixture(scope="module")
def validator(source):
    node = _load_function_node(source)

    assert node is not None, (
        "load_and_validate_image is missing from app/app.py"
    )

    return _load_validator(source, node)


def valid_upload(size):
    image = Image.new("RGB", (1, 1), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    upload = FakeUpload(size)
    upload.seek = buffer.seek
    upload.read = buffer.read
    upload.tell = buffer.tell

    return upload


def test_validator_exists(source):
    assert _load_function_node(source) is not None


def test_size_limit_is_enforced(source, validator):
    node = _load_function_node(source)
    function_source = ast.get_source_segment(source, node)

    assert "MAX_UPLOAD_SIZE_BYTES" in function_source


def test_size_check_precedes_image_decoding(source):
    node = _load_function_node(source)
    function_source = ast.get_source_segment(source, node)

    assert function_source.find("uploaded_file.size") < function_source.find(
        "Image.open"
    ), "The upload size must be checked before image decoding."


def test_upload_one_byte_below_limit_is_accepted(validator):
    image, error = validator(valid_upload(MAX_UPLOAD_SIZE_BYTES - 1))

    assert error is None
    assert image is not None


def test_upload_at_limit_is_accepted(validator):
    image, error = validator(valid_upload(MAX_UPLOAD_SIZE_BYTES))

    assert error is None
    assert image is not None


def test_upload_over_limit_is_rejected_before_decoding(validator):
    class OversizedInvalidUpload:
        size = MAX_UPLOAD_SIZE_BYTES + 1

        def read(self, *args, **kwargs):
            raise AssertionError(
                "Image decoding was reached for an oversized upload."
            )

    image, error = validator(OversizedInvalidUpload())

    assert image is None
    assert error is not None
    assert "maximum allowed size" in error.lower()
