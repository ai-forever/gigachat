"""Shared request execution, auth replay and bounded retry policy."""

from __future__ import annotations

import asyncio
import copy
import functools
import inspect
import json
import random
import time
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, ParamSpec, TypeVar, cast, overload

import httpx2
from pydantic import BaseModel

from gigachat._request_options import NotGiven, RequestOptions
from gigachat._serialization import BodyReplay
from gigachat._streaming import AsyncStream, Stream
from gigachat.exceptions import APIConnectionError, APITimeoutError, ResponseError

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class RequestState:
    owner: Any
    view: Any
    options: RequestOptions
    context_headers: dict[str, str]
    response: httpx2.Response | None = None
    prepared: PreparedRequest | None = None
    reopening: bool = False
    in_send: bool = False


current_request: ContextVar[RequestState | None] = ContextVar("gigachat_request", default=None)


def _state(instance: Any, options: RequestOptions | None) -> RequestState:
    from gigachat.api.utils import build_headers

    client = getattr(instance, "_base_client", instance)
    client._ensure_open()
    owner = getattr(client, "_owner", client)
    existing = current_request.get()
    if existing is not None and existing.view is client and not existing.in_send and options is None:
        return existing
    return RequestState(owner, client, client._request_options.merge(options), build_headers())


def _stream_retry(state: RequestState, error: Exception, yielded: bool) -> float | None:
    prepared = state.prepared
    if yielded or prepared is None:
        return None
    cause = error.__cause__ if isinstance(error, APIConnectionError) else error
    if not isinstance(cause, Exception):
        return None
    prepared.begin_failure(cause)
    delay = prepared.retry_delay(cause)
    if delay is not None:
        state.reopening = True
    return delay


def _sync_stream_scope(func: F) -> F:
    @functools.wraps(func)
    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        from gigachat._streaming import Stream

        options = kwargs.pop("request_options", None)
        state: RequestState | None = None

        def iterate() -> Iterator[Any]:
            nonlocal state
            state = _state(self, options)
            yielded = False
            call_args, call_kwargs = copy.deepcopy(args), copy.deepcopy(kwargs)
            iterator = func(self, *call_args, **call_kwargs)
            try:
                while True:
                    token = current_request.set(state)
                    try:
                        item = next(iterator)
                    except StopIteration:
                        return
                    except Exception as error:
                        delay = _stream_retry(state, error, yielded)
                        if delay is None:
                            raise
                        iterator.close()
                        time.sleep(delay)
                        iterator = func(self, *call_args, **call_kwargs)
                        continue
                    finally:
                        current_request.reset(token)
                    yielded = True
                    yield item
            finally:
                iterator.close()

        return Stream.from_iterator(iterate(), response_getter=lambda: state.response if state else None)

    return cast(F, wrapped)


def _async_stream_scope(func: F) -> F:
    @functools.wraps(func)
    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        from gigachat._streaming import AsyncStream

        options = kwargs.pop("request_options", None)
        state: RequestState | None = None

        async def iterate() -> AsyncIterator[Any]:
            nonlocal state
            state = _state(self, options)
            yielded = False
            call_args, call_kwargs = copy.deepcopy(args), copy.deepcopy(kwargs)
            iterator = func(self, *call_args, **call_kwargs)
            try:
                while True:
                    token = current_request.set(state)
                    try:
                        item = await iterator.__anext__()
                    except StopAsyncIteration:
                        return
                    except Exception as error:
                        delay = _stream_retry(state, error, yielded)
                        if delay is None:
                            raise
                        await iterator.aclose()
                        await asyncio.sleep(delay)
                        iterator = func(self, *call_args, **call_kwargs)
                        continue
                    finally:
                        current_request.reset(token)
                    yielded = True
                    yield item
            finally:
                await iterator.aclose()

        return AsyncStream.from_iterator(iterate(), response_getter=lambda: state.response if state else None)

    return cast(F, wrapped)


P = ParamSpec("P")
ModelT = TypeVar("ModelT", bound=BaseModel)
ReturnT = TypeVar("ReturnT")


@overload
def request_scope(func: Callable[P, AsyncIterator[ModelT]]) -> Callable[P, AsyncStream[ModelT]]: ...


