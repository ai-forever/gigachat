"""Public request execution, option isolation and retry contracts for SDK 0.3.0."""

import asyncio
import copy
import inspect
import io
import json
import ssl
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx2
import pytest
from tests.constants import CHAT_COMPLETION_STREAM, MODELS, OAUTH_TOKEN_VALID

from gigachat import GigaChat
from gigachat._request_options import RequestOptions
from gigachat.context import custom_headers_cvar
from gigachat.exceptions import AuthenticationError, ResponseError, ServerError
from gigachat.models import ChatCompletionRequest
from gigachat.retry import _awith_retry_stream, _should_retry, _with_retry_stream
from gigachat.settings import Settings

PRIMARY_CHAT_COMPLETION: dict[str, Any] = {"messages": []}
BASE = "https://example.test/v1"
AUTH = "https://auth.test/oauth"

# Every original endpoint group, including aliases and streamed variants, must
# propagate request options through the same executor before response parsing.
ENDPOINTS: list[tuple[str, tuple[Any, ...], dict[str, Any], bool]] = [
    ("get_models", (), {}, False),
    ("get_model", ("model",), {}, False),
    ("tokens_count", (["text"],), {"model": "model"}, False),
    ("embeddings", (["text"],), {}, False),
    ("get_balance", (), {}, False),
    ("openapi_function_convert", ("{}",), {}, False),
    ("check_ai", ("text", "model"), {}, False),
    ("get_image", ("image",), {}, False),
    ("get_file", ("file",), {}, False),
    ("get_files", (), {}, False),
    ("delete_file", ("file",), {}, False),
    ("upload_file", (("file.txt", b"contents"),), {}, False),
    ("chat", ({"model": "model", "messages": []},), {}, False),
    ("chat.create", ({"model": "model", "messages": []},), {}, False),
    ("chat.stream", ({"model": "model", "messages": []},), {}, True),
    ("stream", ({"model": "model", "messages": []},), {}, True),
    ("assistants.get", (), {}, False),
    ("assistants.create", ("model", "name"), {}, False),
    ("assistants.update", ("id",), {"name": "new"}, False),
    ("assistants.delete", ("id",), {}, False),
    ("assistants.delete_file", ("id", "file"), {}, False),
    ("threads.list", (), {}, False),
    ("threads.get_threads", (), {}, False),
    ("threads.create_thread", (), {}, False),
    ("threads.retrieve", (["id"],), {}, False),
    ("threads.delete", ("id",), {}, False),
    ("threads.get_messages", ("id",), {}, False),
    ("threads.add_message", ("id", "text"), {}, False),
    ("threads.add_messages", ("id", ["text"]), {}, False),
    ("threads.run", ("id",), {}, False),
    ("threads.get_run", ("id",), {}, False),
    ("threads.run_stream", ("id",), {}, True),
    ("threads.run_messages", (), {"messages": ["text"]}, False),
    ("threads.rerun_messages", ("id",), {}, False),
    ("threads.run_messages_stream", (), {"messages": ["text"]}, True),
    ("threads.rerun_messages_stream", ("id",), {}, True),
]


def _method(client: GigaChat, name: str, asynchronous: bool = False) -> Any:
    parts = name.split(".")
    if asynchronous:
        parts[0] = {"chat": "achat", "assistants": "a_assistants", "threads": "a_threads"}.get(parts[0], "a" + parts[0])
    target: Any = client
    for part in parts:
        target = getattr(target, part)
    return target


@pytest.mark.parametrize(("name", "args", "kwargs", "stream"), ENDPOINTS, ids=[case[0] for case in ENDPOINTS])
def test_every_sync_endpoint_propagates_options(
    name: str, args: tuple[Any, ...], kwargs: dict[str, Any], stream: bool
) -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(400, json={"message": "bad request"}, headers={"x-request-id": "request-1"})

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, http_client=http, access_token="token") as sdk:
            with pytest.raises(ResponseError) as error:  # noqa: PT012 - invoke regular and streamed endpoints
                result = _method(sdk, name)(
                    *copy.deepcopy(args),
                    **copy.deepcopy(kwargs),
                    request_options=RequestOptions(
                        extra_headers={"X-Contract": "sync"}, extra_query=[("q", "1"), ("q", "2")]
                    ),
                )
                if stream:
                    list(result)
        assert not http.is_closed
    assert error.value.status_code == 400
    assert error.value.request_id == "request-1"
    assert len(seen) == 1
    assert seen[0].headers["X-Contract"] == "sync"
    assert seen[0].url.params.get_list("q") == ["1", "2"]
    assert seen[0].url.is_absolute_url


