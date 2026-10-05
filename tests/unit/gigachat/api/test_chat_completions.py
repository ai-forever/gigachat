import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import chat_completions
from gigachat.context import chat_completions_url_cvar
from gigachat.models.chat_completions import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatFilterConfig,
    ChatFunctionSpecification,
    ChatMessage,
    ChatModelOptions,
    ChatStorage,
    ChatTool,
)
from tests.constants import BASE_URL, HEADERS_STREAM, MOCK_URL


@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_additional_fields_cross_http_boundary(
    httpx_mock: HTTPXMock, streaming: bool, asynchronous: bool
) -> None:
    extras = {
        "model": "overridden",
        "stream": not streaming,
        "function_registry": {},
        "filter_config": {"components": {"rephraser": False}},
        "vendor_metadata": {"optional": None},
    }
    payload = ChatCompletionRequest(messages=[], model="explicit-model", additional_fields=extras)
    if streaming:
        httpx_mock.add_response(
            url=MOCK_URL, content=b'data: {"messages": []}\n\ndata: [DONE]\n\n', headers=HEADERS_STREAM
        )
    else:
        httpx_mock.add_response(url=MOCK_URL, json={"messages": []})
    if asynchronous:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            if streaming:
                assert len([chunk async for chunk in chat_completions.stream_async(client, chat=payload)]) == 1
            else:
                await chat_completions.chat_async(client, chat=payload)
    else:
        with httpx.Client(base_url=BASE_URL) as sync_client:
            if streaming:
                assert len(list(chat_completions.stream_sync(sync_client, chat=payload))) == 1
            else:
                chat_completions.chat_sync(sync_client, chat=payload)
    body = json.loads(httpx_mock.get_requests()[0].content)
    expected = {**extras, "model": "explicit-model", "messages": []}
    if streaming:
        expected["stream"] = True
    else:
        expected.pop("stream")
    assert body == expected
    assert extras["model"] == "overridden"
    assert extras["stream"] is not streaming


def test_additional_fields_merge_is_shallow_and_nested_extras_are_preserved() -> None:
    payload = ChatCompletionRequest(
        messages=[],
        model_options=ChatModelOptions(max_tokens=16, preset="example"),
        tools=[ChatTool(web_search={"preset": "example"})],
        additional_fields={
            "model_options": {"max_tokens": 99},
            "function_registry": None,
            "filter_config": ChatFilterConfig(),
        },
    )
    assert chat_completions._build_request_json(payload) == {
        "messages": [],
        "model_options": {"max_tokens": 16, "preset": "example"},
        "tools": [{"web_search": {"preset": "example"}}],
        "function_registry": None,
        "filter_config": {},
    }


PRIMARY_CHAT_COMPLETION_STREAM = (
    b"event: response.message.delta\n"
    b'data: {"model":"GigaChat-2-Max","created_at":1760434637,'
    b'"messages":[{"role":"assistant","content":"primary chunk"}]}\n\n'
    b"event: response.message.done\n"
    b'data: {"model":"GigaChat-2-Max","created_at":1760434638,"finish_reason":"stop"}\n\n'
)

PRIMARY_CHAT_COMPLETION_EVENT_STREAM = (
    b"event: response.message.delta\n"
    b'data: {"model":"GigaChat","created_at":"167890456789",'
    b'"messages":[{"role":"assistant","content":"primary chunk"}]}\n\n'
    b"event: response.tool.completed\n"
    b'data: {"model":"GigaChat","created_at":"167890456790",'
    b'"messages":[{"role":"reasoning","content":[{"tool_execution":'
    b'{"name":"image_generate","status":"success","censored":true}}]}]}\n\n'
    b"event: response.message.done\n"
    b'data: {"model":"GigaChat","created_at":"167890456791","finish_reason":"error",'
    b'"tools_state_id":"tools-state-1","usage":{"input_tokens":1,'
    b'"input_tokens_details":{"prompt_tokens":1,"cached_tokens":0},'
    b'"output_tokens":2,"total_tokens":3}}\n\n'
)


