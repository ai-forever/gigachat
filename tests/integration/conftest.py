"""Configuration for integration tests using VCR/cassette-based recording."""

import json
import os
import re
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator

import pytest
from dotenv import load_dotenv

from gigachat import GigaChat

if not os.getenv("CI"):
    load_dotenv()

# 2100-01-01 00:00:00 UTC (milliseconds) - ensures cassette tokens never appear expired during replay
EXPIRES_AT_VALID = 4102444800000
EXP_VALID = EXPIRES_AT_VALID // 1000
TEST_TIMEOUT = float(os.getenv("GIGACHAT_TEST_TIMEOUT", "120"))


def _scrub_request(request: Any) -> Any:
    """Scrub scope from OAuth request bodies to prevent credential leakage."""
    if request.body:
        body = request.body
        if isinstance(body, bytes):
            body = re.sub(rb"scope=[^&\s]*", b"scope=REDACTED", body)
            request.body = body
        elif isinstance(body, str):
            body = re.sub(r"scope=[^&\s]*", "scope=REDACTED", body)
            request.body = body
    return request


def _scrub_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Scrub access_token and expires_at from OAuth response bodies.

    This prevents credential leakage and ensures tokens never appear expired
    during cassette replay (expires_at/exp are set to year 2100).
    """
    headers = response.get("headers", {})
    for header in list(headers):
        if header.lower() == "set-cookie":
            del headers[header]

    body = response.get("body", {}).get("string", b"")
    if body:
        try:
            body_str = body.decode("utf-8") if isinstance(body, bytes) else body
            data = json.loads(body_str)
            if "access_token" in data:
                data["access_token"] = "REDACTED"
            if "tok" in data:
                data["tok"] = "REDACTED"
            if "expires_at" in data:
                data["expires_at"] = EXPIRES_AT_VALID
            if "exp" in data:
                data["exp"] = EXP_VALID
            response["body"]["string"] = json.dumps(data).encode("utf-8")
        except (json.JSONDecodeError, UnicodeDecodeError):
            if isinstance(body, bytes):
                body = re.sub(rb'"access_token"\s*:\s*"[^"]*"', b'"access_token": "REDACTED"', body)
                body = re.sub(rb'"tok"\s*:\s*"[^"]*"', b'"tok": "REDACTED"', body)
                body = re.sub(
                    rb'"expires_at"\s*:\s*\d+',
                    f'"expires_at": {EXPIRES_AT_VALID}'.encode(),
                    body,
                )
                body = re.sub(
                    rb'"exp"\s*:\s*\d+',
                    f'"exp": {EXP_VALID}'.encode(),
                    body,
                )
                response["body"]["string"] = body
    return response


@pytest.fixture(scope="module")
def vcr_config() -> Dict[str, Any]:
    """Configure VCR for recording HTTP interactions."""
    return {
        "filter_headers": [
            ("authorization", "Bearer REDACTED"),
            ("cookie", "REDACTED"),
        ],
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
        "record_mode": os.getenv("VCR_RECORD_MODE", "once"),
        "decode_compressed_response": True,
        "before_record_request": _scrub_request,
        "before_record_response": _scrub_response,
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir() -> str:
    """Store cassettes in tests/integration/cassettes/ directory."""
    return str(Path(__file__).parent / "cassettes")


def _get_auth_settings() -> Dict[str, str]:
    """Get auth settings from environment or use dummy values for CI.

    In CI environments (where CI=true), VCR cassettes provide all HTTP responses,
    so real credentials are not needed. Dummy values allow tests to run in replay mode.
    """
    credentials = os.getenv("GIGACHAT_CREDENTIALS")
    scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    user = os.getenv("GIGACHAT_USER")
    password = os.getenv("GIGACHAT_PASSWORD")

    if credentials:
        return {"credentials": credentials, "scope": scope}

    if user and password:
        return {"user": user, "password": password}

    # In CI, use dummy credentials since VCR cassettes handle all HTTP responses
    if os.getenv("CI"):
        return {"credentials": "dummy-credentials-for-vcr-replay", "scope": scope}

    pytest.skip("GIGACHAT_CREDENTIALS or GIGACHAT_USER/GIGACHAT_PASSWORD not set (and not in CI)")


@pytest.fixture
def gigachat_client() -> Generator[GigaChat, None, None]:
    """Create GigaChat client using credentials from environment variables."""
    auth_settings = _get_auth_settings()

    with GigaChat(
        credentials=auth_settings.get("credentials"),
        scope=auth_settings.get("scope"),
        user=auth_settings.get("user"),
        password=auth_settings.get("password"),
        verify_ssl_certs=False,
        timeout=TEST_TIMEOUT,
    ) as client:
        yield client


@pytest.fixture
async def gigachat_async_client() -> AsyncGenerator[GigaChat, None]:
    """Create async GigaChat client using credentials from environment variables."""
    auth_settings = _get_auth_settings()

    async with GigaChat(
        credentials=auth_settings.get("credentials"),
        scope=auth_settings.get("scope"),
        user=auth_settings.get("user"),
        password=auth_settings.get("password"),
        verify_ssl_certs=False,
        timeout=TEST_TIMEOUT,
    ) as client:
        yield client
