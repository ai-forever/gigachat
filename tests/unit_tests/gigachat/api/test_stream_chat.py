import logging

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import stream_chat
from gigachat.context import (
    agent_id_cvar,
    authorization_cvar,
    custom_headers_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
    trace_id_cvar,
)
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Chat, ChatCompletionChunk

from ....utils import get_bytes, get_json

BASE_URL = "http://testserver/api"
MOCK_URL = f"{BASE_URL}/chat/completions"

CHAT = Chat.parse_obj(get_json("chat.json"))
CHAT_COMPLETION_STREAM = get_bytes("chat_completion.stream")
HEADERS_STREAM = {"Content-Type": "text/event-stream"}

logger = logging.getLogger(__name__)


def test__kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})

    assert stream_chat._get_kwargs(chat=Chat(messages=[]))

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)
    trace_id_cvar.reset(token_trace_id_cvar)
    agent_id_cvar.reset(token_agent_id_cvar)
    custom_headers_cvar.reset(token_custom_headers_cvar)


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


def test_sync_value_error(caplog: pytest.LogCaptureFixture, httpx_mock: HTTPXMock) -> None:
    caplog.set_level(logging.WARNING)

    httpx_mock.add_response(url=MOCK_URL, content=b'data: {"error": 500}', headers=HEADERS_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="4 validation errors for ChatCompletionChunk*"):
            list(stream_chat.sync(client, chat=CHAT))

    assert '"error": 500' in caplog.text


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
