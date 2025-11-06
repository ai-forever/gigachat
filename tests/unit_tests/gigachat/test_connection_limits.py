import asyncio
from typing import List

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient, _get_auth_kwargs, _get_kwargs
from gigachat.exceptions import ResponseError
from gigachat.models import ChatCompletion
from gigachat.settings import Settings

from ...utils import get_json

BASE_URL = "http://base_url"
AUTH_URL = "http://auth_url"
CHAT_URL = f"{BASE_URL}/chat/completions"
TOKEN_URL = f"{BASE_URL}/token"

ACCESS_TOKEN = get_json("access_token.json")
CHAT_COMPLETION = get_json("chat_completion.json")
TOKEN = get_json("token.json")
CREDENTIALS = "NmIwNzhlODgtNDlkNC00ZjFmLTljMjMtYjFiZTZjMjVmNTRlOmU3NWJlNjVhLTk4YjAtNGY0Ni1iOWVhLTljMDkwZGE4YTk4MQ=="


def test_get_kwargs_with_max_connections() -> None:
    """Test that _get_kwargs properly configures max_connections"""
    settings = Settings(max_connections=5)
    kwargs = _get_kwargs(settings)

    assert "limits" in kwargs
    assert isinstance(kwargs["limits"], httpx.Limits)
    assert kwargs["limits"].max_connections == 5


def test_get_kwargs_without_max_connections() -> None:
    """Test that _get_kwargs works without max_connections"""
    settings = Settings()
    kwargs = _get_kwargs(settings)

    assert "limits" not in kwargs


def test_get_auth_kwargs_with_max_auth_connections() -> None:
    """Test that _get_auth_kwargs properly configures max_auth_connections"""
    settings = Settings(max_auth_connections=3)
    kwargs = _get_auth_kwargs(settings)

    assert "limits" in kwargs
    assert isinstance(kwargs["limits"], httpx.Limits)
    assert kwargs["limits"].max_connections == 3


def test_get_auth_kwargs_without_max_auth_connections() -> None:
    """Test that _get_auth_kwargs works without max_auth_connections"""
    settings = Settings()
    kwargs = _get_auth_kwargs(settings)

    assert "limits" not in kwargs


def test_sync_client_with_max_connections(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatSyncClient properly applies max_connections"""
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, max_connections=10) as client:
        assert client._settings.max_connections == 10
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


def test_sync_client_with_max_auth_connections(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatSyncClient properly applies max_auth_connections"""
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
        max_auth_connections=5,
    ) as client:
        assert client._settings.max_auth_connections == 5
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


def test_sync_client_with_both_connection_limits(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatSyncClient properly applies both connection limits"""
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
        max_connections=10,
        max_auth_connections=5,
    ) as client:
        assert client._settings.max_connections == 10
        assert client._settings.max_auth_connections == 5
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_async_client_with_max_connections(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatAsyncClient properly applies max_connections"""
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, max_connections=10) as client:
        assert client._settings.max_connections == 10
        response = await client.achat("test")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_async_client_with_max_auth_connections(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatAsyncClient properly applies max_auth_connections"""
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
        max_auth_connections=5,
    ) as client:
        assert client._settings.max_auth_connections == 5
        response = await client.achat("test")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_async_client_with_both_connection_limits(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatAsyncClient properly applies both connection limits"""
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
        max_connections=10,
        max_auth_connections=5,
    ) as client:
        assert client._settings.max_connections == 10
        assert client._settings.max_auth_connections == 5
        response = await client.achat("test")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_concurrent_requests_respect_max_connections(httpx_mock: HTTPXMock) -> None:
    """Test that concurrent requests respect max_connections limit"""
    for _ in range(20):
        httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, max_connections=5) as client:
        tasks: List[asyncio.Task[ChatCompletion]] = []
        for i in range(20):
            task = asyncio.create_task(client.achat(f"test {i}"))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

    assert len(responses) == 20
    assert all(isinstance(response, ChatCompletion) for response in responses)


