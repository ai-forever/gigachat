from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
import pytest

from gigachat import DefaultAioHttpClient, GigaChat, GigaChatAsyncClient
from gigachat.http_client import AsyncHttpClient
from gigachat.settings import Settings
from tests.constants import (
    AUTH_URL,
    BASE_URL,
    CHAT_COMPLETION,
    CHAT_COMPLETION_STREAM,
    CHAT_URL,
    CREDENTIALS,
    FILE,
    FILES,
    FILES_URL,
    HEADERS_STREAM,
    OAUTH_TOKEN_VALID,
)

try:
    import aiohttp
except ImportError:
    aiohttp = None


class DummyAsyncHttpClient:
    def __init__(self, response: Optional[httpx.Response] = None):
        self.response = response or httpx.Response(
            200,
            json=CHAT_COMPLETION,
            request=httpx.Request("POST", CHAT_URL),
        )
        self.closed = False

    async def request(self, **kwargs: Any) -> httpx.Response:
        return self.response

    def stream(self, **kwargs: Any) -> Any:
        raise AssertionError("stream() should not be called in this test")

    async def aclose(self) -> None:
        self.closed = True


class DummyAsyncHttpClientFactory:
    def __init__(self):
        self.client_calls: List[Settings] = []
        self.auth_client_calls: List[Settings] = []
        self.client = DummyAsyncHttpClient()
        self.auth_client = DummyAsyncHttpClient()

    def create_client(self, settings: Settings) -> AsyncHttpClient:
        self.client_calls.append(settings)
        return self.client

    def create_auth_client(self, settings: Settings) -> AsyncHttpClient:
        self.auth_client_calls.append(settings)
        return self.auth_client


class DummyAsyncStreamResponse:
    def __init__(
        self,
        *,
        status_code: int,
        url: str,
        body: bytes,
        headers: Optional[Dict[str, str]] = None,
        lines: Optional[List[str]] = None,
    ):
        self.status_code = status_code
        self.url = httpx.URL(url)
        self.headers = httpx.Headers(headers or {})
        self._body = body
        self._lines = list(lines or [])

    async def read(self) -> bytes:
        return self._body

    async def aread(self) -> bytes:
        return self._body

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line


class DummyAsyncStreamContext:
    def __init__(self, response: DummyAsyncStreamResponse):
        self._response = response

    async def __aenter__(self) -> DummyAsyncStreamResponse:
        return self._response

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None


def _default_backend_available() -> bool:
    return aiohttp is not None


def test_default_aiohttp_client_exported() -> None:
    assert DefaultAioHttpClient is not None


async def test_async_client_uses_http_client_factory() -> None:
    factory = DummyAsyncHttpClientFactory()

    async with GigaChatAsyncClient(base_url=BASE_URL, http_client=factory) as client:
        response = await client.achat("test")
        _ = client._auth_aclient

    assert response.choices[0].message.content == CHAT_COMPLETION["choices"][0]["message"]["content"]
    assert len(factory.client_calls) == 1
    assert len(factory.auth_client_calls) == 1
    assert factory.client.closed is True
    assert factory.auth_client.closed is True


def test_gigachat_accepts_http_client_factory() -> None:
    factory = DummyAsyncHttpClientFactory()
    client = GigaChat(base_url=BASE_URL, http_client=factory)
    assert client._http_client_factory is factory


def test_default_aiohttp_client_requires_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    import gigachat.http_client as http_client_module

    monkeypatch.setattr(http_client_module, "aiohttp", None)

    with pytest.raises(ImportError, match="aiohttp"):
        DefaultAioHttpClient().create_client(Settings())

async def test_default_aiohttp_client_uses_aiohttp_backend() -> None:
    if aiohttp is None:
        pytest.skip("aiohttp is not installed")

    aiohttp_client = DefaultAioHttpClient().create_client(Settings(base_url=BASE_URL))
    try:
        assert type(aiohttp_client).__name__ == "_AioHttpClient"
        request, _ = await aiohttp_client.build_aiohttp_request(
            {"method": "POST", "url": "/chat/completions", "content": "{}"}
        )
        assert request.url == httpx.URL(f"{BASE_URL}/chat/completions")
    finally:
        await aiohttp_client.aclose()


