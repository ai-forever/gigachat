"""Wire contracts for thread metadata, status compatibility and sharing."""

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx2
import pytest

from gigachat import GigaChat, RequestOptions
from gigachat.exceptions import APIResponseValidationError, ResponseError
from gigachat.models.threads import ThreadRunOptions, ThreadStatus

BASE = "https://api.example.test/v1"
COMPLETION = {
    "object": "threads.messages.run",
    "model": "model",
    "thread_id": "thread",
    "message_id": "message",
    "created": 1,
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    "message": {"role": "assistant", "content": "hello"},
    "finish_reason": "stop",
}
CHUNK: dict[str, Any] = {key: value for key, value in COMPLETION.items() if key not in {"message", "finish_reason"}}
CHUNK["choices"] = [{"index": 0, "delta": {"content": "hello"}}]


@pytest.fixture
async def wire() -> AsyncIterator[tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]]]:
    requests: list[httpx2.Request] = []
    responses: list[httpx2.Response] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return responses.pop(0)

    transport = httpx2.MockTransport(handle)
    with httpx2.Client(transport=transport) as sync:
        async with httpx2.AsyncClient(transport=transport) as asynchronous:
            async with GigaChat(
                base_url=BASE,
                access_token="fixture",
                http_client=sync,
                async_http_client=asynchronous,
                trust_env=False,
            ) as client:
                yield client, requests, responses
            assert not sync.is_closed
            assert not asynchronous.is_closed
    assert not responses


async def invoke(client: GigaChat, asynchronous: bool, method: str, **kwargs: Any) -> Any:
    resource = client.a_threads if asynchronous else client.threads
    call = getattr(resource, method)(**kwargs)
    if method.endswith("_stream"):
        if asynchronous:
            async with call:
                return [chunk async for chunk in call]
        with call:
            return list(call)
    return await call if asynchronous else call


def completion_response(streaming: bool = False) -> httpx2.Response:
    if streaming:
        return httpx2.Response(
            200,
            headers={"Content-Type": "text/event-stream", "X-Request-ID": "request"},
            content=f"data: {json.dumps(CHUNK)}\n\ndata: [DONE]\n\n".encode(),
        )
    return httpx2.Response(200, json=COMPLETION, headers={"X-Request-ID": "request"})


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("method", ["add_message", "add_messages", "run_messages", "run_messages_stream"])
@pytest.mark.parametrize("metadata", [None, {}, {"label": "value"}])
async def test_metadata_omission_and_empty_object(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]],
    asynchronous: bool,
    method: str,
    metadata: dict[str, Any] | None,
) -> None:
    client, requests, responses = wire
    kwargs: dict[str, Any] = {"thread_id": "thread", "metadata": metadata}
    if method == "add_message":
        kwargs["message"] = "hello"
    else:
        kwargs["messages"] = ["hello"]
    if method.startswith("run"):
        kwargs.update(update_interval=0, thread_options=ThreadRunOptions(unnormalized_history=False))
        responses.append(completion_response(method.endswith("_stream")))
    else:
        responses.append(httpx2.Response(200, json={"thread_id": "thread", "messages": []}))
    await invoke(client, asynchronous, method, **kwargs)
    request = requests[0]
    body = json.loads(request.content)
    assert request.method == "POST"
    assert request.headers["Content-Type"] == "application/json"
    assert request.url.path == "/v1/threads/messages" + ("/run" if method.startswith("run") else "")
    assert body["thread_id"] == "thread"
    assert body.get("model") is None
    assert body.get("assistant_id") is None
    if metadata is None:
        assert "metadata" not in body
    else:
        assert body["metadata"] == metadata
    if method.startswith("run"):
        assert body["update_interval"] == 0
        assert body["unnormalized_history"] is False
        assert body.get("stream", False) is method.endswith("_stream")


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("method", ["rerun_messages", "rerun_messages_stream"])
@pytest.mark.parametrize("interval", [0, 0.5])
async def test_rerun_update_interval_seconds(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]],
    asynchronous: bool,
    method: str,
    interval: float,
) -> None:
    client, requests, responses = wire
    responses.append(completion_response(method.endswith("_stream")))
    await invoke(client, asynchronous, method, thread_id="thread", update_interval=interval)
    assert requests[0].url.path == "/v1/threads/messages/rerun"
    assert json.loads(requests[0].content)["update_interval"] == interval


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("method", ["list", "retrieve"])
@pytest.mark.parametrize("status", ["ready", "frozen", "future_state"])
async def test_thread_status_and_metadata(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]],
    asynchronous: bool,
    method: str,
    status: str,
) -> None:
    client, _, responses = wire
    last_message = {"content": "hello", "additional_data": ["future", {"value": None}]}
    responses.append(
        httpx2.Response(
            200,
            json={
                "threads": [
                    {
                        "id": "thread",
                        "model": "model",
                        "created_at": 1,
                        "updated_at": 2,
                        "run_lock": False,
                        "status": status,
                        "metadata": {},
                        "access_policy": "private",
                        "last_message": last_message,
                    }
                ],
            },
            headers={"X-Request-ID": "request"},
        )
    )
    result = await invoke(client, asynchronous, method, **({"threads_ids": ["thread"]} if method == "retrieve" else {}))
    thread = result.threads[0]
    assert thread.status == status
    if status != "future_state":
        assert thread.status is ThreadStatus(status)
    else:
        assert type(thread.status) is str
    assert thread.metadata == {}
    assert thread.access_policy == "private"
    assert thread.last_message == last_message
    assert result.request_id == "request"


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("method", ["get_messages", "rerun_messages"])
async def test_thread_message_response_metadata_retains_json_shape(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]], asynchronous: bool, method: str
) -> None:
    client, _, responses = wire
    message = {
        "message_id": "message",
        "created_at": 1,
        "role": "assistant",
        "content": "hello",
        "model": "model-version",
        "notasearch_sources": [{"url": "https://example.test", "score": None}],
        "additional_data": ["value", {"unknown": True}],
    }
    payload = (
        {"thread_id": "thread", "messages": [message]}
        if method == "get_messages"
        else {**COMPLETION, "message": message}
    )
    responses.append(httpx2.Response(200, json=payload))
    result = await invoke(client, asynchronous, method, thread_id="thread")
    parsed = result.messages[0] if method == "get_messages" else result.message
    assert parsed.model == message["model"]
    assert parsed.notasearch_sources == message["notasearch_sources"]
    assert parsed.additional_data == message["additional_data"]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("functions", [None, []])
