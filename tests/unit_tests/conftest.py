import os
from typing import Any, Dict, cast

import pytest

from tests.constants import (
    ACCESS_TOKEN,
    AUTH_URL,
    BASE_URL,
    CHAT_URL,
    CREDENTIALS,
    TOKEN,
    TOKEN_URL,
)


@pytest.fixture(autouse=True)
def _delenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {})


@pytest.fixture
def base_url() -> str:
    return BASE_URL


@pytest.fixture
def auth_url() -> str:
    return AUTH_URL


@pytest.fixture
def credentials() -> str:
    return CREDENTIALS


@pytest.fixture
def token_url() -> str:
    return TOKEN_URL


@pytest.fixture
def chat_url() -> str:
    return CHAT_URL


@pytest.fixture
def mock_access_token() -> Dict[str, Any]:
    return cast(Dict[str, Any], ACCESS_TOKEN)


@pytest.fixture
def mock_token() -> Dict[str, Any]:
    return cast(Dict[str, Any], TOKEN)
