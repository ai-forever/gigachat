import os

import pytest


@pytest.fixture(autouse=True)
def _delenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear environment variables for each test."""
    monkeypatch.setattr(os, "environ", {})