@pytest.mark.parametrize(("name", "args", "kwargs", "stream"), ENDPOINTS, ids=[case[0] for case in ENDPOINTS])
async def test_every_async_endpoint_propagates_options(
    name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    stream: bool,
) -> None:
    seen: list[httpx2.Request] = []

    async def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(400, json={"message": "bad request"}, headers={"x-request-id": "request-2"})

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(base_url=BASE, async_http_client=http, access_token="token") as sdk:
            with pytest.raises(ResponseError) as error:  # noqa: PT012 - invoke regular and streamed endpoints
                result = _method(sdk, name, True)(
                    *copy.deepcopy(args),
                    **copy.deepcopy(kwargs),
                    request_options=RequestOptions(
                        extra_headers={"X-Contract": "async"}, extra_query=[("q", "1"), ("q", "2")]
                    ),
                )
                if inspect.isawaitable(result):
                    result = await result
                if stream:
                    _ = [chunk async for chunk in result]
        assert not http.is_closed
    assert error.value.status_code == 400
    assert error.value.request_id == "request-2"
    assert len(seen) == 1
    assert seen[0].headers["X-Contract"] == "async"
    assert seen[0].url.params.get_list("q") == ["1", "2"]
    assert seen[0].url.is_absolute_url


def test_option_snapshot_header_query_precedence_and_payload_immutability() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=PRIMARY_CHAT_COMPLETION)

    headers = {"X-Test": "view"}
    body = {"custom": {"value": [1]}}
    query = [("q", "view")]
    options = RequestOptions(extra_headers=headers, extra_query=query, extra_body=body)
    headers["X-Test"] = "mutated"
    body["custom"]["value"].append(2)
    query.append(("q", "mutated"))
    payload = ChatCompletionRequest(model="model", messages=[])
    original = payload.model_dump()
    with httpx2.Client(
        transport=httpx2.MockTransport(handler), headers={"X-Test": "client"}, params=[("q", "client")]
    ) as http:
        with GigaChat(base_url=BASE, http_client=http, access_token="token") as sdk:
            view = sdk.with_options(
                **{
                    "extra_headers": options.extra_headers,
                    "extra_query": options.extra_query,
                    "extra_body": options.extra_body,
                }
            )
            token = custom_headers_cvar.set({"X-Test": "context"})
            try:
                view.chat.create(
                    payload,
                    request_options=RequestOptions(extra_headers={"x-test": "call"}, extra_query=[("q", "call")]),
                )
                sdk.chat.create(payload)
            finally:
                custom_headers_cvar.reset(token)
    assert payload.model_dump() == original
    assert seen[0].headers["X-Test"] == "call"
    assert seen[1].headers["X-Test"] == "context"
    assert seen[0].url.params.get_list("q") == ["client", "view", "call"]
    assert seen[1].url.params.get_list("q") == ["client"]
    assert json.loads(seen[0].content)["custom"] == {"value": [1]}
    assert "custom" not in json.loads(seen[1].content)


async def test_concurrent_views_do_not_share_request_state() -> None:
    seen: list[httpx2.Request] = []

    async def handler(request: httpx2.Request) -> httpx2.Response:
        await asyncio.sleep(0)
        seen.append(request)
        return httpx2.Response(200, json=MODELS)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(base_url=BASE, async_http_client=http, access_token="token") as sdk:
            first = sdk.with_options(extra_headers={"X-View": "one"}, extra_query=[("view", "one")])
            second = sdk.with_options(extra_headers={"X-View": "two"}, extra_query=[("view", "two")])
            await asyncio.gather(first.aget_models(), second.aget_models(), sdk.aget_models())
    assert sorted((request.headers.get("X-View", ""), request.url.params.get("view", "")) for request in seen) == [
        ("", ""),
        ("one", "one"),
        ("two", "two"),
    ]


@pytest.mark.parametrize("statuses", [[500, 401, 500], [401, 500, 200], [401, 401]])
def test_auth_replay_does_not_reset_status_retry_count(statuses: list[int], monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, str | None]] = []
    statuses = list(statuses)
    monkeypatch.setattr("gigachat._execution.time.sleep", lambda delay: None)

    def handler(request: httpx2.Request) -> httpx2.Response:
        events.append((request.url.host, request.headers.get("authorization")))
        if request.url.host == "auth.test":
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(statuses.pop(0), json=MODELS)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            http_client=http,
            auth_http_client=http,
            access_token="old",
            credentials="dummy",
            max_retries=1,
        ) as sdk:
            if statuses[-1] == 200:
                sdk.get_models()
            else:
                with pytest.raises(ResponseError):
                    sdk.get_models()
    assert not statuses
    assert sum(host == "auth.test" for host, _ in events) == 1
    assert events[0] == ("example.test", "Bearer old")


@pytest.mark.parametrize("status", [429, 500, 503])
def test_empty_status_allowlist_disables_retries(status: int) -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(status, json={"message": "failed"})

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, http_client=http, max_retries=3, retry_on_status_codes=()) as sdk:
            with pytest.raises(ResponseError):
                sdk.get_models()
    assert calls == 1


@pytest.mark.parametrize("delay", ["120", "99999999999999999999999999999999999999999"])
def test_server_delay_exceeding_retry_budget_is_not_shortened(delay: str, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []
    monkeypatch.setattr("gigachat._execution.time.sleep", sleeps.append)

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(503, headers={"retry-after": delay})

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, http_client=http, max_retries=3, max_retry_time=10) as sdk:
            with pytest.raises(ServerError):
                sdk.get_models()
    assert calls == 1
    assert sleeps == []


def test_external_authorization_bypasses_oauth_and_auth_replay() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(401)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE, auth_url=AUTH, http_client=http, auth_http_client=http, credentials="dummy"
        ) as sdk:
            with pytest.raises(AuthenticationError):
                sdk.get_models(request_options=RequestOptions(extra_headers={"Authorization": "Bearer external"}))
    assert len(seen) == 1
    assert seen[0].url.host == "example.test"
    assert seen[0].headers["Authorization"] == "Bearer external"


