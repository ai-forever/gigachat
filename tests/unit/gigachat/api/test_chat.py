import asyncio
import json
import logging
from copy import deepcopy
from typing import Any, Dict, Optional

import httpx
import pytest
from pydantic import BaseModel, ConfigDict
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
from gigachat.models import Chat, ChatCompletion, ChatCompletionChunk
from gigachat.models.chat import Function, Messages, MessagesRole
from gigachat.models.response_format import JsonSchemaResponseFormat
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

SAMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {"type": "array", "items": {"type": "string"}},
        "final_answer": {"type": "string"},
    },
    "required": ["steps", "final_answer"],
}


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

    with httpx.Client(base_url=BASE_URL) as client:
        assert chat._get_chat_kwargs(client, chat=Chat(messages=[]))

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

    with httpx.Client(base_url=BASE_URL) as client:
        assert chat._get_stream_kwargs(client, chat=Chat(messages=[]))

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
    """Test that response_format is preserved when additional_fields are used."""
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hello")],
        response_format=JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=True),
        additional_fields={"extra": "val"},
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    assert request_content["extra"] == "val"
    assert request_content["response_format"]["type"] == "json_schema"
    assert request_content["response_format"]["schema"] == SAMPLE_SCHEMA
    assert request_content["response_format"]["strict"] is True


def test_chat_sync_preserves_function_json_schema(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)
    parameters = {
        "$defs": {"value": {"type": ["string", "null"]}},
        "type": "object",
        "properties": {
            "value": {"$ref": "#/$defs/value"},
            "choice": {"anyOf": [{"const": "automatic"}, {"enum": [1, True, None]}]},
            "anything": True,
            "forbidden": False,
        },
        "unevaluatedProperties": False,
    }
    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="choose a value")],
        functions=[Function(name="choose", parameters=parameters)],
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)

    request_content = json.loads(httpx_mock.get_requests()[0].content.decode("utf-8"))
    assert request_content["functions"][0]["parameters"] == parameters


@pytest.mark.parametrize("async_mode", [False, True])
async def test_chat_preserves_flat_pydantic_function_schema(httpx_mock: HTTPXMock, async_mode: bool) -> None:
    class Place(BaseModel):
        city: str

        model_config = ConfigDict(extra="forbid")

    class Weather(BaseModel):
        """Look up the weather."""

        place: Place
        units: Optional[str] = None

        model_config = ConfigDict(extra="forbid")

    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)
    schema = Weather.model_json_schema()
    expected_parameters = deepcopy(schema)
    name = expected_parameters.pop("title")
    description = expected_parameters.pop("description")
    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="Weather in Paris")],
        functions=[Function.model_validate(schema)],
    )

    if async_mode:
        async with httpx.AsyncClient(base_url=BASE_URL) as async_client:
            await chat.chat_async(async_client, chat=chat_data)
    else:
        with httpx.Client(base_url=BASE_URL) as client:
            chat.chat_sync(client, chat=chat_data)

    request_content = json.loads(httpx_mock.get_requests()[0].content.decode("utf-8"))
    assert request_content["functions"] == [
        {"name": name, "description": description, "parameters": expected_parameters}
    ]


