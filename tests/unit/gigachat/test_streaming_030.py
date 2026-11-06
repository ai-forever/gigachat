import asyncio
import inspect
import json
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx2 as httpx
import pytest
from pydantic import BaseModel, ValidationError

from gigachat._response import AsyncStreamingResponse, RawResponse, StreamingResponse
from gigachat._streaming import AsyncStream, Stream
from gigachat.api.utils import parse_chunk, parse_event_chunk
from gigachat.exceptions import APIConnectionError, APIResponseValidationError, APITimeoutError, StreamInterruptedError
from gigachat.models.chat_completions import ChatCompletionChunk


class Chunk(BaseModel):
    value: str
    event: str | None = None
    x_headers: dict[str, str | None] | None = None


class Bytes(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __init__(self, content: bytes, *, failure: bool = False) -> None:
        self.content = content
        self.failure = failure
        self.closed = False
        self.reads = 0

    def __iter__(self) -> Iterator[bytes]:
        for byte in self.content:
            self.reads += 1
            yield bytes([byte])
        if self.failure:
            raise httpx.ReadError("connection lost")

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self:
            yield chunk

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.close()


def response(body: Bytes) -> httpx.Response:
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream", "x-request-id": "test-request", "x-custom": "metadata"},
        stream=body,
        request=httpx.Request("POST", "https://example.test/chat"),
    )


@pytest.mark.parametrize("ending", ["\n", "\r", "\r\n"])
@pytest.mark.parametrize("final_blank", [True, False])
def test_sse_sync_utf8_multiline_and_eof(ending: str, final_blank: bool) -> None:
    lines = [": keepalive", "", "event: result", 'data: {"value":', 'data: "Привет 🌏"}']
    content = ending.join(lines) + (ending * 2 if final_blank else "")
    body = Bytes(content.encode())
    stream = Stream(response(body), Chunk, event_mode=True)
    chunks = list(stream)
    assert len(chunks) == 1
    assert chunks[0].value == "Привет 🌏"
    assert chunks[0].event == "result"
    assert chunks[0].x_headers is not None
    assert chunks[0].x_headers["x-request-id"] == "test-request"
    assert stream.request_id == "test-request"
    assert stream.headers["x-custom"] == "metadata"
    assert stream.status_code == 200
    assert str(stream.url) == "https://example.test/chat"
    assert stream.completed
    assert stream.is_closed
    assert body.closed


@pytest.mark.parametrize("ending", ["\n", "\r", "\r\n"])
@pytest.mark.parametrize("final_blank", [True, False])
async def test_sse_async_utf8_multiline_and_eof(ending: str, final_blank: bool) -> None:
    content = ending.join([": ping", "", "event: result", 'data: {"value":', 'data: "Привет 🌏"}'])
    body = Bytes((content + (ending * 2 if final_blank else "")).encode())
    stream = AsyncStream(response(body), Chunk, event_mode=True)
    chunks = [chunk async for chunk in stream]
    assert [(chunk.event, chunk.value) for chunk in chunks] == [("result", "Привет 🌏")]
    assert stream.completed
    assert stream.is_closed
    assert body.closed


def test_done_stops_without_reconnect_or_reading_tail() -> None:
    content = b'retry: 1\n\ndata: \n\ndata: {"value":"one"}\n\ndata: [DONE]\n\n'
    body = Bytes(content + b'data: {"value":"must not appear"}\n\n', failure=True)
    stream = Stream(response(body), Chunk)
    assert [chunk.value for chunk in stream] == ["one"]
    assert body.reads == len(content)
    assert body.closed


def test_primary_metadata_and_unknown_fields_survive() -> None:
    body = Bytes(
        b'event: response.message.done\ndata: {"message_id":"m", "tools_state_id":"t", '
        b'"finish_reason":"stop", "future":{"nested":1}, "usage":{"total_tokens":9}}\n\n'
    )
    chunk = list(Stream(response(body), ChatCompletionChunk, event_mode=True))[0]
    assert chunk.event == "response.message.done"
    assert chunk.message_id == "m"
    assert chunk.tools_state_id == "t"
    assert chunk.finish_reason == "stop"
    assert chunk.usage is not None
    assert chunk.usage.total_tokens == 9
    assert chunk.model_extra is not None
    assert chunk.model_extra["future"] == {"nested": 1}