@overload
def request_scope(func: Callable[P, Iterator[ModelT]]) -> Callable[P, Stream[ModelT]]: ...


@overload
def request_scope(func: Callable[P, ReturnT]) -> Callable[P, ReturnT]: ...


def request_scope(func: Callable[..., Any]) -> Callable[..., Any]:
    """Establish isolated request options and stream cleanup with one shared retry budget."""
    if inspect.isasyncgenfunction(func):
        return _async_stream_scope(func)
    if inspect.isgeneratorfunction(func):
        return _sync_stream_scope(func)
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def asynchronous(self: Any, *args: Any, **kwargs: Any) -> Any:
            options = kwargs.pop("request_options", None)
            token = current_request.set(_state(self, options))
            try:
                return await func(self, *args, **kwargs)
            finally:
                current_request.reset(token)

        return asynchronous

    @functools.wraps(func)
    def synchronous(self: Any, *args: Any, **kwargs: Any) -> Any:
        options = kwargs.pop("request_options", None)
        token = current_request.set(_state(self, options))
        try:
            return func(self, *args, **kwargs)
        finally:
            current_request.reset(token)

    return synchronous


def _prepared(client: Any, kwargs: dict[str, Any], state: RequestState | None) -> PreparedRequest:
    if state is not None and state.reopening and state.prepared is not None:
        state.reopening = False
        return state.prepared
    prepared = PreparedRequest(client, kwargs, state)
    if state is not None:
        state.prepared = prepared
    return prepared


