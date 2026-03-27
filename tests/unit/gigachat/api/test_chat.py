import asyncio
import json
import logging
from typing import Dict

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import chat
from gigachat.api.utils import USER_AGENT
from gigachat.context import (
    agent_id_cvar,
    authorization_cvar,
    chat_url_cvar,
    custom_headers_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
    trace_id_cvar,
)
from gigachat.exceptions import AuthenticationError, BadRequestError
from gigachat.models import Chat, ChatCompletion, ChatCompletionChunk, Messages, MessagesRole
from tests.constants import (
    BASE_URL,
    CHAT,
    CHAT_COMPLETION,
    CHAT_COMPLETION_STREAM,
    HEADERS_STREAM,
    MOCK_URL,
    X_CUSTOM_HEADER,
)
from tests.utils import get_json


def test_chat_kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})
    token_chat_url_cvar = chat_url_cvar.set("/chat/completions")

    assert chat._get_chat_kwargs(chat=Chat(messages=[]))

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)
    trace_id_cvar.reset(token_trace_id_cvar)
    agent_id_cvar.reset(token_agent_id_cvar)
    custom_headers_cvar.reset(token_custom_headers_cvar)
    chat_url_cvar.reset(token_chat_url_cvar)


def test_stream_kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})
    token_chat_url_cvar = chat_url_cvar.set("/chat/completions")

    assert chat._get_stream_kwargs(chat=Chat(messages=[]))

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)
    trace_id_cvar.reset(token_trace_id_cvar)
    agent_id_cvar.reset(token_agent_id_cvar)
    custom_headers_cvar.reset(token_custom_headers_cvar)
    chat_url_cvar.reset(token_chat_url_cvar)


def test_chat_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = chat.chat_sync(client, chat=CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_sync_additional_fields(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    json_data = get_json("chat.json")
    json_data["additional_fields"] = {"additional_field": "val"}
    chat_data = Chat.model_validate(json_data)

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)
    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["additional_field"] == "val"


def test_chat_sync_additional_fields_passthrough_preset(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        additional_fields={"preset": "my-preset"},
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["preset"] == "my-preset"


def test_chat_sync_sanitizes_lone_surrogates(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="broken \udcd0 text")],
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["messages"][0]["content"] == r"broken \udcd0 text"


def test_chat_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="5 validation errors for ChatCompletion*"):
            chat.chat_sync(client, chat=CHAT)


def test_chat_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            chat.chat_sync(client, chat=CHAT)


def test_chat_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(BadRequestError) as exc_info:
            chat.chat_sync(client, chat=CHAT)

    assert exc_info.value.status_code == 400
    assert str(exc_info.value.url) == MOCK_URL


def test_chat_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = chat.chat_sync(
            client,
            chat=CHAT,
            access_token="access_token",
        )

    assert isinstance(response, ChatCompletion)


async def test_chat_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await chat.chat_async(client, chat=CHAT)

    assert isinstance(response, ChatCompletion)


async def test_chat_async_additional_fields(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    json_data = get_json("chat.json")
    json_data["additional_fields"] = {"additional_field": "val"}
    chat_data = Chat.model_validate(json_data)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await chat.chat_async(client, chat=chat_data)
    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["additional_field"] == "val"


def test_headers_in_request(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)
    token_custom_headers_cvar = custom_headers_cvar.set({"X-Custom-Header": "CustomValue"})

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=CHAT)

    headers = httpx_mock.get_requests()[0].headers
    assert headers["User-Agent"] == USER_AGENT
    assert headers[X_CUSTOM_HEADER] == "CustomValue"

    custom_headers_cvar.reset(token_custom_headers_cvar)


async def test_headers_in_async_request(httpx_mock: HTTPXMock) -> None:
    async def call_with_headers(client: httpx.AsyncClient, headers: Dict[str, str]) -> None:
        token_custom_headers_cvar = custom_headers_cvar.set(headers)
        await chat.chat_async(client, chat=CHAT)
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


def test_stream_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(chat.stream_sync(client, chat=CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_sync_additional_fields(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    json_data = get_json("chat.json")
    json_data["additional_fields"] = {"additional_field": "val"}
    chat_data = Chat.model_validate(json_data)

    with httpx.Client(base_url=BASE_URL) as client:
        list(chat.stream_sync(client, chat=chat_data))

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["additional_field"] == "val"


def test_stream_sync_sanitizes_lone_surrogates(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="broken \udcd0 text")],
    )

    with httpx.Client(base_url=BASE_URL) as client:
        list(chat.stream_sync(client, chat=chat_data))

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["messages"][0]["content"] == r"broken \udcd0 text"


def test_stream_sync_content_type_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(httpx.TransportError):
            list(chat.stream_sync(client, chat=CHAT))


def test_stream_sync_value_error(caplog: pytest.LogCaptureFixture, httpx_mock: HTTPXMock) -> None:
    caplog.set_level(logging.WARNING)

    httpx_mock.add_response(url=MOCK_URL, content=b'data: {"error": 500}', headers=HEADERS_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="4 validation errors for ChatCompletionChunk*"):
            list(chat.stream_sync(client, chat=CHAT))

    assert '"error": 500' in caplog.text


def test_stream_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            list(chat.stream_sync(client, chat=CHAT))


def test_stream_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(BadRequestError) as exc_info:
            list(chat.stream_sync(client, chat=CHAT))

    assert exc_info.value.status_code == 400
    assert str(exc_info.value.url) == MOCK_URL


def test_stream_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(
            chat.stream_sync(
                client,
                chat=CHAT,
                access_token="access_token",
            )
        )

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


async def test_stream_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = [chunk async for chunk in chat.stream_async(client, chat=CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


async def test_stream_async_additional_fields(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    json_data = get_json("chat.json")
    json_data["additional_fields"] = {"additional_field": "val"}
    chat_data = Chat.model_validate(json_data)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        async for _chunk in chat.stream_async(client, chat=chat_data):
            pass

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["additional_field"] == "val"


def test_chat_sync_function_ranker_top_logprobs_and_unnormalized_history(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    chat_data = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        function_ranker={"enabled": True, "top_n": 3},
        top_logprobs=2,
        unnormalized_history=True,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["function_ranker"] == {"enabled": True, "top_n": 3}
    assert request_content["top_logprobs"] == 2
    assert request_content["unnormalized_history"] is True


def test_stream_sync_function_ranker_top_logprobs_and_unnormalized_history(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    chat_data = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        function_ranker={"enabled": True, "top_n": 3},
        top_logprobs=2,
        unnormalized_history=True,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        list(chat.stream_sync(client, chat=chat_data))

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["function_ranker"] == {"enabled": True, "top_n": 3}
    assert request_content["top_logprobs"] == 2
    assert request_content["unnormalized_history"] is True
