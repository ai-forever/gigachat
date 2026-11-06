from contextvars import ContextVar

import httpx2 as httpx
import pytest
from pydantic import BaseModel, ValidationError

from gigachat.api.utils import (
    USER_AGENT,
    build_headers,
    build_response,
    build_x_headers,
    execute_event_stream_async,
    execute_event_stream_sync,
    execute_request_async,
    execute_request_sync,
    execute_stream_async,
    execute_stream_sync,
    parse_chunk,
    parse_event_chunk,
)
from gigachat.context import (
    agent_id_cvar,
    authorization_cvar,
    client_id_cvar,
    custom_headers_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
    trace_id_cvar,
)
from gigachat.exceptions import AuthenticationError, ResponseError
from tests.constants import BASE_URL
from tests.httpx_mock import HTTPXMock


class MockModel(BaseModel):
    """Mock model for testing."""

    value: str
    x_headers: dict[str, str | None] | None = None


class EventMockModel(MockModel):
    """Mock model for testing SSE events."""

    event: str | None = None


def test_build_headers_empty() -> None:
    headers = build_headers()
    assert "Authorization" not in headers
    assert headers == {"User-Agent": USER_AGENT}


def test_build_headers_with_token() -> None:
    token = "test_token"
    headers = build_headers(access_token=token)
    assert headers["Authorization"] == f"Bearer {token}"
    assert "authorization" not in headers


def test_build_headers_context_vars() -> None:
    token = "context_token"
    token_reset = authorization_cvar.set(f"Bearer {token}")
    try:
        headers = build_headers()
        assert headers["Authorization"] == f"Bearer {token}"
    finally:
        authorization_cvar.reset(token_reset)


def test_build_x_headers() -> None:
    headers = httpx.Headers(
        {
            "x-request-id": "req-1",
            "x-session-id": "sess-1",
            "x-client-id": "client-1",
        }
    )
    response = httpx.Response(200, headers=headers)
    x_headers = build_x_headers(response)
    assert x_headers["x-request-id"] == "req-1"
    assert x_headers["x-session-id"] == "sess-1"
    assert x_headers["x-client-id"] == "client-1"


def test_build_response_success() -> None:
    response = httpx.Response(200, json={"value": "test"})
    model = build_response(response, MockModel)
    assert isinstance(model, MockModel)
    assert model.value == "test"


def test_build_response_error() -> None:
    request = httpx.Request("GET", f"{BASE_URL}/test")
    response = httpx.Response(400, content="Bad Request", request=request)
    with pytest.raises(ResponseError):
        build_response(response, MockModel)


def test_execute_request_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE_URL}/test", json={"value": "sync"})

    with httpx.Client(base_url=BASE_URL) as client:
        response = execute_request_sync(
            client,
            {"method": "GET", "url": "/test"},
            MockModel,
        )

    assert isinstance(response, MockModel)
    assert response.value == "sync"


async def test_execute_request_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE_URL}/test", json={"value": "async"})

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await execute_request_async(
            client,
            {"method": "GET", "url": "/test"},
            MockModel,
        )

    assert isinstance(response, MockModel)
    assert response.value == "async"


def test_parse_chunk_valid() -> None:
    chunk = parse_chunk('data: {"value": "chunk"}', MockModel)
    assert isinstance(chunk, MockModel)
    assert chunk.value == "chunk"


def test_parse_chunk_valid_no_space() -> None:
    chunk = parse_chunk('data:{"value": "chunk"}', MockModel)
    assert isinstance(chunk, MockModel)
    assert chunk.value == "chunk"


def test_parse_chunk_done() -> None:
    chunk = parse_chunk("data: [DONE]", MockModel)
    assert chunk is None


def test_parse_event_chunk_valid() -> None:
    chunk = parse_event_chunk("response.message.done", '{"value": "chunk"}', EventMockModel)
    assert isinstance(chunk, EventMockModel)
    assert chunk.event == "response.message.done"
    assert chunk.value == "chunk"


def test_parse_chunk_invalid() -> None:
    with pytest.raises(ValidationError):
        parse_chunk("data: invalid json", MockModel)