def test_get_stream_kwargs_sets_primary_stream_payload() -> None:
    chat_data = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="solve 2+2")],
        stream=False,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        kwargs = chat_completions._get_stream_kwargs(client, chat=chat_data, access_token="access_token")
        request_content = json.loads(kwargs["content"])

    assert kwargs["url"] == "/chat/completions"
    assert kwargs["headers"]["Accept"] == "text/event-stream"
    assert kwargs["headers"]["Cache-Control"] == "no-store"
    assert kwargs["headers"]["Authorization"] == "Bearer access_token"
    assert request_content["stream"] is True
    assert request_content["messages"][0]["content"] == [{"text": "solve 2+2"}]


def test_build_request_json_maps_profanity_check_to_disable_filter() -> None:
    chat_data = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="solve 2+2")],
        profanity_check=False,
    )

    request_content = chat_completions._build_request_json(chat_data)

    assert request_content["disable_filter"] is True
    assert "profanity_check" not in request_content


def test_build_request_json_maps_storage_true_to_object() -> None:
    chat_data = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="solve 2+2")],
        storage=True,
    )

    request_content = chat_completions._build_request_json(chat_data)

    assert request_content["storage"] == {}


def test_build_request_json_omits_storage_when_false() -> None:
    chat_data = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="solve 2+2")],
        storage=False,
    )

    request_content = chat_completions._build_request_json(chat_data)

    assert "storage" not in request_content


def test_build_request_json_keeps_storage_object() -> None:
    chat_data = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="solve 2+2")],
        storage=ChatStorage(thread_id="thread-1", limit=10),
    )

    request_content = chat_completions._build_request_json(chat_data)

    assert request_content["storage"] == {"thread_id": "thread-1", "limit": 10}


def test_build_request_json_keeps_parallel_tool_calls_in_model_options() -> None:
    chat_data = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="call both functions")],
        model_options=ChatModelOptions(parallel_tool_calls=True),
    )

    request_content = chat_completions._build_request_json(chat_data)

    assert request_content["model_options"] == {"parallel_tool_calls": True}
    assert "parallel_tool_calls" not in request_content


def test_build_request_json_preserves_function_json_schema() -> None:
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
    chat_data = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="choose a value")],
        tools=[
            ChatTool(
                functions={
                    "specifications": [ChatFunctionSpecification(name="choose", parameters=parameters)],
                }
            )
        ],
    )

    request_content = chat_completions._build_request_json(chat_data)
    functions = request_content["tools"][0]["functions"]

    assert functions["specifications"][0]["parameters"] == parameters


def test_stream_sync_parses_primary_chunk(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=PRIMARY_CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(chat_completions.stream_sync(client, chat=chat_data))

    assert len(response) == 2
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[0].event == "response.message.delta"
    assert response[0].messages is not None
    assert response[0].messages[0].content is not None
    assert response[0].messages[0].content[0].text == "primary chunk"
    assert response[1].event == "response.message.done"
    assert response[1].finish_reason == "stop"


async def test_stream_async_parses_primary_chunk(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=PRIMARY_CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = [chunk async for chunk in chat_completions.stream_async(client, chat=chat_data)]

    assert len(response) == 2
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[0].event == "response.message.delta"
    assert response[0].messages is not None
    assert response[0].messages[0].content is not None
    assert response[0].messages[0].content[0].text == "primary chunk"
    assert response[1].event == "response.message.done"
    assert response[1].finish_reason == "stop"


def test_stream_sync_parses_named_sse_events_without_done_marker(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=PRIMARY_CHAT_COMPLETION_EVENT_STREAM, headers=HEADERS_STREAM)
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(chat_completions.stream_sync(client, chat=chat_data))

    assert len(response) == 3
    assert response[0].event == "response.message.delta"
    assert response[0].messages is not None
    assert response[0].messages[0].content is not None
    assert response[0].messages[0].content[0].text == "primary chunk"
    assert response[1].event == "response.tool.completed"
    assert response[1].messages is not None
    assert response[1].messages[0].content is not None
    assert response[1].messages[0].content[0].tool_execution is not None
    assert response[1].messages[0].content[0].tool_execution.name == "image_generate"
    assert response[1].messages[0].content[0].tool_execution.status == "success"
    assert response[1].messages[0].content[0].tool_execution.censored is True
    assert response[2].event == "response.message.done"
    assert response[2].finish_reason == "error"
    assert response[2].tools_state_id == "tools-state-1"
    assert response[2].usage is not None
    assert response[2].usage.input_tokens_details is not None
    assert response[2].usage.input_tokens_details.prompt_tokens == 1
    assert response[2].usage.input_tokens_details.cached_tokens == 0


async def test_stream_async_parses_named_sse_events_without_done_marker(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=PRIMARY_CHAT_COMPLETION_EVENT_STREAM, headers=HEADERS_STREAM)
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = [chunk async for chunk in chat_completions.stream_async(client, chat=chat_data)]

    assert len(response) == 3
    assert response[0].event == "response.message.delta"
    assert response[1].event == "response.tool.completed"
    assert response[2].event == "response.message.done"
    assert response[2].finish_reason == "error"


def test_chat_sync_supports_versioned_primary_path_override(httpx_mock: HTTPXMock) -> None:
    versioned_base_url = "https://host/api/v1"
    versioned_path = "/v2/chat/completions"
    token = chat_completions_url_cvar.set(versioned_path)
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])

    try:
        httpx_mock.add_response(url="https://host/v2/chat/completions", json={"messages": []})

        with httpx.Client(base_url=versioned_base_url) as client:
            chat_completions.chat_sync(client, chat=chat_data)
    finally:
        chat_completions_url_cvar.reset(token)

    request = httpx_mock.get_requests()[0]
    assert str(request.url) == "https://host/v2/chat/completions"