def test_owner_close_invalidates_views_and_preserves_borrowed_client() -> None:
    with httpx2.Client(transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=MODELS))) as http:
        sdk = GigaChat(base_url=BASE, http_client=http)
        view = sdk.with_options(extra_headers={"X-View": "view"})
        view.get_models()
        sdk.close()
        sdk.close()
        assert not http.is_closed
        assert http.get("https://other.test").status_code == 200
        with pytest.raises(RuntimeError, match="closed"):
            view.get_models()


@pytest.mark.parametrize(
    "error",
    [
        httpx2.PoolTimeout("busy"),
        httpx2.SSEError("bad format"),
        httpx2.LocalProtocolError("bad request"),
        httpx2.UnsupportedProtocol("unsupported"),
        httpx2.ProxyError("proxy"),
        httpx2.TransportError("unknown"),
    ],
)
def test_nontransient_transport_errors_are_not_retryable(error: Exception) -> None:
    assert not _should_retry(error, (429, 500))


def test_certificate_verification_failure_is_not_retryable() -> None:
    error = httpx2.ConnectError("TLS failed")
    error.__cause__ = ssl.SSLCertVerificationError("untrusted certificate")
    assert not _should_retry(error, (500,))


@pytest.mark.parametrize(
    "error", [httpx2.ReadError("read"), httpx2.ConnectTimeout("connect"), httpx2.RemoteProtocolError("remote")]
)
def test_transient_transport_errors_are_retryable(error: Exception) -> None:
    assert _should_retry(error, ())


def test_compatibility_stream_never_replays_delivered_item() -> None:
    class Client:
        _settings = Settings(max_retries=2)
        calls = 0

        @_with_retry_stream
        def stream(self) -> Iterator[str]:
            self.calls += 1
            yield "first"
            raise httpx2.ReadError("interrupted")

    client = Client()
    stream = client.stream()
    assert next(stream) == "first"
    with pytest.raises(httpx2.ReadError):
        next(stream)
    assert client.calls == 1


async def test_async_compatibility_stream_never_replays_delivered_item() -> None:
    class Client:
        _settings = Settings(max_retries=2)
        calls = 0

        @_awith_retry_stream
        async def stream(self) -> AsyncIterator[str]:
            self.calls += 1
            yield "first"
            raise httpx2.ReadError("interrupted")

    client = Client()
    stream = client.stream()
    assert await anext(stream) == "first"
    with pytest.raises(httpx2.ReadError):
        await anext(stream)
    assert client.calls == 1


@pytest.mark.parametrize("statuses", [[500, 401, 500], [401, 500, 200], [401, 401]])
async def test_async_auth_replay_keeps_total_status_retry_budget(
    statuses: list[int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statuses = list(statuses)
    events: list[str] = []

    async def no_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr("gigachat._execution.asyncio.sleep", no_sleep)

    async def handler(request: httpx2.Request) -> httpx2.Response:
        events.append(request.url.host)
        if request.url.host == "auth.test":
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(statuses.pop(0), json=MODELS)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            async_http_client=http,
            auth_async_http_client=http,
            access_token="old",
            credentials="dummy",
            max_retries=1,
        ) as sdk:
            if statuses[-1] == 200:
                await sdk.aget_models()
            else:
                with pytest.raises(ResponseError):
                    await sdk.aget_models()
    assert not statuses
    assert events.count("auth.test") == 1


def test_api_overrides_do_not_leak_to_oauth() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=OAUTH_TOKEN_VALID if request.url.host == "auth.test" else MODELS)

    with httpx2.Client(transport=httpx2.MockTransport(handler), headers={"X-Shared": "yes"}) as http:
        with GigaChat(
            base_url=BASE, auth_url=AUTH, http_client=http, auth_http_client=http, credentials="dummy"
        ) as sdk:
            sdk.get_models(request_options=RequestOptions(extra_headers={"X-API": "api"}, extra_query={"api": "query"}))
    assert len(seen) == 2
    assert seen[0].url.host == "auth.test"
    assert "X-API" not in seen[0].headers
    assert "api" not in seen[0].url.params
    assert seen[1].headers["X-API"] == "api"
    assert seen[1].url.params["api"] == "query"


@pytest.mark.parametrize("override", [{"storage": True}, {"custom_mutation": {"state": True}}])
def test_final_chat_body_override_disables_status_retry(override: dict[str, Any]) -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(503)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, http_client=http, max_retries=2) as sdk:
            with pytest.raises(ServerError):
                sdk.chat.create({"model": "model", "messages": []}, request_options=RequestOptions(extra_body=override))
    assert len(seen) == 1
    assert all(json.loads(seen[0].content)[name] == value for name, value in override.items())


def test_mutating_endpoint_does_not_retry_status() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(503)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, http_client=http, max_retries=2) as sdk:
            with pytest.raises(ServerError):
                sdk.assistants.create("model", "name")
    assert len(seen) == 1


