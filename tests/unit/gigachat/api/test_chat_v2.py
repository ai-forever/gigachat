import asyncio
import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import chat_v2
from gigachat.context import (
    agent_id_cvar,
    authorization_cvar,
    chat_v2_url_cvar,
    custom_headers_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
    trace_id_cvar,
)
from gigachat.models.chat_v2 import (
    ChatCompletionV2,
    ChatCompletionV2Chunk,
    ChatV2,
)
from tests.constants import (
    BASE_URL,
    CHAT_COMPLETION_V2,
    CHAT_COMPLETION_V2_STREAM,
    CHAT_V2,
    CHAT_V2_BASE_URL,
    CHAT_V2_URL,
    HEADERS_STREAM,
    X_CUSTOM_HEADER,
)


def test_resolve_chat_v2_url_from_standard_base_url() -> None:
    assert chat_v2.resolve_chat_v2_url(CHAT_V2_BASE_URL) == CHAT_V2_URL


def test_resolve_chat_v2_url_uses_absolute_override() -> None:
    token = chat_v2_url_cvar.set("https://override.example/api/v2/chat/completions")
    try:
        assert (
            chat_v2.resolve_chat_v2_url(CHAT_V2_BASE_URL)
            == "https://override.example/api/v2/chat/completions"
        )
    finally:
        chat_v2_url_cvar.reset(token)


def test_resolve_chat_v2_url_uses_path_override() -> None:
    token = chat_v2_url_cvar.set("/custom/api/v2/chat/completions")
    try:
        assert chat_v2.resolve_chat_v2_url(CHAT_V2_BASE_URL) == f"{BASE_URL}/custom/api/v2/chat/completions"
    finally:
        chat_v2_url_cvar.reset(token)


def test_resolve_chat_v2_url_invalid_base_url() -> None:
    with pytest.raises(ValueError, match="Cannot derive v2 chat URL"):
        chat_v2.resolve_chat_v2_url(BASE_URL)


def test_chat_v2_kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})
    token_chat_v2_url_cvar = chat_v2_url_cvar.set("/api/v2/chat/completions")

    try:
        assert chat_v2._get_chat_v2_kwargs(chat=ChatV2.model_validate(CHAT_V2), base_url=CHAT_V2_BASE_URL)
    finally:
        authorization_cvar.reset(token_authorization_cvar)
        request_id_cvar.reset(token_request_id_cvar)
        session_id_cvar.reset(token_session_id_cvar)
        service_id_cvar.reset(token_service_id_cvar)
        operation_id_cvar.reset(token_operation_id_cvar)
        trace_id_cvar.reset(token_trace_id_cvar)
        agent_id_cvar.reset(token_agent_id_cvar)
        custom_headers_cvar.reset(token_custom_headers_cvar)
        chat_v2_url_cvar.reset(token_chat_v2_url_cvar)


def test_chat_v2_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)

    with httpx.Client(base_url=CHAT_V2_BASE_URL) as client:
        response = chat_v2.chat_v2_sync(client, chat=ChatV2.model_validate(CHAT_V2), base_url=CHAT_V2_BASE_URL)

    assert isinstance(response, ChatCompletionV2)
    assert response.messages[0].content[0].text == "Вот ответ"


def test_chat_v2_sync_additional_fields_typed_precedence(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)

    chat_data = ChatV2.model_validate(CHAT_V2)
    chat_data.model = "typed-model"
    chat_data.additional_fields = {
        "model": "raw-model",
        "model_options": {"response_format": {"type": "text"}, "raw_nested_flag": True},
        "raw_top_level_flag": True,
    }

    with httpx.Client(base_url=CHAT_V2_BASE_URL) as client:
        chat_v2.chat_v2_sync(client, chat=chat_data, base_url=CHAT_V2_BASE_URL)

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["model"] == "typed-model"
    assert request_content["model_options"]["response_format"]["type"] == "json_schema"
    assert request_content["model_options"]["raw_nested_flag"] is True
    assert request_content["raw_top_level_flag"] is True


def test_chat_v2_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)
    token_custom_headers_cvar = custom_headers_cvar.set({X_CUSTOM_HEADER: "CustomValue"})

    try:
        with httpx.Client(base_url=CHAT_V2_BASE_URL) as client:
            chat_v2.chat_v2_sync(
                client,
                chat=ChatV2.model_validate(CHAT_V2),
                base_url=CHAT_V2_BASE_URL,
                access_token="access_token",
            )
    finally:
        custom_headers_cvar.reset(token_custom_headers_cvar)

    headers = httpx_mock.get_requests()[0].headers
    assert headers[X_CUSTOM_HEADER] == "CustomValue"


def test_stream_v2_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, content=CHAT_COMPLETION_V2_STREAM, headers=HEADERS_STREAM)

    with httpx.Client(base_url=CHAT_V2_BASE_URL) as client:
        response = list(chat_v2.stream_v2_sync(client, chat=ChatV2.model_validate(CHAT_V2), base_url=CHAT_V2_BASE_URL))

    assert len(response) == 2
    assert all(isinstance(chunk, ChatCompletionV2Chunk) for chunk in response)
    assert response[1].finish_reason == "stop"

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["stream"] is True


async def test_chat_v2_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)

    async with httpx.AsyncClient(base_url=CHAT_V2_BASE_URL) as client:
        response = await chat_v2.chat_v2_async(
            client, chat=ChatV2.model_validate(CHAT_V2), base_url=CHAT_V2_BASE_URL
        )

    assert isinstance(response, ChatCompletionV2)


async def test_stream_v2_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, content=CHAT_COMPLETION_V2_STREAM, headers=HEADERS_STREAM)

    async with httpx.AsyncClient(base_url=CHAT_V2_BASE_URL) as client:
        response = [chunk async for chunk in chat_v2.stream_v2_async(
            client,
            chat=ChatV2.model_validate(CHAT_V2),
            base_url=CHAT_V2_BASE_URL,
        )]

    assert len(response) == 2
    assert all(isinstance(chunk, ChatCompletionV2Chunk) for chunk in response)


async def test_headers_in_async_v2_request(httpx_mock: HTTPXMock) -> None:
    async def call_with_headers(client: httpx.AsyncClient, headers: dict[str, str]) -> None:
        token_custom_headers_cvar = custom_headers_cvar.set(headers)
        try:
            await chat_v2.chat_v2_async(client, chat=ChatV2.model_validate(CHAT_V2), base_url=CHAT_V2_BASE_URL)
        finally:
            custom_headers_cvar.reset(token_custom_headers_cvar)

    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)

    async with httpx.AsyncClient(base_url=CHAT_V2_BASE_URL) as client:
        await asyncio.gather(
            call_with_headers(client, {X_CUSTOM_HEADER: "CustomValue1"}),
            call_with_headers(client, {X_CUSTOM_HEADER: "CustomValue2"}),
        )

    header_values = [req.headers[X_CUSTOM_HEADER] for req in httpx_mock.get_requests()]
    assert sorted(header_values) == ["CustomValue1", "CustomValue2"]