async def test_chat_async_supports_versioned_primary_path_override(httpx_mock: HTTPXMock) -> None:
    versioned_base_url = "https://host/api/v1"
    versioned_path = "/v2/chat/completions"
    token = chat_completions_url_cvar.set(versioned_path)
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])

    try:
        httpx_mock.add_response(url="https://host/v2/chat/completions", json={"messages": []})

        async with httpx.AsyncClient(base_url=versioned_base_url) as client:
            await chat_completions.chat_async(client, chat=chat_data)
    finally:
        chat_completions_url_cvar.reset(token)

    request = httpx_mock.get_requests()[0]
    assert str(request.url) == "https://host/v2/chat/completions"


def test_chat_sync_uses_v2_primary_route_for_legacy_v1_base_url(httpx_mock: HTTPXMock) -> None:
    versioned_base_url = "https://host/api/v1"
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])
    httpx_mock.add_response(url="https://host/api/v2/chat/completions", json={"messages": []})

    with httpx.Client(base_url=versioned_base_url) as client:
        chat_completions.chat_sync(client, chat=chat_data)

    request = httpx_mock.get_requests()[0]
    assert str(request.url) == "https://host/api/v2/chat/completions"


async def test_chat_async_uses_v2_primary_route_for_legacy_v1_base_url(httpx_mock: HTTPXMock) -> None:
    versioned_base_url = "https://host/api/v1"
    chat_data = ChatCompletionRequest(messages=[ChatMessage(role="user", content="solve 2+2")])
    httpx_mock.add_response(url="https://host/api/v2/chat/completions", json={"messages": []})

    async with httpx.AsyncClient(base_url=versioned_base_url) as client:
        await chat_completions.chat_async(client, chat=chat_data)

    request = httpx_mock.get_requests()[0]
    assert str(request.url) == "https://host/api/v2/chat/completions"


def test_build_request_json_nests_all_generation_options() -> None:
    options = {
        "preset": "example",
        "temperature": 0,
        "top_p": 0.5,
        "max_tokens": 10,
        "repetition_penalty": 1.0,
        "update_interval": 0,
        "unnormalized_history": False,
        "top_logprobs": 2,
        "parallel_tool_calls": False,
        "reasoning": {"effort": "medium", "max_tokens": 5},
        "response_format": {"type": "text"},
    }
    chat = ChatCompletionRequest.model_validate({"messages": [], **options})

    assert chat_completions._build_request_json(chat) == {"messages": [], "model_options": options}