def test_seekable_upload_401_replays_original_nonzero_offset() -> None:
    from tests.constants import FILES

    seen: list[httpx2.Request] = []
    upload = io.BytesIO(b"secret-prefix-visible-payload")
    upload.seek(len(b"secret-prefix-"))

    def handler(request: httpx2.Request) -> httpx2.Response:
        request.read()
        seen.append(request)
        if request.url.host == "auth.test":
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(401 if len(seen) == 1 else 200, json=FILES)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            http_client=http,
            auth_http_client=http,
            access_token="old",
            credentials="dummy",
        ) as sdk:
            sdk.upload_file(("file.txt", upload))
    uploads = [request for request in seen if request.url.host != "auth.test"]
    assert len(uploads) == 2
    for request in uploads:
        assert b"visible-payload" in request.content
        assert b"secret-prefix" not in request.content


def test_nonseekable_upload_refuses_401_replay() -> None:
    class NonSeekable(io.BytesIO):
        def seekable(self) -> bool:
            return False

    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(401)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            http_client=http,
            auth_http_client=http,
            access_token="old",
            credentials="dummy",
        ) as sdk:
            with pytest.raises(AuthenticationError):
                sdk.upload_file(("file.txt", NonSeekable(b"contents")))
    assert len(seen) == 1
    assert seen[0].url.host == "example.test"


def test_endpoint_query_values_survive_client_and_request_options() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(400)

    with httpx2.Client(transport=httpx2.MockTransport(handler), params=[("q", "client")]) as http:
        with GigaChat(base_url=BASE, http_client=http) as sdk:
            with pytest.raises(ResponseError):
                sdk.threads.get_messages(
                    "thread-1", limit=10, before=0, request_options=RequestOptions(extra_query=[("q", "call")])
                )
    assert seen[0].url.params["thread_id"] == "thread-1"
    assert seen[0].url.params["limit"] == "10"
    assert seen[0].url.params.get_list("q") == ["client", "call"]


@pytest.mark.parametrize(("name", "args", "kwargs", "stream"), ENDPOINTS, ids=[case[0] for case in ENDPOINTS])
def test_every_sync_endpoint_has_at_most_one_auth_replay(
    name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    stream: bool,
) -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=OAUTH_TOKEN_VALID) if request.url.host == "auth.test" else httpx2.Response(401)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            http_client=http,
            auth_http_client=http,
            access_token="old",
            credentials="dummy",
        ) as sdk:
            with pytest.raises(AuthenticationError):  # noqa: PT012 - invoke regular and streamed endpoints
                result = _method(sdk, name)(*copy.deepcopy(args), **copy.deepcopy(kwargs))
                if stream:
                    list(result)
    assert [request.url.host for request in seen] == ["example.test", "auth.test", "example.test"]
    assert seen[0].headers["Authorization"] == "Bearer old"
    assert seen[2].headers["Authorization"] == f"Bearer {OAUTH_TOKEN_VALID['access_token']}"


@pytest.mark.parametrize(("name", "args", "kwargs", "stream"), ENDPOINTS, ids=[case[0] for case in ENDPOINTS])
async def test_every_async_endpoint_has_at_most_one_auth_replay(
    name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    stream: bool,
) -> None:
    seen: list[httpx2.Request] = []

    async def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=OAUTH_TOKEN_VALID) if request.url.host == "auth.test" else httpx2.Response(401)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            async_http_client=http,
            auth_async_http_client=http,
            access_token="old",
            credentials="dummy",
        ) as sdk:
            with pytest.raises(AuthenticationError):  # noqa: PT012 - invoke regular and streamed endpoints
                result = _method(sdk, name, True)(*copy.deepcopy(args), **copy.deepcopy(kwargs))
                if inspect.isawaitable(result):
                    result = await result
                if stream:
                    _ = [chunk async for chunk in result]
    assert [request.url.host for request in seen] == ["example.test", "auth.test", "example.test"]
    assert seen[0].headers["Authorization"] == "Bearer old"
    assert seen[2].headers["Authorization"] == f"Bearer {OAUTH_TOKEN_VALID['access_token']}"


@pytest.mark.parametrize("primary", [False, True])
def test_configured_model_is_inserted_without_mutating_input(primary: bool) -> None:
    from tests.constants import CHAT_COMPLETION

    from gigachat.models import Chat

    payload: Any = ChatCompletionRequest(messages=[]) if primary else Chat(messages=[])
    original = payload.model_dump()
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=PRIMARY_CHAT_COMPLETION if primary else CHAT_COMPLETION)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, http_client=http, model="configured") as sdk:
            if primary:
                sdk.chat.create(payload)
            else:
                sdk.chat(payload)
    assert payload.model_dump() == original
    assert payload.model is None
    assert json.loads(seen[0].content)["model"] == "configured"


def test_stale_401_does_not_discard_a_newer_token() -> None:
    import threading
    from concurrent.futures import ThreadPoolExecutor

    barrier = threading.Barrier(2)
    refreshed = threading.Event()
    lock = threading.Lock()
    old_calls = 0
    auth_calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal old_calls, auth_calls
        if request.url.host == "auth.test":
            with lock:
                auth_calls += 1
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        if request.headers.get("Authorization") == "Bearer old":
            with lock:
                old_calls += 1
                index = old_calls
            barrier.wait(timeout=5)
            if index == 2:
                assert refreshed.wait(timeout=5)
            return httpx2.Response(401)
        refreshed.set()
        return httpx2.Response(200, json=MODELS)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            http_client=http,
            auth_http_client=http,
            access_token="old",
            credentials="dummy",
        ) as sdk:
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: sdk.get_models(), range(2)))
            assert sdk.token == OAUTH_TOKEN_VALID["access_token"]
    assert len(results) == 2
    assert old_calls == 2
    assert auth_calls == 1