def test_chat_sync_response_format_json_schema(httpx_mock: HTTPXMock) -> None:
    """Test that response_format with JSON schema is sent correctly."""
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="solve 2+2")],
        response_format=JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=False),
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    response_format = request_content["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["schema"] == SAMPLE_SCHEMA
    assert response_format["strict"] is False


def test_chat_sync_response_format_dict_passthrough(httpx_mock: HTTPXMock) -> None:
    """Test that a dict response_format is sent as-is."""
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    raw_rf = {"type": "json_schema", "schema": SAMPLE_SCHEMA, "strict": True}
    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="solve 2+2")],
        response_format=raw_rf,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chat.chat_sync(client, chat=chat_data)

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    response_format = request_content["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["schema"] == SAMPLE_SCHEMA


def test_stream_sync_response_format_json_schema(httpx_mock: HTTPXMock) -> None:
    """Test that streaming request includes response_format."""
    httpx_mock.add_response(url=MOCK_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    chat_data = Chat(
        messages=[Messages(role=MessagesRole.USER, content="solve 2+2")],
        response_format=JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=True),
    )

    with httpx.Client(base_url=BASE_URL) as client:
        list(chat.stream_sync(client, chat=chat_data))

    requests = httpx_mock.get_requests()
    request_content = json.loads(requests[0].content.decode("utf-8"))
    response_format = request_content["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["schema"] == SAMPLE_SCHEMA
    assert response_format["strict"] is True


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


@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_chat_contract_fields_cross_http_boundary(
    httpx_mock: HTTPXMock, streaming: bool, asynchronous: bool
) -> None:
    request_data: Dict[str, Any] = {
        "assistant_id": "assistant-1",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "function_call": {"id": "call-1", "name": "lookup", "arguments": {"value": None}},
                "inline_data": {"sources": [{"source-1": {"url": "https://example.com"}}]},
            }
        ],
        "preset": "example-preset",
        "filters_settings": {
            "default": {
                "request_content": {"neuro": False, "blacklist": True, "whitelist": False},
                "response_content": {"blacklist": True},
                "components": {"rephraser": False, "screpish": True, "whitelist_rag": False},
            }
        },
        "reasoning_max_tokens": 32,
        "unnormalized_history": False,
        "top_logprobs": 1,
        "additional_data": {
            "giga_rag": {"site_id": "example"},
            "features": {
                "embedder_model": "example-embedder",
                "sp_indexes": ["index"],
                "sp_flags": [],
                "ignored_functions": ["skip"],
            },
            "user_info": {"current_time": 1},
        },
        "function_registry": {},
        "storage": {"is_stateful": True, "metadata": {}},
    }
    message_data = {
        "role": "assistant",
        "content": "ok",
        "inline_data": {"widgets": [{"kind": "example", "payload": {"value": None}}]},
        "logprobs": [
            {
                "chosen": {"token": "ok", "token_id": 1, "logprob": -0.2},
                "top": [{"token": "ok", "token_id": 1, "logprob": -0.2}],
            }
        ],
    }
    response_data = {
        "choices": [{"index": 0, "delta" if streaming else "message": message_data, "finish_reason": "stop"}],
        "created": 1,
        "model": "example-model",
        "object": "chat.completion.chunk" if streaming else "chat.completion",
        "thread_id": "thread-1",
        "message_id": "message-1",
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2, "precached_prompt_tokens": 0},
        "additional_data": {
            "sources": {"source-1": {"title": "Example", "url": "https://example.com"}},
            "execution_steps": [{"step": "example"}],
        },
    }
    if streaming:
        httpx_mock.add_response(
            url=MOCK_URL,
            content=("data: " + json.dumps(response_data) + "\n\ndata: [DONE]\n\n").encode(),
            headers=HEADERS_STREAM,
        )
    else:
        httpx_mock.add_response(url=MOCK_URL, json=response_data)
    advanced_names = {
        "preset",
        "filters_settings",
        "unnormalized_history",
        "top_logprobs",
        "additional_data",
        "function_registry",
    }
    chat_data = Chat.model_validate(
        {
            **{key: value for key, value in request_data.items() if key not in advanced_names},
            "additional_fields": {key: value for key, value in request_data.items() if key in advanced_names},
        }
    )
    assert chat_data.additional_fields is not None
    chat_data.additional_fields["stream"] = not streaming
    if asynchronous:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            if streaming:
                responses = [chunk async for chunk in chat.stream_async(client, chat=chat_data)]
                response_dump = responses[0].model_dump(exclude_none=True, by_alias=True, exclude={"x_headers"})
            else:
                response = await chat.chat_async(client, chat=chat_data)
                response_dump = response.model_dump(exclude_none=True, by_alias=True, exclude={"x_headers"})
    else:
        with httpx.Client(base_url=BASE_URL) as sync_client:
            if streaming:
                responses = list(chat.stream_sync(sync_client, chat=chat_data))
                response_dump = responses[0].model_dump(exclude_none=True, by_alias=True, exclude={"x_headers"})
            else:
                response = chat.chat_sync(sync_client, chat=chat_data)
                response_dump = response.model_dump(exclude_none=True, by_alias=True, exclude={"x_headers"})

    expected_request = {**request_data, "stream": True} if streaming else request_data
    assert json.loads(httpx_mock.get_requests()[0].content) == expected_request
    assert response_dump == response_data


@pytest.mark.parametrize("registry", [None, {}, {"profile": "example", "labels": [], "ab_flags": {}}])
def test_function_registry_preserves_disabled_and_default_selection(registry: Any) -> None:
    request = chat._build_request_json(Chat(messages=[], additional_fields={"function_registry": registry}))

    assert request["function_registry"] == registry


def test_explicit_chat_fields_override_additional_fields() -> None:
    request = chat._build_request_json(
        Chat(messages=[], max_tokens=10, additional_fields={"max_tokens": 50, "custom_option": True})
    )

    assert request["max_tokens"] == 10
    assert request["custom_option"] is True
