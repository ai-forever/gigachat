import re
from pathlib import Path

import gigachat


def test_version_matches_project_metadata() -> None:
    pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', content, re.MULTILINE)

    assert match is not None
    assert gigachat.__version__ == match.group(1)