async def test_async_stale_401_does_not_discard_a_newer_token() -> None:
    both_started = asyncio.Event()
    refreshed = asyncio.Event()
    old_calls = 0
    auth_calls = 0

    async def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal old_calls, auth_calls
        if request.url.host == "auth.test":
            auth_calls += 1
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        if request.headers.get("Authorization") == "Bearer old":
            old_calls += 1
            index = old_calls
            if old_calls == 2:
                both_started.set()
            await asyncio.wait_for(both_started.wait(), 5)
            if index == 2:
                await asyncio.wait_for(refreshed.wait(), 5)
            return httpx2.Response(401)
        refreshed.set()
        return httpx2.Response(200, json=MODELS)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            async_http_client=http,
            auth_async_http_client=http,
            access_token="old",
            credentials="dummy",
        ) as sdk:
            results = await asyncio.gather(sdk.aget_models(), sdk.aget_models())
            assert sdk.token == OAUTH_TOKEN_VALID["access_token"]
    assert len(results) == 2
    assert old_calls == 2
    assert auth_calls == 1


def test_concurrent_sync_requests_share_one_token_refresh() -> None:
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    barrier = threading.Barrier(10)
    auth_calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal auth_calls
        if request.url.host == "auth.test":
            auth_calls += 1
            time.sleep(0.01)
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(200, json=MODELS)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE, auth_url=AUTH, http_client=http, auth_http_client=http, credentials="dummy"
        ) as sdk:

            def request(index: int) -> Any:
                barrier.wait(timeout=5)
                return sdk.get_models()

            with ThreadPoolExecutor(max_workers=10) as executor:
                assert len(list(executor.map(request, range(10)))) == 10
    assert auth_calls == 1


async def test_concurrent_async_requests_share_one_token_refresh() -> None:
    auth_calls = 0

    async def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal auth_calls
        if request.url.host == "auth.test":
            auth_calls += 1
            await asyncio.sleep(0.01)
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(200, json=MODELS)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(
            base_url=BASE, auth_url=AUTH, async_http_client=http, auth_async_http_client=http, credentials="dummy"
        ) as sdk:
            assert len(await asyncio.gather(*(sdk.aget_models() for _ in range(10)))) == 10
    assert auth_calls == 1


async def test_cancelled_refresh_releases_lock_for_the_next_request() -> None:
    auth_started = asyncio.Event()
    auth_calls = 0

    async def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal auth_calls
        if request.url.host == "auth.test":
            auth_calls += 1
            if auth_calls == 1:
                auth_started.set()
                await asyncio.Event().wait()
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(200, json=MODELS)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(
            base_url=BASE, auth_url=AUTH, async_http_client=http, auth_async_http_client=http, credentials="dummy"
        ) as sdk:
            task = asyncio.create_task(sdk.aget_models())
            await asyncio.wait_for(auth_started.wait(), 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            result = await asyncio.wait_for(sdk.aget_models(), 5)
            assert result.data
            assert sdk.token == OAUTH_TOKEN_VALID["access_token"]
    assert auth_calls == 2


def test_retry_budget_expiry_during_oauth_keeps_fresh_token_without_resource_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    monkeypatch.setattr("gigachat._execution.time.monotonic", lambda: clock[0])
    hosts: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        hosts.append(request.url.host)
        if request.url.host == "auth.test":
            clock[0] = 2.0
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(401)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            http_client=http,
            auth_http_client=http,
            access_token="old",
            credentials="dummy",
            max_retry_time=1,
        ) as sdk:
            with pytest.raises(AuthenticationError):
                sdk.get_models()
            assert sdk.token == OAUTH_TOKEN_VALID["access_token"]
    assert hosts == ["example.test", "auth.test"]


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_response_hook_exception_preserves_type(asynchronous: bool) -> None:
    class HookFailure(Exception):
        pass

    def fail(response: httpx2.Response) -> None:
        raise HookFailure("hook failure")

    async def async_fail(response: httpx2.Response) -> None:
        fail(response)

    transport = httpx2.MockTransport(lambda request: httpx2.Response(200, json=MODELS))
    if asynchronous:
        async with httpx2.AsyncClient(transport=transport, event_hooks={"response": [async_fail]}) as http:
            async with GigaChat(base_url=BASE, async_http_client=http, max_retries=3) as sdk:
                with pytest.raises(HookFailure):
                    await sdk.aget_models()
    else:
        with httpx2.Client(transport=transport, event_hooks={"response": [fail]}) as sync_http:
            with GigaChat(base_url=BASE, http_client=sync_http, max_retries=3) as sdk:
                with pytest.raises(HookFailure):
                    sdk.get_models()