async def test_default_aiohttp_client_chat_request(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _default_backend_available():
        pytest.skip("DefaultAioHttpClient backend dependencies are not installed")

    calls: List[Dict[str, Any]] = []

    async def fake_request(self: Any, **kwargs: Any) -> httpx.Response:
        calls.append(kwargs)
        return httpx.Response(
            200,
            json=CHAT_COMPLETION,
            request=httpx.Request(kwargs["method"], CHAT_URL),
        )

    async with GigaChatAsyncClient(base_url=BASE_URL, http_client=DefaultAioHttpClient()) as client:
        monkeypatch.setattr(type(client._aclient), "request", fake_request)
        response = await client.achat("Say this is a test")

    assert response.choices[0].message.content == CHAT_COMPLETION["choices"][0]["message"]["content"]
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "/chat/completions"
    assert calls[0]["headers"]["Content-Type"] == "application/json"
    assert "Say this is a test" in calls[0]["content"]


async def test_default_aiohttp_client_auth_request(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _default_backend_available():
        pytest.skip("DefaultAioHttpClient backend dependencies are not installed")

    auth_calls: List[Dict[str, Any]] = []
    chat_calls: List[Dict[str, Any]] = []

    async def fake_request(self: Any, **kwargs: Any) -> httpx.Response:
        if kwargs["url"] == AUTH_URL:
            auth_calls.append(kwargs)
            return httpx.Response(
                200,
                json=OAUTH_TOKEN_VALID,
                request=httpx.Request(kwargs["method"], AUTH_URL),
            )

        chat_calls.append(kwargs)
        return httpx.Response(
            200,
            json=CHAT_COMPLETION,
            request=httpx.Request(kwargs["method"], CHAT_URL),
        )

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
        http_client=DefaultAioHttpClient(),
    ) as client:
        monkeypatch.setattr(type(client._aclient), "request", fake_request)
        await client.achat("test")

    assert auth_calls[0]["method"] == "POST"
    assert auth_calls[0]["url"] == AUTH_URL
    assert auth_calls[0]["headers"]["Authorization"].startswith("Basic ")
    assert chat_calls[0]["url"] == "/chat/completions"


async def test_default_aiohttp_client_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _default_backend_available():
        pytest.skip("DefaultAioHttpClient backend dependencies are not installed")

    calls: List[Dict[str, Any]] = []

    def fake_stream(self: Any, **kwargs: Any) -> DummyAsyncStreamContext:
        calls.append(kwargs)
        return DummyAsyncStreamContext(
            DummyAsyncStreamResponse(
                status_code=200,
                url=CHAT_URL,
                body=CHAT_COMPLETION_STREAM,
                headers=HEADERS_STREAM,
                lines=CHAT_COMPLETION_STREAM.decode("utf-8").splitlines(),
            )
        )

    async with GigaChatAsyncClient(base_url=BASE_URL, http_client=DefaultAioHttpClient()) as client:
        monkeypatch.setattr(type(client._aclient), "stream", fake_stream)
        chunks = [chunk async for chunk in client.astream("stream test")]

    assert len(chunks) > 0
    assert calls[0]["url"] == "/chat/completions"
    assert calls[0]["headers"]["Accept"] == "text/event-stream"
    assert '"stream": true' in calls[0]["content"]


async def test_default_aiohttp_client_upload_file(monkeypatch: pytest.MonkeyPatch) -> None:
    if not _default_backend_available():
        pytest.skip("DefaultAioHttpClient backend dependencies are not installed")

    calls: List[Dict[str, Any]] = []

    async def fake_request(self: Any, **kwargs: Any) -> httpx.Response:
        calls.append(kwargs)
        return httpx.Response(
            200,
            json=FILES,
            request=httpx.Request(kwargs["method"], FILES_URL),
        )

    async with GigaChatAsyncClient(base_url=BASE_URL, http_client=DefaultAioHttpClient()) as client:
        monkeypatch.setattr(type(client._aclient), "request", fake_request)
        response = await client.aupload_file(FILE)

    assert response.id_ == FILES["id"]
    assert calls[0]["url"] == "/files"
    assert calls[0]["data"] == {"purpose": "general"}
    assert "file" in calls[0]["files"]
