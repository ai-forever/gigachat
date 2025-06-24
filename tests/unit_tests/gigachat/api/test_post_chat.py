import asyncio

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import post_chat
from gigachat.api.utils import USER_AGENT
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
from gigachat.models import Chat, ChatCompletion

from ....utils import get_json

BASE_URL = "http://testserver/api"
MOCK_URL = f"{BASE_URL}/chat/completions"

CHAT = Chat.parse_obj(get_json("chat.json"))
CHAT_COMPLETION = get_json("chat_completion.json")

X_CUSTOM_HEADER = "X-Custom-Header"


def test__kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})

    assert post_chat._get_kwargs(chat=Chat(messages=[]))

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)
    trace_id_cvar.reset(token_trace_id_cvar)
    agent_id_cvar.reset(token_agent_id_cvar)
    custom_headers_cvar.reset(token_custom_headers_cvar)


def test_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = post_chat.sync(client, chat=CHAT)

    assert isinstance(response, ChatCompletion)


def test_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="5 validation errors for ChatCompletion*"):
            post_chat.sync(client, chat=CHAT)


def test_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            post_chat.sync(client, chat=CHAT)


def test_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            post_chat.sync(client, chat=CHAT)


def test_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = post_chat.sync(
            client,
            chat=CHAT,
            access_token="access_token",
        )

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await post_chat.asyncio(client, chat=CHAT)

    assert isinstance(response, ChatCompletion)


def test_headers_in_request(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)
    token_custom_headers_cvar = custom_headers_cvar.set({"X-Custom-Header": "CustomValue"})

    with httpx.Client(base_url=BASE_URL) as client:
        post_chat.sync(client, chat=CHAT)

    headers = httpx_mock.get_requests()[0].headers
    assert headers["User-Agent"] == USER_AGENT
    assert headers[X_CUSTOM_HEADER] == "CustomValue"

    custom_headers_cvar.reset(token_custom_headers_cvar)


@pytest.mark.asyncio()
async def test_headers_in_async_request(httpx_mock: HTTPXMock) -> None:
    async def call_with_headers(client: httpx.AsyncClient, headers: dict) -> None:
        token_custom_headers_cvar = custom_headers_cvar.set(headers)
        await post_chat.asyncio(client, chat=CHAT)
        custom_headers_cvar.reset(token_custom_headers_cvar)

    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await asyncio.gather(
            call_with_headers(client, {X_CUSTOM_HEADER: "CustomValue1"}),
            call_with_headers(client, {X_CUSTOM_HEADER: "CustomValue2"}),
            call_with_headers(client, {X_CUSTOM_HEADER: "CustomValue3"}),
        )

    # Verify that headers are not mixed up between concurrent requests
    requests = httpx_mock.get_requests()
    assert len(requests) == 3

    # Extract all header values
    header_values = [req.headers[X_CUSTOM_HEADER] for req in requests]
    expected_values = ["CustomValue1", "CustomValue2", "CustomValue3"]

    # Check that each expected value appears exactly once
    assert sorted(header_values) == sorted(expected_values)