class PreparedRequest:
    def __init__(self, client: Any, kwargs: dict[str, Any], state: RequestState | None) -> None:
        self.client, self.state = client, state
        self.kwargs = dict(kwargs)
        self.cookies = httpx2.Cookies(client.cookies)
        self.default_headers = httpx2.Headers(client.headers)
        self.kwargs.setdefault("timeout", copy.deepcopy(client.timeout))
        self.external_auth = False
        self.retry_count = 0
        self.auth_replays = 0
        self.started: float | None = None
        self.last_error: Exception | None = None
        self.generation = 0
        self.max_retries = 0
        self.budget = 60.0
        self.factor = 0.5
        self.codes: tuple[int, ...] = ()
        if state is not None:
            owner, options = state.owner, state.options
            settings = owner._settings
            self.max_retries = (
                settings.max_retries if isinstance(options.max_retries, NotGiven) else options.max_retries
            )
            self.budget = (
                settings.max_retry_time if isinstance(options.max_retry_time, NotGiven) else options.max_retry_time
            )
            self.factor, self.codes = settings.retry_backoff_factor, settings.retry_on_status_codes
            # Routing is always determined by the SDK, including borrowed clients.
            url = httpx2.URL(self.kwargs["url"])
            if url.is_relative_url:
                url = httpx2.URL(settings.base_url.rstrip("/") + "/" + str(url).lstrip("/"))
            pairs = (
                list(url.params.multi_items())
                + list(httpx2.QueryParams(self.kwargs.pop("params", None)).multi_items())
                + list(client.params.multi_items())
                + options.extra_query
            )
            url = url.copy_with(query=str(httpx2.QueryParams(pairs)).encode() if pairs else None)
            self.kwargs["url"] = url
            headers = httpx2.Headers(client.headers)
            defaults = httpx2.Headers()
            if settings.session_id:
                defaults["X-Session-ID"] = settings.session_id
            defaults.update(headers)
            external = httpx2.Headers(client.headers)
            external.update(state.context_headers)
            external.update(options.extra_headers)
            self.external_auth = "authorization" in external
            defaults.update(self.kwargs.get("headers", {}))
            defaults.update(state.context_headers)
            defaults.update(options.extra_headers)
            if self.external_auth:
                defaults["Authorization"] = external["authorization"]
            self.kwargs["headers"] = defaults
            if not isinstance(options.timeout, NotGiven):
                self.kwargs["timeout"] = options.timeout
            if options.extra_body:
                content = self.kwargs.get("content")
                content_type = httpx2.Headers(kwargs.get("headers", {})).get("content-type", "")
                json_body = "json" in self.kwargs or content_type.split(";", 1)[0].strip().lower() == "application/json"
                if self.kwargs.get("files") or not json_body or (content is None and "json" not in self.kwargs):
                    raise ValueError("extra_body is supported only for JSON endpoints")
                body = (
                    copy.deepcopy(self.kwargs.get("json")) if "json" in self.kwargs else json.loads(cast(str, content))
                )
                if not isinstance(body, dict):
                    raise ValueError("extra_body requires a JSON object")
                if "stream" in options.extra_body and options.extra_body["stream"] != body.get("stream", False):
                    raise ValueError("extra_body.stream conflicts with the selected request method")
                body.update(options.extra_body)
                self.kwargs.update(
                    {"json": body} if "json" in self.kwargs else {"content": json.dumps(body, ensure_ascii=False)}
                )
        self.replay = BodyReplay(self.kwargs)
        self.safe = self._safe_operation()

    def _safe_operation(self) -> bool:
        if self.kwargs["method"].upper() in ("GET", "HEAD", "OPTIONS"):
            return True
        path = httpx2.URL(self.kwargs["url"]).path
        if path.endswith(("/embeddings", "/tokens/count", "/ai/check", "/functions/convert")):
            return True
        if path.endswith("/chat/completions"):
            from gigachat.models.chat import Chat
            from gigachat.models.chat_completions import ChatCompletionRequest

            body = self.kwargs.get("json") or json.loads(self.kwargs.get("content") or "{}")
            storage = body.get("storage")
            if isinstance(storage, dict) or storage is True:
                return False
            if any(body.get(k) for k in ("assistant_id", "thread_id", "run_id")):
                return False
            known = {
                field.alias or name
                for model in (Chat, ChatCompletionRequest)
                for name, field in model.model_fields.items()
            } | {"stream"}
            if body.keys() - known:
                return False
            # Unknown body overrides can carry mutation semantics: opt out conservatively.
            if self.state and self.state.options.extra_body:
                return False
            return True
        return False

    def remaining(self) -> float:
        return self.budget if self.started is None else self.budget - (time.monotonic() - self.started)

    def begin_failure(self, error: Exception) -> None:
        if self.started is None:
            self.started = time.monotonic()
        self.last_error = error

    def headers(self) -> None:
        if self.state is not None and not self.external_auth:
            owner = self.state.owner
            with owner._token_state_lock:
                self.generation = owner._token_generation
                token = owner.token
            headers = self.kwargs["headers"]
            headers.pop("authorization", None)
            if token:
                headers["Authorization"] = f"Bearer {token}"

    def auth_retry(self, error: Exception) -> bool:
        return bool(
            self.state
            and isinstance(error, ResponseError)
            and error.status_code == 401
            and self.state.owner._use_auth
            and not self.external_auth
            and self.auth_replays == 0
            and self.replay.replayable
            and self.remaining() > 0
        )

    def retry_delay(self, error: Exception) -> float | None:
        from gigachat.retry import _should_retry

        if self.retry_count >= self.max_retries or not self.replay.replayable or not _should_retry(error, self.codes):
            return None
        if not self.safe and not isinstance(error, httpx2.ConnectError):
            return None
        server_delay = error.retry_after if isinstance(error, ResponseError) else 0.0
        delay = server_delay or min(self.factor * 2 ** min(self.retry_count, 30) + random.uniform(0, 0.5), 60.0)
        if delay >= self.remaining():
            return None
        self.retry_count += 1
        return delay

    def build(self) -> httpx2.Request:
        if self.last_error is not None and self.remaining() <= 0:
            raise self.last_error
        self.headers()
        self.replay.rewind()
        kwargs = dict(self.kwargs)
        kwargs.pop("auth", None)
        request = self.client.build_request(**kwargs)
        if self.state is not None:
            frozen_headers = httpx2.Headers(self.kwargs.get("headers", self.default_headers))
            # Keep only HTTP framing calculated for this exact encoded body.
            for name in ("host", "content-length", "transfer-encoding", "content-type"):
                if name not in frozen_headers and name in request.headers:
                    frozen_headers[name] = request.headers[name]
            request.headers = frozen_headers
            if "cookie" not in request.headers:
                self.cookies.set_cookie_header(request)
        # build_request appends client query defaults; restore exact ordered query.
        if self.state is not None:
            request.url = httpx2.URL(kwargs["url"])
        return cast(httpx2.Request, request)


