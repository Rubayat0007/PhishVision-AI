"""AppTest entry point that renders a recorded analyzer result.

Not collected by pytest (filename does not start with ``test_``); AppTest
executes it as a Streamlit script.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.ui.render import render_analysis  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "analyzer_result.json"

render_analysis(json.loads(FIXTURE.read_text(encoding="utf-8")))