@pytest.mark.parametrize("content", [b'data: {"value":', b"data: private prompt\n\n", b"data: {}\n\n"])
def test_invalid_event_closes_and_does_not_log_payload(content: bytes, caplog: pytest.LogCaptureFixture) -> None:
    body = Bytes(content)
    stream = Stream(response(body), Chunk)
    with pytest.raises(APIResponseValidationError) as exc:
        list(stream)
    assert exc.value.__cause__ is not None
    assert "private prompt" not in caplog.text
    assert body.closed
    assert stream.is_closed
    assert not stream.completed


@pytest.mark.parametrize("limit", [1, 16])
def test_sync_event_size_limit_including_unterminated_line(limit: int) -> None:
    body = Bytes(b'data: {"value":"' + b"x" * 1000)
    with pytest.raises(APIResponseValidationError) as exc:
        list(Stream(response(body), Chunk, max_event_size=limit))
    assert isinstance(exc.value.__cause__, httpx.SSEError)
    assert body.closed
    assert body.reads < 1000


async def test_async_event_size_limit() -> None:
    body = Bytes(b'data: {"value":"' + b"x" * 1000)
    with pytest.raises(APIResponseValidationError):
        _ = [chunk async for chunk in AsyncStream(response(body), Chunk, max_event_size=16)]
    assert body.closed
    assert body.reads < 1000


def test_event_size_limit_can_be_disabled() -> None:
    body = Bytes(b'data: {"value":"works"}\n\n')
    assert list(Stream(response(body), Chunk, max_event_size=None))[0].value == "works"


def test_sync_early_exit_and_close_before_first_next() -> None:
    body = Bytes(b'data: {"value":"one"}\n\ndata: {"value":"two"}\n\n')
    with Stream(response(body), Chunk) as stream:
        assert next(stream).value == "one"
    assert body.closed
    assert stream.is_closed
    assert not stream.completed
    assert list(stream) == []
    unopened = Bytes(b"never read")
    Stream(response(unopened), Chunk).close()
    assert unopened.closed
    assert unopened.reads == 0


async def test_async_early_exit_and_close_before_first_next() -> None:
    body = Bytes(b'data: {"value":"one"}\n\ndata: {"value":"two"}\n\n')
    async with AsyncStream(response(body), Chunk) as stream:
        assert (await stream.__anext__()).value == "one"
    assert body.closed
    assert stream.is_closed
    assert not stream.completed
    unopened = Bytes(b"never read")
    await AsyncStream(response(unopened), Chunk).aclose()
    assert unopened.closed
    assert unopened.reads == 0


@pytest.mark.parametrize("partial", [True, False])
def test_transport_failure_is_not_replayed(partial: bool) -> None:
    body = Bytes(b'data: {"value":"one"}\n\n' if partial else b"", failure=True)
    stream = Stream(response(body), Chunk)
    with pytest.raises(StreamInterruptedError) as exc:
        list(stream)
    assert exc.value.partial_output is partial
    assert exc.value.request_id == "test-request"
    assert isinstance(exc.value.__cause__, httpx.ReadError)
    assert body.closed
    assert not stream.completed


async def test_async_transport_failure_is_not_replayed() -> None:
    body = Bytes(b'data: {"value":"one"}\n\n', failure=True)
    stream = AsyncStream(response(body), Chunk)
    with pytest.raises(StreamInterruptedError) as exc:
        _ = [chunk async for chunk in stream]
    assert exc.value.partial_output
    assert body.closed
    assert not stream.completed


async def test_cancellation_closes_response() -> None:
    entered = asyncio.Event()

    class BlockingBytes(Bytes):
        async def __aiter__(self) -> AsyncIterator[bytes]:
            entered.set()
            await asyncio.Event().wait()
            yield b"unreachable"

    body = BlockingBytes(b"")
    stream = AsyncStream(response(body), Chunk)
    task = asyncio.create_task(stream.__anext__())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert body.closed
    assert stream.is_closed
    assert not stream.completed


def test_lazy_iterator_is_closed_on_early_exit() -> None:
    body = Bytes(b'data: {"value":"one"}\n\ndata: {"value":"two"}\n\n')

    def generate() -> Iterator[Chunk]:
        with Stream(response(body), Chunk) as inner:
            yield from inner

    with Stream.from_iterator(generate()) as stream:
        assert next(stream).value == "one"
        assert stream.request_id == "test-request"
    assert body.closed


async def test_lazy_async_iterator_is_closed_on_early_exit() -> None:
    body = Bytes(b'data: {"value":"one"}\n\ndata: {"value":"two"}\n\n')

    async def generate() -> AsyncIterator[Chunk]:
        async with AsyncStream(response(body), Chunk) as inner:
            async for chunk in inner:
                yield chunk

    async with AsyncStream.from_iterator(generate()) as stream:
        assert (await stream.__anext__()).value == "one"
        assert stream.request_id == "test-request"
    assert body.closed