def _network_error(error: Exception) -> None:
    if isinstance(error, httpx2.TimeoutException):
        raise APITimeoutError() from error
    if isinstance(error, httpx2.TransportError) and not isinstance(error, httpx2.SSEError):
        raise APIConnectionError() from error
    raise error


def _status(response: httpx2.Response) -> None:
    if response.status_code >= 400:
        from gigachat.api.utils import _raise_for_status

        _raise_for_status(response.url, response.status_code, response.content, response.headers)


def _refresh(prepared: PreparedRequest, *, invalidate: bool = False) -> None:
    if not prepared.state or prepared.external_auth:
        return
    owner = prepared.state.owner
    if invalidate:
        owner._reset_token(prepared.generation)
    token = current_request.set(None)
    try:
        if owner._use_auth:
            owner._update_token()
    finally:
        current_request.reset(token)


async def _arefresh(prepared: PreparedRequest, *, invalidate: bool = False) -> None:
    if not prepared.state or prepared.external_auth:
        return
    owner = prepared.state.owner
    if invalidate:
        owner._reset_token(prepared.generation)
    token = current_request.set(None)
    try:
        if owner._use_auth:
            await owner._aupdate_token()
    finally:
        current_request.reset(token)


@contextmanager
def _sending(state: RequestState | None) -> Iterator[None]:
    if state:
        state.in_send = True
    try:
        yield
    finally:
        if state:
            state.in_send = False


def send_sync(client: httpx2.Client, *, stream: bool = False, **kwargs: Any) -> httpx2.Response:
    state = current_request.get()
    prepared = _prepared(client, kwargs, state)
    _refresh(prepared)
    while True:
        response = None
        try:
            request = prepared.build()
            with _sending(state):
                response = client.send(request, stream=stream, auth=kwargs.get("auth") if state is None else None)
            if response.status_code >= 400:
                response.read()
            _status(response)
            if state:
                state.response = response
            return response
        except BaseException as error:
            if response is not None:
                response.close()
            if not isinstance(error, Exception):
                raise
            prepared.begin_failure(error)
            if prepared.auth_retry(error):
                prepared.auth_replays += 1
                _refresh(prepared, invalidate=True)
                continue
            delay = prepared.retry_delay(error)
            if delay is None:
                _network_error(error)
            time.sleep(cast(float, delay))


async def send_async(client: httpx2.AsyncClient, *, stream: bool = False, **kwargs: Any) -> httpx2.Response:
    state = current_request.get()
    if state:
        state.owner._ensure_async_loop()
    prepared = _prepared(client, kwargs, state)
    await _arefresh(prepared)
    while True:
        response = None
        try:
            request = prepared.build()
            with _sending(state):
                response = await client.send(request, stream=stream, auth=kwargs.get("auth") if state is None else None)
            if response.status_code >= 400:
                await response.aread()
            _status(response)
            if state:
                state.response = response
            return response
        except BaseException as error:
            if response is not None:
                await response.aclose()
            if not isinstance(error, Exception):
                raise
            prepared.begin_failure(error)
            if prepared.auth_retry(error):
                prepared.auth_replays += 1
                await _arefresh(prepared, invalidate=True)
                continue
            delay = prepared.retry_delay(error)
            if delay is None:
                _network_error(error)
            await asyncio.sleep(cast(float, delay))


def request_sync(client: httpx2.Client, **kwargs: Any) -> httpx2.Response:
    return send_sync(client, **kwargs)


async def request_async(client: httpx2.AsyncClient, **kwargs: Any) -> httpx2.Response:
    return await send_async(client, **kwargs)


@contextmanager
def stream_sync(client: httpx2.Client, **kwargs: Any) -> Iterator[httpx2.Response]:
    response = send_sync(client, stream=True, **kwargs)
    try:
        yield response
    finally:
        response.close()


@asynccontextmanager
async def stream_async(client: httpx2.AsyncClient, **kwargs: Any) -> AsyncIterator[httpx2.Response]:
    response = await send_async(client, stream=True, **kwargs)
    try:
        yield response
    finally:
        await response.aclose()