def test_settings_from_env_max_connections(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that max_connections can be set via environment variable"""
    monkeypatch.setenv("GIGACHAT_MAX_CONNECTIONS", "15")
    settings = Settings()

    assert settings.max_connections == 15


def test_settings_from_env_max_auth_connections(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that max_auth_connections can be set via environment variable"""
    monkeypatch.setenv("GIGACHAT_MAX_AUTH_CONNECTIONS", "7")
    settings = Settings()

    assert settings.max_auth_connections == 7


def test_settings_from_env_both_connection_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that both connection limits can be set via environment variables"""
    monkeypatch.setenv("GIGACHAT_MAX_CONNECTIONS", "20")
    monkeypatch.setenv("GIGACHAT_MAX_AUTH_CONNECTIONS", "10")
    settings = Settings()

    assert settings.max_connections == 20
    assert settings.max_auth_connections == 10


def test_constructor_overrides_env_max_connections(monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock) -> None:
    """Test that constructor parameter overrides environment variable for max_connections"""
    monkeypatch.setenv("GIGACHAT_MAX_CONNECTIONS", "15")
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, max_connections=25) as client:
        assert client._settings.max_connections == 25
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


def test_constructor_overrides_env_max_auth_connections(monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock) -> None:
    """Test that constructor parameter overrides environment variable for max_auth_connections"""
    monkeypatch.setenv("GIGACHAT_MAX_AUTH_CONNECTIONS", "7")
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
        max_auth_connections=12,
    ) as client:
        assert client._settings.max_auth_connections == 12
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


def test_sync_429_retry_on_token_request(httpx_mock: HTTPXMock) -> None:
    """Test that 429 errors on token requests are retried with exponential backoff"""
    httpx_mock.add_response(url=TOKEN_URL, status_code=429, json={"status": 429, "message": "Too Many Requests"})
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        user="test_user",
        password="test_password",
    ) as client:
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


def test_sync_429_retry_on_oauth_request(httpx_mock: HTTPXMock) -> None:
    """Test that 429 errors on OAuth requests are retried with exponential backoff"""
    httpx_mock.add_response(url=AUTH_URL, status_code=429, json={"status": 429, "message": "Too Many Requests"})
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
    ) as client:
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


def test_sync_429_max_retries_exceeded(httpx_mock: HTTPXMock) -> None:
    """Test that 429 errors raise ResponseError after max retries"""
    for _ in range(3):
        httpx_mock.add_response(url=TOKEN_URL, status_code=429, json={"status": 429, "message": "Too Many Requests"})

    with GigaChatSyncClient(
        base_url=BASE_URL,
        user="test_user",
        password="test_password",
    ) as client:
        with pytest.raises(ResponseError) as exc_info:
            client.chat("test")

        assert exc_info.value.args[1] == 429


def test_sync_429_respects_retry_after_header(httpx_mock: HTTPXMock) -> None:
    """Test that 429 retry logic respects Retry-After header"""
    httpx_mock.add_response(
        url=TOKEN_URL,
        status_code=429,
        json={"status": 429, "message": "Too Many Requests"},
        headers={"Retry-After": "0.1"},
    )
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        user="test_user",
        password="test_password",
    ) as client:
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_async_429_retry_on_token_request(httpx_mock: HTTPXMock) -> None:
    """Test that 429 errors on async token requests are retried with exponential backoff"""
    httpx_mock.add_response(url=TOKEN_URL, status_code=429, json={"status": 429, "message": "Too Many Requests"})
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        user="test_user",
        password="test_password",
    ) as client:
        response = await client.achat("test")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_async_429_retry_on_oauth_request(httpx_mock: HTTPXMock) -> None:
    """Test that 429 errors on async OAuth requests are retried with exponential backoff"""
    httpx_mock.add_response(url=AUTH_URL, status_code=429, json={"status": 429, "message": "Too Many Requests"})
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
    ) as client:
        response = await client.achat("test")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_async_429_max_retries_exceeded(httpx_mock: HTTPXMock) -> None:
    """Test that 429 errors raise ResponseError after max retries in async"""
    for _ in range(3):
        httpx_mock.add_response(url=TOKEN_URL, status_code=429, json={"status": 429, "message": "Too Many Requests"})

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        user="test_user",
        password="test_password",
    ) as client:
        with pytest.raises(ResponseError) as exc_info:
            await client.achat("test")

        assert exc_info.value.args[1] == 429


def test_get_auth_kwargs_includes_base_url() -> None:
    """Test that _get_auth_kwargs includes base_url for token endpoint"""
    settings = Settings(base_url=BASE_URL)
    kwargs = _get_auth_kwargs(settings)

    assert "base_url" in kwargs
    assert kwargs["base_url"] == BASE_URL
