import os

import pytest

from gigachat.settings import ENV_PREFIX


@pytest.fixture(autouse=True)
def _delenv(monkeypatch) -> None:
    for name in os.environ:
        if name.lower().startswith(ENV_PREFIX.lower()):
            monkeypatch.delenv(name)