def test_chat_sync_reads_object_metadata_and_sends_nested_token_limit(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=MOCK_URL,
        json={"messages": [], "additional_data": {"execution_steps": [{"name": "test"}]}},
    )
    chat = ChatCompletionRequest.model_validate({"messages": [], "max_tokens": 10})

    with httpx.Client(base_url=BASE_URL) as client:
        response = chat_completions.chat_sync(client, chat=chat)

    assert response.model_dump(exclude_none=True)["additional_data"] == {"execution_steps": [{"name": "test"}]}
    assert json.loads(httpx_mock.get_requests()[0].content) == {"messages": [], "model_options": {"max_tokens": 10}}


async def test_chat_async_reads_object_metadata_and_sends_nested_token_limit(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=MOCK_URL,
        json={"messages": [], "additional_data": {"execution_steps": [{"name": "test"}]}},
    )
    chat = ChatCompletionRequest.model_validate({"messages": [], "max_tokens": 10})

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await chat_completions.chat_async(client, chat=chat)

    assert response.model_dump(exclude_none=True)["additional_data"] == {"execution_steps": [{"name": "test"}]}
    assert json.loads(httpx_mock.get_requests()[0].content) == {"messages": [], "model_options": {"max_tokens": 10}}


CONTRACT_COMPLETION_STREAM = (
    b"event: response.message.delta\n"
    b'data: {"messages":[{"role":"assistant","content":[{"text":"ok",'
    b'"logprobs":[{"chosen":{"token":"ok","token_id":7,"logprob":-0.1}}]}]}]}\n\n'
    b"event: response.message.done\n"
    b'data: {"finish_reason":"error","additional_data":{"execution_steps":[]},'
    b'"error_details":{"http_status":500,"user_message":"Try again"}}\n\n'
    b"data: [DONE]\n\n"
)


def test_stream_sync_parses_contract_metadata(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CONTRACT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    chat = ChatCompletionRequest(messages=[])

    with httpx.Client(base_url=BASE_URL) as client:
        chunks = list(chat_completions.stream_sync(client, chat=chat))

    assert len(chunks) == 2
    assert chunks[0].messages is not None
    assert chunks[0].messages[0].content is not None
    assert chunks[0].messages[0].content[0].logprobs is not None
    assert chunks[0].messages[0].content[0].logprobs[0].chosen is not None
    assert chunks[0].messages[0].content[0].logprobs[0].chosen.token_id == 7
    assert chunks[1].error_details is not None
    assert chunks[1].error_details["http_status"] == 500
    assert chunks[1].model_dump(exclude_none=True)["additional_data"] == {"execution_steps": []}


async def test_stream_async_parses_contract_metadata(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, content=CONTRACT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    chat = ChatCompletionRequest(messages=[])

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        chunks = [chunk async for chunk in chat_completions.stream_async(client, chat=chat)]

    assert len(chunks) == 2
    assert (
        chunks[0].model_dump(exclude_none=True)["messages"][0]["content"][0]["logprobs"][0]["chosen"]["token_id"] == 7
    )
    assert chunks[1].error_details is not None
    assert chunks[1].error_details["user_message"] == "Try again"
    assert chunks[1].model_dump(exclude_none=True)["additional_data"] == {"execution_steps": []}


def test_build_request_json_preserves_ids_for_repeated_function_names() -> None:
    calls = [
        {"function_call": {"id": "call-1", "name": "lookup", "arguments": {"key": "a"}}},
        {"function_call": {"id": "call-2", "name": "lookup", "arguments": {"key": "b"}}},
    ]
    results = [
        {"function_result": {"id": "call-1", "name": "lookup", "result": {"value": 1}}},
        {"function_result": {"id": "call-2", "name": "lookup", "result": {"value": 2}}},
    ]
    payload = {
        "messages": [
            {"role": "assistant", "tools_state_id": "state-1", "content": calls},
            {"role": "tool", "tools_state_id": "state-1", "content": results},
        ],
        "model_options": {"parallel_tool_calls": True},
    }
    request = ChatCompletionRequest.model_validate(payload)

    assert request.messages[1].content is not None
    assert all(part.function_result is not None for part in request.messages[1].content)
    assert [part.function_result.id_ for part in request.messages[1].content if part.function_result] == [
        "call-1",
        "call-2",
    ]
    assert chat_completions._build_request_json(request) == payload