class _FirstChunkBody(httpx2.SyncByteStream, httpx2.AsyncByteStream):
    def __init__(self, fail: bool) -> None:
        self.fail = fail
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        if self.fail:
            raise httpx2.ReadError("body interrupted before first chunk")
        yield CHAT_COMPLETION_STREAM

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self:
            yield chunk

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_stream_failure_before_first_chunk_can_retry(asynchronous: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    bodies: list[_FirstChunkBody] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        body = _FirstChunkBody(not bodies)
        bodies.append(body)
        return httpx2.Response(200, stream=body, headers={"content-type": "text/event-stream"})

    async def no_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr("gigachat._execution.time.sleep", lambda delay: None)
    monkeypatch.setattr("gigachat._execution.asyncio.sleep", no_sleep)
    transport = httpx2.MockTransport(handler)
    if asynchronous:
        async with httpx2.AsyncClient(transport=transport) as http:
            async with GigaChat(base_url=BASE, async_http_client=http, max_retries=1) as sdk:
                chunks = [chunk async for chunk in sdk.astream({"model": "model", "messages": []})]
    else:
        with httpx2.Client(transport=transport) as sync_http:
            with GigaChat(base_url=BASE, http_client=sync_http, max_retries=1) as sdk:
                chunks = list(sdk.stream({"model": "model", "messages": []}))
    assert len(chunks) == 3
    assert len(bodies) == 2
    assert all(body.closed for body in bodies)


async def test_async_retry_budget_expiry_during_oauth_keeps_fresh_token_without_resource_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    monkeypatch.setattr("gigachat._execution.time.monotonic", lambda: clock[0])
    hosts: list[str] = []

    async def handler(request: httpx2.Request) -> httpx2.Response:
        hosts.append(request.url.host)
        if request.url.host == "auth.test":
            clock[0] = 2.0
            return httpx2.Response(200, json=OAUTH_TOKEN_VALID)
        return httpx2.Response(401)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(
            base_url=BASE,
            auth_url=AUTH,
            async_http_client=http,
            auth_async_http_client=http,
            access_token="old",
            credentials="dummy",
            max_retry_time=1,
        ) as sdk:
            with pytest.raises(AuthenticationError):
                await sdk.aget_models()
            assert sdk.token == OAUTH_TOKEN_VALID["access_token"]
    assert hosts == ["example.test", "auth.test"]


async def test_async_owner_close_invalidates_views_and_preserves_borrowed_client() -> None:
    transport = httpx2.MockTransport(lambda request: httpx2.Response(200, json=MODELS))
    async with httpx2.AsyncClient(transport=transport) as http:
        sdk = GigaChat(base_url=BASE, async_http_client=http)
        view = sdk.with_options(extra_headers={"X-View": "view"})
        await view.aget_models()
        await sdk.aclose()
        await sdk.aclose()
        sdk.close()
        with pytest.raises(RuntimeError, match="closed"):
            sdk.with_options(timeout=1)
        assert not http.is_closed
        assert (await http.get("https://other.test")).status_code == 200
        with pytest.raises(RuntimeError, match="closed"):
            await view.aget_models()


async def test_hybrid_close_releases_only_sync_side_and_aclose_releases_both(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx2.MockTransport(lambda request: httpx2.Response(200, json=MODELS))
    sync_http = httpx2.Client(transport=transport)
    async_http = httpx2.AsyncClient(transport=transport)
    monkeypatch.setattr("gigachat.client.DefaultHttpxClient", lambda **kwargs: sync_http)
    monkeypatch.setattr("gigachat.client.DefaultAsyncHttpxClient", lambda **kwargs: async_http)
    sdk = GigaChat(trust_env=False, base_url=BASE)
    sdk.get_models()
    await sdk.aget_models()
    sdk.close()
    assert sync_http.is_closed
    assert not async_http.is_closed
    assert (await sdk.aget_models()).data
    with pytest.raises(RuntimeError, match="closed"):
        sdk.get_models()
    await sdk.aclose()
    assert async_http.is_closed
    with pytest.raises(RuntimeError, match="closed"):
        await sdk.aget_models()


async def test_closing_view_invalidates_only_that_view() -> None:
    transport = httpx2.MockTransport(lambda request: httpx2.Response(200, json=MODELS))
    with httpx2.Client(transport=transport) as sync_http:
        async with httpx2.AsyncClient(transport=transport) as async_http:
            async with GigaChat(base_url=BASE, http_client=sync_http, async_http_client=async_http) as sdk:
                view = sdk.with_options(extra_headers={"X-View": "one"})
                await view.aget_models()
                view.close()
                with pytest.raises(RuntimeError, match="closed"):
                    view.get_models()
                with pytest.raises(RuntimeError, match="closed"):
                    await view.aget_models()
                with pytest.raises(RuntimeError, match="closed"):
                    view.with_options(timeout=1)
                assert sdk.get_models().data
                assert (await sdk.aget_models()).data
                other = sdk.with_options(extra_headers={"X-View": "two"})
                await other.aclose()
                assert sdk.get_models().data
                assert (await sdk.aget_models()).data
                assert not sync_http.is_closed
                assert not async_http.is_closed


def test_async_client_rejects_a_different_event_loop() -> None:
    transport = httpx2.MockTransport(lambda request: httpx2.Response(200, json=MODELS))
    http = httpx2.AsyncClient(transport=transport)
    sdk = GigaChat(base_url=BASE, async_http_client=http)
    first = asyncio.new_event_loop()
    second = asyncio.new_event_loop()
    try:
        assert first.run_until_complete(sdk.aget_models()).data
        with pytest.raises(RuntimeError, match="different event loop"):
            second.run_until_complete(sdk.aget_models())
    finally:
        first.run_until_complete(sdk.aclose())
        first.run_until_complete(http.aclose())
        first.close()
        second.close()


def test_lazy_sync_initialization_and_close_share_one_lifecycle_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    import threading
    from concurrent.futures import ThreadPoolExecutor

    creating = threading.Event()
    release = threading.Event()
    closing = threading.Event()
    closed = threading.Event()
    http = httpx2.Client(transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json=MODELS)))
    factory_calls = 0

    def factory(**kwargs: Any) -> httpx2.Client:
        nonlocal factory_calls
        factory_calls += 1
        creating.set()
        assert release.wait(timeout=5)
        return http

    monkeypatch.setattr("gigachat.client.DefaultHttpxClient", factory)
    sdk = GigaChat(base_url=BASE, trust_env=False)

    def close() -> None:
        closing.set()
        sdk.close()
        closed.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        initialized = executor.submit(lambda: sdk._client)
        assert creating.wait(timeout=5)
        finished = executor.submit(close)
        assert closing.wait(timeout=5)
        assert not closed.wait(timeout=0.02)
        release.set()
        assert initialized.result(timeout=5) is http
        finished.result(timeout=5)
    assert closed.is_set()
    assert http.is_closed
    assert factory_calls == 1
    with pytest.raises(RuntimeError, match="closed"):
        sdk.get_models()
    assert factory_calls == 1


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_password_token_uses_sdk_url_instead_of_borrowed_client_url(asynchronous: bool) -> None:
    from tests.constants import PASSWORD_TOKEN_VALID

    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=PASSWORD_TOKEN_VALID if request.url.path.endswith("/token") else MODELS)

    transport = httpx2.MockTransport(handler)
    if asynchronous:
        async with httpx2.AsyncClient(transport=transport, base_url="https://wrong.test/unused") as http:
            async with GigaChat(base_url=BASE, async_http_client=http, user="user", password="password") as sdk:
                await sdk.aget_models()
    else:
        with httpx2.Client(transport=transport, base_url="https://wrong.test/unused") as sync_http:
            with GigaChat(base_url=BASE, http_client=sync_http, user="user", password="password") as sdk:
                sdk.get_models()
    assert [str(request.url) for request in seen] == [BASE + "/token", BASE + "/models"]
    assert seen[0].headers["Authorization"].startswith("Basic ")
    assert seen[1].headers["Authorization"].startswith("Bearer ")


