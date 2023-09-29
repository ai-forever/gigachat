import os

import pytest


@pytest.fixture(autouse=True)
def _delenv(monkeypatch) -> None:
    monkeypatch.setattr(os, "environ", {})
