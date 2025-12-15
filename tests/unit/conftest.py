import os
from typing import Any, Dict

import pytest

from tests.constants import (
    AUTH_URL,
    BASE_URL,
    CHAT_URL,
    CREDENTIALS,
    OAUTH_TOKEN_EXPIRED,
    OAUTH_TOKEN_VALID,
    PASSWORD_TOKEN_EXPIRED,
    PASSWORD_TOKEN_VALID,
    TOKEN_URL,
)


@pytest.fixture(autouse=True)
def _delenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear environment variables for each test."""
    monkeypatch.setattr(os, "environ", {})


# URL fixtures
@pytest.fixture
def base_url() -> str:
    return BASE_URL


@pytest.fixture
def auth_url() -> str:
    return AUTH_URL


@pytest.fixture
def token_url() -> str:
    return TOKEN_URL


@pytest.fixture
def chat_url() -> str:
    return CHAT_URL


@pytest.fixture
def credentials() -> str:
    return CREDENTIALS


# OAuth token fixtures (/oauth endpoint, access_token/expires_at format)
@pytest.fixture
def oauth_token_valid() -> Dict[str, Any]:
    return OAUTH_TOKEN_VALID


@pytest.fixture
def oauth_token_expired() -> Dict[str, Any]:
    return OAUTH_TOKEN_EXPIRED


# Password auth token fixtures (/token endpoint, tok/exp format)
@pytest.fixture
def password_token_valid() -> Dict[str, Any]:
    return PASSWORD_TOKEN_VALID


@pytest.fixture
def password_token_expired() -> Dict[str, Any]:
    return PASSWORD_TOKEN_EXPIRED