def test_execute_stream_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=b'data: {"value": "chunk1"}\n\ndata: {"value": "chunk2"}\n\n',
        headers={"content-type": "text/event-stream"},
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chunks = list(
            execute_stream_sync(
                client,
                {"method": "GET", "url": "/stream"},
                MockModel,
            )
        )

    assert len(chunks) == 2
    assert chunks[0].value == "chunk1"
    assert chunks[1].value == "chunk2"


def test_execute_stream_sync_uses_v1_data_lines(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=b'event: response.message.done\ndata: {"value": "done"}\n\n',
        headers={"content-type": "text/event-stream", "x-request-id": "req-1"},
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chunks = list(
            execute_stream_sync(
                client,
                {"method": "GET", "url": "/stream"},
                EventMockModel,
            )
        )

    assert len(chunks) == 1
    assert chunks[0].event is None
    assert chunks[0].value == "done"
    assert chunks[0].x_headers is not None
    assert chunks[0].x_headers["x-request-id"] == "req-1"


def test_execute_event_stream_sync_preserves_sse_event(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=b'event: response.message.done\ndata: {"value": "done"}\n\n',
        headers={"content-type": "text/event-stream", "x-request-id": "req-1"},
    )

    with httpx.Client(base_url=BASE_URL) as client:
        chunks = list(
            execute_event_stream_sync(
                client,
                {"method": "GET", "url": "/stream"},
                EventMockModel,
            )
        )

    assert len(chunks) == 1
    assert chunks[0].event == "response.message.done"
    assert chunks[0].value == "done"
    assert chunks[0].x_headers is not None
    assert chunks[0].x_headers["x-request-id"] == "req-1"


async def test_execute_stream_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=b'data: {"value": "chunk1"}\n\ndata: {"value": "chunk2"}\n\n',
        headers={"content-type": "text/event-stream"},
    )

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        chunks = [
            chunk
            async for chunk in execute_stream_async(
                client,
                {"method": "GET", "url": "/stream"},
                MockModel,
            )
        ]

    assert len(chunks) == 2
    assert chunks[0].value == "chunk1"
    assert chunks[1].value == "chunk2"


async def test_execute_stream_async_uses_v1_data_lines(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=b'event: response.message.done\ndata: {"value": "done"}\n\n',
        headers={"content-type": "text/event-stream", "x-request-id": "req-1"},
    )

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        chunks = [
            chunk
            async for chunk in execute_stream_async(
                client,
                {"method": "GET", "url": "/stream"},
                EventMockModel,
            )
        ]

    assert len(chunks) == 1
    assert chunks[0].event is None
    assert chunks[0].value == "done"
    assert chunks[0].x_headers is not None
    assert chunks[0].x_headers["x-request-id"] == "req-1"


async def test_execute_event_stream_async_preserves_sse_event(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=b'event: response.message.done\ndata: {"value": "done"}\n\n',
        headers={"content-type": "text/event-stream", "x-request-id": "req-1"},
    )

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        chunks = [
            chunk
            async for chunk in execute_event_stream_async(
                client,
                {"method": "GET", "url": "/stream"},
                EventMockModel,
            )
        ]

    assert len(chunks) == 1
    assert chunks[0].event == "response.message.done"
    assert chunks[0].value == "done"
    assert chunks[0].x_headers is not None
    assert chunks[0].x_headers["x-request-id"] == "req-1"


def test_execute_stream_sync_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        status_code=401,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            list(
                execute_stream_sync(
                    client,
                    {"method": "GET", "url": "/stream"},
                    MockModel,
                )
            )