def test_retry_snapshots_borrowed_client_defaults_and_context(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[httpx2.Request] = []
    context_token = custom_headers_cvar.set({"X-Context": "initial"})
    monkeypatch.setattr("gigachat._execution.time.sleep", lambda delay: None)

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        if len(seen) == 1:
            http.headers["X-Default"] = "changed"
            http.headers["X-Late"] = "late"
            http.headers["Authorization"] = "Bearer late-external"
            http.cookies.set("session", "changed")
            http.cookies.set("late", "late")
            http.params = {"client": "changed", "late": "late"}
            http.timeout.read = 77
            http.timeout = httpx2.Timeout(99)
            custom_headers_cvar.set({"X-Context": "changed"})
            return httpx2.Response(503, headers={"set-cookie": "server=late; Path=/"})
        return httpx2.Response(200, json=MODELS)

    try:
        with httpx2.Client(
            transport=httpx2.MockTransport(handler),
            headers={"X-Default": "initial"},
            cookies={"session": "initial"},
            params={"client": "initial"},
            timeout=11,
        ) as http:
            with GigaChat(base_url=BASE, http_client=http, access_token="fixed", max_retries=1) as sdk:
                sdk.get_models()
            assert http.headers["X-Default"] == "changed"
    finally:
        custom_headers_cvar.reset(context_token)
    assert len(seen) == 2
    for request in seen:
        assert request.headers["X-Default"] == "initial"
        assert request.headers["X-Context"] == "initial"
        assert request.headers["Authorization"] == "Bearer fixed"
        assert "X-Late" not in request.headers
        assert request.headers["Cookie"] == "session=initial"
        assert request.url.params == httpx2.QueryParams({"client": "initial"})
        assert request.extensions["timeout"] == {"connect": 11, "read": 11, "write": 11, "pool": 11}


@pytest.mark.parametrize("same_view", [False, True])
def test_nested_sync_callback_starts_fresh_request_options(same_view: bool) -> None:
    seen: list[httpx2.Request] = []
    entered = False
    inner: Any = None

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal entered
        seen.append(request)
        if not entered:
            entered = True
            inner.get_models()
        return httpx2.Response(200, json=MODELS)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, http_client=http) as sdk:
            outer = sdk.with_options(extra_headers={"X-View": "outer"}, extra_query={"view": "outer"})
            inner = (
                outer
                if same_view
                else sdk.with_options(extra_headers={"X-View": "inner"}, extra_query={"view": "inner"})
            )
            outer.get_models(request_options=RequestOptions(extra_headers={"X-Call": "outer-only"}))
    assert len(seen) == 2
    assert seen[0].headers["X-Call"] == "outer-only"
    assert seen[1].headers["X-View"] == ("outer" if same_view else "inner")
    assert seen[1].url.params["view"] == ("outer" if same_view else "inner")
    assert "X-Call" not in seen[1].headers


