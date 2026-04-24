import json

import httpx
from pytest_httpx import HTTPXMock

from gigachat.api import chat_completions
from gigachat.context import chat_completions_url_cvar
from gigachat.models.chat_completions import ChatCompletionChunk, ChatCompletionRequest, ChatMessage
from tests.constants import BASE_URL, HEADERS_STREAM, MOCK_URL

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