@pytest.mark.parametrize(
    ("stream", "expected_event"),
    [
        (b'data: {"value": "done"}\n\ndata: [DONE]\n\n', None),
        (b'event: response.message.done\ndata: {"value": "done"}\n\ndata: [DONE]\n\n', "response.message.done"),
        (b': keepalive\nid: 1\ndata: {\ndata: "value": "done"\ndata: }', None),
        (b'event: response.message.done\ndata: {"value": "done"}', "response.message.done"),
        (b'event: unused\n\ndata: {"value": "done"}\n\nevent: done\ndata: [DONE]', None),
    ],
)
def test_execute_event_stream_sync_accepts_sse_variants(
    httpx_mock: HTTPXMock, stream: bytes, expected_event: str | None
) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=stream,
        headers={"content-type": "text/event-stream", "x-request-id": "req-1"},
    )
    with httpx.Client(base_url=BASE_URL) as client:
        chunks = list(execute_event_stream_sync(client, {"method": "GET", "url": "/stream"}, EventMockModel))

    assert len(chunks) == 1
    assert chunks[0].value == "done"
    assert chunks[0].event == expected_event
    assert chunks[0].x_headers is not None
    assert chunks[0].x_headers["x-request-id"] == "req-1"


@pytest.mark.parametrize(
    ("stream", "expected_event"),
    [
        (b'data: {"value": "done"}\n\ndata: [DONE]\n\n', None),
        (b'event: response.message.done\ndata: {"value": "done"}\n\ndata: [DONE]\n\n', "response.message.done"),
        (b': keepalive\nid: 1\ndata: {\ndata: "value": "done"\ndata: }', None),
        (b'event: response.message.done\ndata: {"value": "done"}', "response.message.done"),
        (b'event: unused\n\ndata: {"value": "done"}\n\nevent: done\ndata: [DONE]', None),
    ],
)
async def test_execute_event_stream_async_accepts_sse_variants(
    httpx_mock: HTTPXMock, stream: bytes, expected_event: str | None
) -> None:
    httpx_mock.add_response(
        url=f"{BASE_URL}/stream",
        content=stream,
        headers={"content-type": "text/event-stream", "x-request-id": "req-1"},
    )
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        chunks = [
            chunk
            async for chunk in execute_event_stream_async(client, {"method": "GET", "url": "/stream"}, EventMockModel)
        ]

    assert len(chunks) == 1
    assert chunks[0].value == "done"
    assert chunks[0].event == expected_event
    assert chunks[0].x_headers is not None
    assert chunks[0].x_headers["x-request-id"] == "req-1"


@pytest.mark.parametrize(
    ("header", "variable"),
    [
        ("Authorization", authorization_cvar),
        ("X-Session-ID", session_id_cvar),
        ("X-Request-ID", request_id_cvar),
        ("X-Service-ID", service_id_cvar),
        ("X-Operation-ID", operation_id_cvar),
        ("X-Client-ID", client_id_cvar),
        ("X-Trace-ID", trace_id_cvar),
        ("X-Agent-ID", agent_id_cvar),
    ],
)
def test_build_headers_preserves_canonical_context_names(header: str, variable: ContextVar[str | None]) -> None:
    token = variable.set("context-value")
    try:
        headers = build_headers()
    finally:
        variable.reset(token)
    assert headers[header] == "context-value"
    assert header.lower() not in headers
    assert httpx.Headers(headers)[header.lower()] == "context-value"


def test_build_headers_lowercase_custom_overrides_keep_canonical_names() -> None:
    auth_token = authorization_cvar.set("Bearer context")
    session_token = session_id_cvar.set("context-session")
    custom_token = custom_headers_cvar.set(
        {
            "authorization": "Bearer custom",
            "user-agent": "custom-agent",
            "x-session-id": "custom-session",
            "X-CuStOm": "raw-case-value",
        }
    )
    try:
        headers = build_headers(access_token="sdk-token")
    finally:
        custom_headers_cvar.reset(custom_token)
        session_id_cvar.reset(session_token)
        authorization_cvar.reset(auth_token)
    assert headers == {
        "Authorization": "Bearer custom",
        "User-Agent": "custom-agent",
        "X-Session-ID": "custom-session",
        "X-CuStOm": "raw-case-value",
    }
    wire_headers = httpx.Headers(headers)
    assert wire_headers.get_list("authorization") == ["Bearer custom"]
    assert wire_headers.get_list("x-session-id") == ["custom-session"]
