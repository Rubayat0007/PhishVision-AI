"""Streamlit page tests with AppTest.

Scope: the page must import, render, and accept input without raising. The
upload→analyze branch needs a real ``UploadedFile`` object which AppTest does
not construct from bytes; that path is covered instead by the AST-based
validator test and by the analyzer contract tests.

Gated on the full runtime (streamlit, torch, EasyOCR, checkpoint), so CI
skips it; marked ``slow`` because constructing the analyzer takes ~20 s.
"""

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("torch")
pytest.importorskip("easyocr")

from pathlib import Path  # noqa: E402

from streamlit.testing.v1 import AppTest  # noqa: E402

from src.config import ACTIVE_MODEL_PATH  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
APP = REPO / "app" / "app.py"

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not ACTIVE_MODEL_PATH.is_file(),
        reason=f"production checkpoint not provisioned at {ACTIVE_MODEL_PATH}",
    ),
]


@pytest.fixture(scope="module")
def app():
    instance = AppTest.from_file(str(APP), default_timeout=180)
    instance.run()
    return instance


def test_page_renders_without_exception(app):
    assert not app.exception, [str(item) for item in app.exception]


def test_title_is_present(app):
    titles = [item.value for item in app.title]

    assert any("PhishVision" in value for value in titles)


def test_upload_and_url_widgets_exist(app):
    assert len(app.file_uploader) == 1
    assert len(app.text_input) >= 1


def test_url_input_can_be_set_without_breaking_the_page(app):
    app.text_input[0].set_value("http://192.168.1.10/login/verify").run()

    assert not app.exception


def test_no_analysis_is_attempted_before_upload(app):
    # The analyze button lives inside the "file uploaded" branch.
    assert len(app.button) == 0