def test_legacy_parsing_does_not_log_secrets(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(ValidationError):
        parse_chunk("data: secret prompt", Chunk)
    with pytest.raises(json.JSONDecodeError):
        parse_event_chunk("private event", "secret prompt", Chunk)
    assert "secret prompt" not in caplog.text
    assert "private event" not in caplog.text


def test_raw_response_parsing_is_synchronous_and_preserves_metadata() -> None:
    body = Bytes(b'{"value":"one"}')
    http_response = response(body)
    with pytest.raises(httpx.ResponseNotRead):
        RawResponse(http_response, lambda r: Chunk.model_validate_json(r.content))
    http_response.read()
    raw = RawResponse(http_response, lambda r: Chunk.model_validate_json(r.content))
    assert raw.parse().value == "one"
    assert not inspect.isawaitable(raw.parse())
    assert raw.content == body.content
    assert raw.request_id == "test-request"
    assert raw.status_code == 200
    assert raw.headers["x-custom"] == "metadata"


async def test_raw_after_async_request_has_sync_parse() -> None:
    http_response = response(Bytes(b'{"value":"one"}'))
    await http_response.aread()
    raw = RawResponse(http_response, lambda r: Chunk.model_validate_json(r.content))
    assert raw.parse().value == "one"
    assert not inspect.isawaitable(raw.parse())


def test_streaming_bytes_are_lazy_and_closed() -> None:
    body = Bytes(b"binary\x00payload")
    with StreamingResponse(response(body), lambda r: r.content) as stream:
        assert body.reads == 0
        assert next(stream.iter_bytes(3)) == b"bin"
    assert body.closed


async def test_async_streaming_bytes_parse_is_awaited() -> None:
    body = Bytes(b"binary\x00payload")
    async with AsyncStreamingResponse(response(body), lambda r: r.content) as stream:
        assert body.reads == 0
        assert await stream.parse() == body.content
    assert body.closed


def test_lazy_metadata_uses_open_response() -> None:
    body = Bytes(b'data: {"value":"one"}\n\n')
    opened: list[httpx.Response] = []

    def generate() -> Iterator[Chunk]:
        opened.append(response(body))
        with Stream(opened[0], Chunk) as inner:
            yield from inner

    with Stream.from_iterator(generate(), response_getter=lambda: opened[0] if opened else None) as stream:
        assert stream.status_code is None
        assert next(stream).value == "one"
        assert stream.status_code == 200
        assert stream.headers["x-custom"] == "metadata"
    assert body.closed


def test_raw_namespace_is_lazy_and_honors_request_options() -> None:
    from gigachat._request_options import RequestOptions
    from gigachat.client import GigaChatSyncClient

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        # Invalid JSON must be available to the raw caller before parse is requested.
        return httpx.Response(200, content=b"broken json", headers={"x-request-id": "raw-request"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        with GigaChatSyncClient(
            http_client=transport, access_token="token", model="model", base_url="https://example.test/v1"
        ) as client:
            raw = client.chat.with_raw_response.create(
                "hello", request_options=RequestOptions(extra_headers={"x-test": "yes"})
            )
            assert raw.content == b"broken json"
            assert raw.request_id == "raw-request"
            assert len(requests) == 1
            assert requests[0].url.path == "/v2/chat/completions"
            assert requests[0].headers["x-test"] == "yes"
            with pytest.raises(APIResponseValidationError, match="Invalid API response"):
                raw.parse()
        assert not transport.is_closed


async def test_async_raw_namespace_parse_is_sync_and_preserves_unknown_fields() -> None:
    from gigachat._request_options import RequestOptions
    from gigachat.client import GigaChatAsyncClient

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"messages": [], "future": 1}, headers={"x-request-id": "raw-request"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as transport:
        async with GigaChatAsyncClient(
            async_http_client=transport, access_token="token", model="model", base_url="https://example.test/v1"
        ) as client:
            raw = await client.achat.with_raw_response.create(
                "hello", request_options=RequestOptions(extra_headers={"x-test": "yes"})
            )
            parsed = raw.parse()
            assert parsed.model_extra is not None
            assert parsed.model_extra["future"] == 1
            assert len(requests) == 1
            assert requests[0].headers["x-test"] == "yes"
        assert not transport.is_closed


def test_file_download_streams_bytes_and_cleans_up_failure(tmp_path: "Path") -> None:
    from gigachat.client import GigaChatSyncClient

    payload = b"\xff\x00binary" * 20000
    bodies: list[Bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "application/octet-stream"
        assert request.url.path == "/v1/files/file/content"
        body = Bytes(payload, failure=len(bodies) == 2)
        bodies.append(body)
        return httpx.Response(200, stream=body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        with GigaChatSyncClient(
            http_client=transport, access_token="token", base_url="https://example.test/v1"
        ) as client:
            assert client.get_file_content("file") == payload
            target = tmp_path / "download.bin"
            assert client.download_file("file", target) == target
            assert target.read_bytes() == payload
            target.write_bytes(b"preserve previous result")
            with pytest.raises(APIConnectionError) as error:
                client.download_file("file", target)
            assert isinstance(error.value.__cause__, httpx.ReadError)
            assert len(bodies) == 3
            assert target.read_bytes() == b"preserve previous result"
            assert sorted(path.name for path in tmp_path.iterdir()) == ["download.bin"]
    assert all(body.closed for body in bodies)


async def test_async_file_download_and_early_close(tmp_path: "Path") -> None:
    from gigachat.client import GigaChatAsyncClient

    payload = b"\xff\x00binary" * 10000
    bodies: list[Bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = Bytes(payload)
        bodies.append(body)
        return httpx.Response(200, stream=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as transport:
        async with GigaChatAsyncClient(
            async_http_client=transport, access_token="token", base_url="https://example.test/v1"
        ) as client:
            assert await client.aget_file_content("file") == payload
            target = tmp_path / "download.bin"
            assert await client.adownload_file("file", target) == target
            assert target.read_bytes() == payload
            async with await client.astream_file_content("file") as stream:
                assert bodies[-1].reads == 0
                iterator = stream.iter_bytes(1)
                assert await iterator.__anext__() == payload[:1]
                await iterator.aclose()
    assert all(body.closed for body in bodies)


def test_primary_stream_early_close_preserves_shared_client_and_metadata() -> None:
    from gigachat.client import GigaChatSyncClient

    body = Bytes(b'data: {"message_id":"first"}\n\ndata: {"message_id":"second"}\n\n')
    with httpx.Client(transport=httpx.MockTransport(lambda request: response(body))) as transport:
        with GigaChatSyncClient(http_client=transport, access_token="token", model="model") as client:
            with client.chat.stream("hello") as stream:
                assert next(stream).message_id == "first"
                assert stream.headers["x-custom"] == "metadata"
                assert stream.status_code == 200
            assert body.closed
        assert not transport.is_closed


async def test_primary_async_stream_early_close_owns_all_generators() -> None:
    from gigachat.client import GigaChatAsyncClient

    body = Bytes(b'data: {"message_id":"first"}\n\ndata: {"message_id":"second"}\n\n')
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: response(body))) as transport:
        async with GigaChatAsyncClient(async_http_client=transport, access_token="token", model="model") as client:
            async with client.achat.stream("hello") as stream:
                assert (await stream.__anext__()).message_id == "first"
                assert stream.headers["x-custom"] == "metadata"
                assert stream.status_code == 200
            assert body.closed
        assert not transport.is_closed


def test_primary_stream_does_not_retry_partial_output() -> None:
    from gigachat.client import GigaChatSyncClient

    requests: list[httpx.Request] = []
    body = Bytes(b'data: {"message_id":"first"}\n\n', failure=True)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return response(body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        with GigaChatSyncClient(http_client=transport, access_token="token", model="model", max_retries=3) as client:
            with client.chat.stream("hello") as stream:
                assert next(stream).message_id == "first"
                with pytest.raises(StreamInterruptedError) as exc:
                    next(stream)
            assert exc.value.partial_output
            assert exc.value.request_id == "test-request"
            assert len(requests) == 1
    assert body.closed


async def test_primary_async_stream_event_size_request_override() -> None:
    from gigachat._request_options import RequestOptions
    from gigachat.client import GigaChatAsyncClient

    body = Bytes(b'data: {"message_id":"long value"}\n\n')
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: response(body))) as transport:
        async with GigaChatAsyncClient(async_http_client=transport, access_token="token", model="model") as client:
            with pytest.raises(APIResponseValidationError):
                async with client.achat.stream(
                    "hello", request_options=RequestOptions(max_sse_event_size=16)
                ) as stream:
                    await stream.__anext__()
    assert body.closed


@pytest.mark.parametrize("method", ["run_stream", "run_messages_stream", "rerun_messages_stream"])
async def test_thread_async_stream_early_close_owns_all_generators(method: str) -> None:
    from gigachat.client import GigaChatAsyncClient
    from tests.constants import POST_THREAD_MESSAGES_RUN_STREAM

    body = Bytes(POST_THREAD_MESSAGES_RUN_STREAM)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: response(body))) as transport:
        async with GigaChatAsyncClient(async_http_client=transport, access_token="token", model="model") as client:
            function = getattr(client.a_threads, method)
            options = {"messages": ["hello"]} if method == "run_messages_stream" else {"thread_id": "thread"}
            stream = function(**options)
            assert isinstance(stream, AsyncStream)
            async with stream:
                await stream.__anext__()
            assert body.closed
        assert not transport.is_closed


@pytest.mark.parametrize("operation", ["read", "iter_bytes", "parse"])
@pytest.mark.parametrize("timeout", [False, True])
def test_binary_response_normalizes_read_failures(operation: str, timeout: bool) -> None:
    original = httpx.ReadTimeout("read timed out") if timeout else httpx.ReadError("read failed")

    class FailingBytes(Bytes):
        def __iter__(self) -> Iterator[bytes]:
            self.reads += 1
            yield b"partial"
            raise original

    body = FailingBytes(b"")
    stream = StreamingResponse(response(body), lambda result: result.content)
    expected = APITimeoutError if timeout else APIConnectionError

    def consume() -> None:
        if operation == "iter_bytes":
            iterator = stream.iter_bytes()
            assert next(iterator) == b"partial"
            next(iterator)
        elif operation == "read":
            stream.read()
        else:
            stream.parse()

    with pytest.raises(expected) as caught:
        consume()
    assert caught.value.__cause__ is original
    assert caught.value.request_id == "test-request"
    assert body.reads == 1
    assert body.closed
    assert stream.is_closed


@pytest.mark.parametrize("operation", ["read", "iter_bytes", "parse"])
@pytest.mark.parametrize("timeout", [False, True])
async def test_async_binary_response_normalizes_read_failures(operation: str, timeout: bool) -> None:
    original = httpx.ReadTimeout("read timed out") if timeout else httpx.ReadError("read failed")

    class FailingBytes(Bytes):
        def __iter__(self) -> Iterator[bytes]:
            self.reads += 1
            yield b"partial"
            raise original

    body = FailingBytes(b"")
    stream = AsyncStreamingResponse(response(body), lambda result: result.content)
    expected = APITimeoutError if timeout else APIConnectionError

    async def consume() -> None:
        if operation == "iter_bytes":
            iterator = stream.iter_bytes()
            assert await iterator.__anext__() == b"partial"
            await iterator.__anext__()
        elif operation == "read":
            await stream.read()
        else:
            await stream.parse()

    with pytest.raises(expected) as caught:
        await consume()
    assert caught.value.__cause__ is original
    assert caught.value.request_id == "test-request"
    assert body.reads == 1
    assert body.closed
    assert stream.is_closed


def test_primary_stream_content_type_failure_is_not_retried() -> None:
    from gigachat.client import GigaChatSyncClient

    requests: list[httpx.Request] = []
    body = Bytes(b'{"unexpected":"JSON response"}')

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "application/json", "x-request-id": "invalid-stream"},
            stream=body,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        with GigaChatSyncClient(http_client=transport, access_token="token", model="model", max_retries=3) as client:
            with client.chat.stream("hello") as stream:
                with pytest.raises(APIResponseValidationError, match="Expected response Content-Type") as caught:
                    next(stream)
            assert caught.value.request_id == "invalid-stream"
            assert len(requests) == 1
            assert body.reads == 0
            assert body.closed
            assert stream.is_closed
            assert not stream.completed


async def test_primary_async_stream_content_type_failure_is_not_retried() -> None:
    from gigachat.client import GigaChatAsyncClient

    requests: list[httpx.Request] = []
    body = Bytes(b'{"unexpected":"JSON response"}')

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "application/json", "x-request-id": "invalid-stream"},
            stream=body,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as transport:
        async with GigaChatAsyncClient(
            async_http_client=transport, access_token="token", model="model", max_retries=3
        ) as client:
            async with client.achat.stream("hello") as stream:
                with pytest.raises(APIResponseValidationError, match="Expected response Content-Type") as caught:
                    await stream.__anext__()
            assert caught.value.request_id == "invalid-stream"
            assert len(requests) == 1
            assert body.reads == 0
            assert body.closed
            assert stream.is_closed
            assert not stream.completed