async def test_assistant_update_preserves_explicit_empty_functions(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]],
    asynchronous: bool,
    functions: list[Any] | None,
) -> None:
    client, requests, responses = wire
    responses.append(
        httpx2.Response(200, json={"assistant_id": "assistant", "model": "model", "created_at": 1, "updated_at": 2})
    )
    resource: Any = client.a_assistants if asynchronous else client.assistants
    result = resource.update("assistant", functions=functions)
    if asynchronous:
        await result
    body = json.loads(requests[0].content)
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/v1/assistants/modify"
    if functions is None:
        assert "functions" not in body
    else:
        assert body["functions"] == []


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status", [200, 201, 302, 400, 401, 429, 500])
async def test_thread_share_contract_and_options(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]], asynchronous: bool, status: int
) -> None:
    client, requests, responses = wire
    response = httpx2.Response(
        status,
        json={"shared_thread_id": "shared", "link": "https://example.test/shared"},
        headers={"X-Request-ID": "request"},
    )
    responses.append(response)
    options = RequestOptions(
        extra_headers={"X-Fixture": "value"},
        extra_query=[("tag", "a"), ("tag", "b")],
        extra_body={"provider_extension": {}},
    )
    if status == 200:
        result = await invoke(client, asynchronous, "share", thread_id="thread", request_options=options)
        assert result.shared_thread_id == "shared"
        assert result.link == "https://example.test/shared"
        assert result.request_id == "request"
    else:
        with pytest.raises(ResponseError) as error:
            await invoke(client, asynchronous, "share", thread_id="thread", request_options=options)
        assert error.value.status_code == status
        assert error.value.request_id == "request"
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert request.url.path == "/v1/threads/share"
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["X-Fixture"] == "value"
    assert request.url.params.get_list("tag") == ["a", "b"]
    assert json.loads(request.content) == {"thread_id": "thread", "provider_extension": {}}
    assert response.is_closed


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_thread_share_invalid_response_has_request_id(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]], asynchronous: bool
) -> None:
    client, _, responses = wire
    responses.append(
        httpx2.Response(200, json={"link": "https://example.test/shared"}, headers={"X-Request-ID": "request"})
    )
    with pytest.raises(APIResponseValidationError) as error:
        await invoke(client, asynchronous, "share", thread_id="thread")
    assert error.value.request_id == "request"
    assert error.value.__cause__ is not None


class OpenStream(httpx2.SyncByteStream, httpx2.AsyncByteStream):
    def __init__(self) -> None:
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        yield f"data: {json.dumps(CHUNK)}\n\n".encode()
        raise AssertionError("Early close must not read another chunk")

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self:
            yield chunk

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.close()


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("method", ["run_messages_stream", "rerun_messages_stream"])
async def test_thread_stream_early_close_releases_response(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]], asynchronous: bool, method: str
) -> None:
    client, requests, responses = wire
    raw = OpenStream()
    responses.append(httpx2.Response(200, headers={"Content-Type": "text/event-stream"}, stream=raw))
    resource = client.a_threads if asynchronous else client.threads
    kwargs: dict[str, Any] = {"thread_id": "thread", "update_interval": 0}
    if method == "run_messages_stream":
        kwargs["messages"] = ["hello"]
    stream = getattr(resource, method)(**kwargs)
    if asynchronous:
        async with stream:
            assert (await anext(stream)).choices[0].delta.content == "hello"
    else:
        with stream:
            assert next(stream).choices[0].delta.content == "hello"
    assert raw.closed
    assert len(requests) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_thread_stream_usage_arrives_only_with_final_chunk(
    wire: tuple[GigaChat, list[httpx2.Request], list[httpx2.Response]], asynchronous: bool
) -> None:
    client, requests, responses = wire
    first = {key: value for key, value in CHUNK.items() if key != "usage"}
    final = {**CHUNK, "choices": [{"delta": {"content": ""}, "index": 0, "finish_reason": "stop"}]}
    response = httpx2.Response(
        200,
        headers={"Content-Type": "text/event-stream", "X-Request-ID": "thread-stream"},
        content=(f"data: {json.dumps(first)}\n\ndata: {json.dumps(final)}\n\ndata: [DONE]\n\n").encode(),
    )
    responses.append(response)
    chunks = await invoke(client, asynchronous, "run_messages_stream", thread_id="thread", messages=["hello"])
    assert len(chunks) == 2
    assert chunks[0].usage is None
    assert chunks[0].choices[0].delta.content == "hello"
    assert chunks[1].usage.total_tokens == 2
    assert chunks[1].choices[0].finish_reason == "stop"
    assert all(chunk.request_id == "thread-stream" for chunk in chunks)
    assert len(requests) == 1
    assert response.is_closed
