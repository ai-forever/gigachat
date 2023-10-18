import os

import pytest


@pytest.fixture(autouse=True)
def _delenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {})