@pytest.mark.parametrize("same_view", [False, True])
async def test_nested_async_callback_starts_fresh_request_options(same_view: bool) -> None:
    seen: list[httpx2.Request] = []
    entered = False
    inner: Any = None

    async def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal entered
        seen.append(request)
        if not entered:
            entered = True
            await inner.aget_models()
        return httpx2.Response(200, json=MODELS)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(base_url=BASE, async_http_client=http) as sdk:
            outer = sdk.with_options(extra_headers={"X-View": "outer"}, extra_query={"view": "outer"})
            inner = (
                outer
                if same_view
                else sdk.with_options(extra_headers={"X-View": "inner"}, extra_query={"view": "inner"})
            )
            await outer.aget_models(request_options=RequestOptions(extra_headers={"X-Call": "outer-only"}))
    assert len(seen) == 2
    assert seen[0].headers["X-Call"] == "outer-only"
    assert seen[1].headers["X-View"] == ("outer" if same_view else "inner")
    assert seen[1].url.params["view"] == ("outer" if same_view else "inner")
    assert "X-Call" not in seen[1].headers


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_stream_retry_reuses_input_snapshot_from_first_iteration(
    asynchronous: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload: dict[str, Any] = {"model": "model", "messages": [{"role": "user", "content": "before-creation"}]}
    seen: list[dict[str, Any]] = []
    bodies: list[_FirstChunkBody] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(json.loads(request.content))
        payload["messages"][0]["content"] = "changed-during-first-attempt"
        body = _FirstChunkBody(not bodies)
        bodies.append(body)
        return httpx2.Response(200, stream=body, headers={"content-type": "text/event-stream"})

    async def no_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr("gigachat._execution.time.sleep", lambda delay: None)
    monkeypatch.setattr("gigachat._execution.asyncio.sleep", no_sleep)
    transport = httpx2.MockTransport(handler)
    if asynchronous:
        async with httpx2.AsyncClient(transport=transport) as http:
            async with GigaChat(base_url=BASE, async_http_client=http, max_retries=1) as sdk:
                stream = sdk.astream(payload)
                payload["messages"][0]["content"] = "at-first-iteration"
                chunks = [chunk async for chunk in stream]
    else:
        with httpx2.Client(transport=transport) as sync_http:
            with GigaChat(base_url=BASE, http_client=sync_http, max_retries=1) as sdk:
                sync_stream = sdk.stream(payload)
                payload["messages"][0]["content"] = "at-first-iteration"
                chunks = list(sync_stream)
    assert len(chunks) == 3
    assert len(seen) == 2
    assert [body["messages"][0]["content"] for body in seen] == ["at-first-iteration", "at-first-iteration"]
    assert payload["messages"][0]["content"] == "changed-during-first-attempt"
    assert all(body.closed for body in bodies)


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_stream_input_validation_preserves_pydantic_error(asynchronous: bool) -> None:
    from pydantic import ValidationError

    calls: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        raise AssertionError("Invalid user input reached the network transport")

    invalid = {"model": "model", "messages": "invalid-list"}
    transport = httpx2.MockTransport(handler)
    if asynchronous:
        async with httpx2.AsyncClient(transport=transport) as http:
            async with GigaChat(base_url=BASE, async_http_client=http, max_retries=3) as sdk:
                with pytest.raises(ValidationError):
                    await anext(sdk.astream(invalid))
    else:
        with httpx2.Client(transport=transport) as sync_http:
            with GigaChat(base_url=BASE, http_client=sync_http, max_retries=3) as sdk:
                with pytest.raises(ValidationError):
                    next(sdk.stream(invalid))
    assert calls == []


def test_view_get_token_returns_shared_refreshed_owner_token() -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json=OAUTH_TOKEN_VALID)

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http:
        with GigaChat(base_url=BASE, auth_url=AUTH, auth_http_client=http, credentials="dummy") as sdk:
            view = sdk.with_options(extra_headers={"X-View": "before-refresh"})
            refreshed = view.get_token()
            assert refreshed is not None
            assert refreshed.access_token == OAUTH_TOKEN_VALID["access_token"]
            assert refreshed is sdk.get_token()
            assert view.token == sdk.token
    assert calls == 1


async def test_view_aget_token_returns_shared_refreshed_owner_token() -> None:
    calls = 0

    async def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(200, json=OAUTH_TOKEN_VALID)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as http:
        async with GigaChat(base_url=BASE, auth_url=AUTH, auth_async_http_client=http, credentials="dummy") as sdk:
            view = sdk.with_options(extra_headers={"X-View": "before-refresh"})
            refreshed = await view.aget_token()
            assert refreshed is not None
            assert refreshed.access_token == OAUTH_TOKEN_VALID["access_token"]
            assert refreshed is await sdk.aget_token()
            assert view.token == sdk.token
    assert calls == 1
