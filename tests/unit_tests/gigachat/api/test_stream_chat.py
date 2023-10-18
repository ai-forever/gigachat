import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import stream_chat
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Chat, ChatCompletionChunk

from ....utils import get_bytes, get_json

BASE_URL = "http://testserver/api"
MOCK_URL = f"{BASE_URL}/chat/completions"

CHAT = Chat.parse_obj(get_json("chat.json"))
CHAT_COMPLETION_STREAM = get_bytes("chat_completion.stream")
HEADERS_STREAM = {"Content-Type": "text/event-stream"}


def test_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(stream_chat.sync(client, chat=CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_sync_content_type_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(httpx.TransportError):
            list(stream_chat.sync(client, chat=CHAT))


def test_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=b"data: {}", headers=HEADERS_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="4 validation errors for ChatCompletionChunk*"):
            list(stream_chat.sync(client, chat=CHAT))


def test_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            list(stream_chat.sync(client, chat=CHAT))


def test_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            list(stream_chat.sync(client, chat=CHAT))


def test_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(
            stream_chat.sync(
                client,
                chat=CHAT,
                access_token="access_token",
                client_id="client_id",
                session_id="session_id",
                request_id="request_id",
            )
        )

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = [chunk async for chunk in stream_chat.asyncio(client, chat=CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"
