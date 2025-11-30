import asyncio

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient, _get_kwargs
from gigachat.models import ChatCompletion
from gigachat.settings import Settings
from tests.constants import (
    BASE_URL,
    CHAT_COMPLETION,
    CHAT_URL,
)


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


def test_sync_client_with_max_connections(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatSyncClient properly applies max_connections"""
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, max_connections=10) as client:
        assert client._settings.max_connections == 10
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)


async def test_async_client_with_max_connections(httpx_mock: HTTPXMock) -> None:
    """Test that GigaChatAsyncClient properly applies max_connections"""
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, max_connections=10) as client:
        assert client._settings.max_connections == 10
        response = await client.achat("test")

    assert isinstance(response, ChatCompletion)


async def test_concurrent_requests_respect_max_connections(httpx_mock: HTTPXMock) -> None:
    """Test that concurrent requests respect max_connections limit"""
    for _ in range(10):
        httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, max_connections=3) as client:
        tasks = [client.achat("test") for _ in range(10)]
        responses = await asyncio.gather(*tasks)

    assert len(responses) == 10
    assert all(isinstance(r, ChatCompletion) for r in responses)


def test_settings_from_env_max_connections(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that max_connections can be set via environment variable"""
    monkeypatch.setenv("GIGACHAT_MAX_CONNECTIONS", "7")
    settings = Settings()
    assert settings.max_connections == 7


def test_constructor_overrides_env_max_connections(monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock) -> None:
    """Test that constructor parameter overrides environment variable"""
    monkeypatch.setenv("GIGACHAT_MAX_CONNECTIONS", "5")
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, max_connections=10) as client:
        assert client._settings.max_connections == 10
        response = client.chat("test")

    assert isinstance(response, ChatCompletion)
