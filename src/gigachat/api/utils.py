import json
import logging
import re
from collections.abc import AsyncIterator, Iterator
from http import HTTPStatus
from typing import (
    Any,
    NoReturn,
    TypeVar,
)
from urllib.parse import urlsplit, urlunsplit

import httpx2 as httpx
from pydantic import BaseModel, ValidationError

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
from gigachat.exceptions import (
    APIResponseValidationError,
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RequestEntityTooLargeError,
    ResponseError,
    ServerError,
    UnprocessableEntityError,
)
from gigachat.models.base import APIResponse

logger = logging.getLogger(__name__)

USER_AGENT = "GigaChat-python-lib"
EVENT_STREAM = "text/event-stream"


_VERSIONED_PATH = re.compile(r"^/(api/)?v\d+(/|$)")
_VERSION_SUFFIX = re.compile(r"/v\d+$")


def _base_url(client: httpx.Client | httpx.AsyncClient) -> str:
    from gigachat._core.execution import current_request

    state = current_request.get()
    return str(state.owner._settings.base_url if state is not None else client.base_url)


def _at_origin(client: httpx.Client | httpx.AsyncClient, path: str) -> str:
    base = urlsplit(_base_url(client))
    return urlunsplit((base.scheme, base.netloc, path, "", ""))


def resolve_request_url(client: httpx.Client | httpx.AsyncClient, url: str) -> str:
    """Anchor versioned absolute paths (e.g. ``/v1/...``, ``/api/v2/...``) at the client's origin."""
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        return url
    if _VERSIONED_PATH.match(url):
        return _at_origin(client, url)
    return url


def resolve_primary_chat_url(client: httpx.Client | httpx.AsyncClient, override: str | None) -> str:
    """Resolve the primary chat URL, rewriting any ``/vN`` suffix in ``base_url`` to ``/v2``."""
    if override is not None:
        return resolve_request_url(client, override)
    base_path = urlsplit(_base_url(client)).path.rstrip("/")
    if not _VERSION_SUFFIX.search(base_path):
        return "/chat/completions"
    return _at_origin(client, _VERSION_SUFFIX.sub("/v2/chat/completions", base_path))


def build_headers(access_token: str | None = None) -> dict[str, str]:
    """Build headers for the request."""
    headers = httpx.Headers()

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    headers["User-Agent"] = USER_AGENT

    context_vars = {
        "Authorization": authorization_cvar,
        "X-Session-ID": session_id_cvar,
        "X-Request-ID": request_id_cvar,
        "X-Service-ID": service_id_cvar,
        "X-Operation-ID": operation_id_cvar,
        "X-Client-ID": client_id_cvar,
        "X-Trace-ID": trace_id_cvar,
        "X-Agent-ID": agent_id_cvar,
    }

    for header, cvar in context_vars.items():
        value = cvar.get()
        if value:
            headers[header] = value

    custom_headers = custom_headers_cvar.get()
    if custom_headers:
        headers.update(custom_headers)
    canonical = {name.lower(): name for name in ("User-Agent", *context_vars)}
    return {
        canonical.get(key.decode().lower(), key.decode()): value.decode(headers.encoding) for key, value in headers.raw
    }


T = TypeVar("T", bound=BaseModel)


def parse_data_chunk(line: str, model_class: type[T]) -> T | None:
    """Parse an SSE data line."""
    name, _, value = line.partition(":")
    if name == "data":
        value = value.lstrip()
        if value == "[DONE]":
            return None
        return model_class.model_validate_json(value)
    return None


def parse_chunk(line: str, model_class: type[T]) -> T | None:
    """Parse an SSE data line."""
    return parse_data_chunk(line, model_class)


def parse_event_chunk(event: str | None, data: str, model_class: type[T]) -> T:
    """Parse an SSE event with an optional event name."""
    payload = json.loads(data)
    if event and isinstance(payload, dict):
        payload.setdefault("event", event)
    return model_class.model_validate(payload)


def build_x_headers(response: httpx.Response) -> dict[str, str | None]:
    """Extract X-Headers from response."""
    return {
        "x-request-id": response.headers.get("x-request-id"),
        "x-session-id": response.headers.get("x-session-id"),
        "x-client-id": response.headers.get("x-client-id"),
    }


def _check_content_type(response: httpx.Response) -> None:
    content_type, _, _ = response.headers.get("content-type", "").partition(";")
    if content_type.strip().lower() != EVENT_STREAM:
        raise APIResponseValidationError(
            f"Expected response Content-Type to be '{EVENT_STREAM}', got {content_type!r}",
            request_id=response.headers.get("x-request-id"),
        )


def _raise_for_status(url: httpx.URL | str, status_code: int, content: bytes, headers: httpx.Headers) -> NoReturn:
    if status_code == HTTPStatus.BAD_REQUEST:
        raise BadRequestError(url, status_code, content, headers)
    elif status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(url, status_code, content, headers)
    elif status_code == HTTPStatus.FORBIDDEN:
        raise ForbiddenError(url, status_code, content, headers)
    elif status_code == HTTPStatus.NOT_FOUND:
        raise NotFoundError(url, status_code, content, headers)
    elif status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
        raise RequestEntityTooLargeError(url, status_code, content, headers)
    elif status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        raise UnprocessableEntityError(url, status_code, content, headers)
    elif status_code == HTTPStatus.TOO_MANY_REQUESTS:
        if retry_after := headers.get("retry-after"):
            logger.warning("Rate limit exceeded (429). Retry-After: %s", retry_after)
        else:
            logger.warning("Rate limit exceeded (429)")
        raise RateLimitError(url, status_code, content, headers)
    elif 500 <= status_code < 600:
        logger.warning("Server error (%d)", status_code)
        raise ServerError(url, status_code, content, headers)
    else:
        raise ResponseError(url, status_code, content, headers)


def _check_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    else:
        _raise_for_status(response.url, response.status_code, response.read(), response.headers)


async def _acheck_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    else:
        _raise_for_status(response.url, response.status_code, await response.aread(), response.headers)


def build_response(response: httpx.Response, model_class: type[T]) -> T:
    """Parse successful response into Pydantic model or raise error."""
    if response.status_code != HTTPStatus.OK:
        _raise_for_status(response.url, response.status_code, response.content, response.headers)
    try:
        payload = response.json()
        if isinstance(payload, dict):
            payload = {**payload, "x_headers": build_x_headers(response)}
        result = model_class.model_validate(payload)
        if isinstance(result, APIResponse):
            result.x_headers = build_x_headers(response)
        return result
    except (ValidationError, json.JSONDecodeError) as exc:
        raise APIResponseValidationError(
            "Invalid API response", request_id=response.headers.get("x-request-id")
        ) from exc


def execute_request_sync(client: httpx.Client, kwargs: dict[str, Any], model_class: type[T]) -> T:
    """Execute sync request and parse response."""
    from gigachat._core.execution import request_sync

    response = request_sync(client, **kwargs)
    return build_response(response, model_class)


async def execute_request_async(client: httpx.AsyncClient, kwargs: dict[str, Any], model_class: type[T]) -> T:
    """Execute async request and parse response."""
    from gigachat._core.execution import request_async

    response = await request_async(client, **kwargs)
    return build_response(response, model_class)


def _max_event_size() -> int:
    from gigachat._core.execution import current_request
    from gigachat._core.request import NotGiven
    from gigachat._core.streaming import DEFAULT_MAX_EVENT_SIZE

    state = current_request.get()
    if state is None:
        return DEFAULT_MAX_EVENT_SIZE
    configured = state.options.max_sse_event_size
    if isinstance(configured, NotGiven):
        return int(state.owner._settings.max_sse_event_size)
    return configured


def execute_stream_sync(client: httpx.Client, kwargs: dict[str, Any], model_class: type[T]) -> Iterator[T]:
    """Execute a streaming request and close its response on every exit."""
    from gigachat._core.execution import stream_sync
    from gigachat._core.streaming import Stream

    with stream_sync(client, **kwargs) as response:
        _check_response(response)
        with Stream(response, model_class, max_event_size=_max_event_size()) as stream:
            yield from stream


async def execute_stream_async(
    client: httpx.AsyncClient, kwargs: dict[str, Any], model_class: type[T]
) -> AsyncIterator[T]:
    """Execute an asynchronous streaming request with explicit response ownership."""
    from gigachat._core.execution import stream_async
    from gigachat._core.streaming import AsyncStream

    async with stream_async(client, **kwargs) as response:
        await _acheck_response(response)
        async with AsyncStream(response, model_class, max_event_size=_max_event_size()) as stream:
            async for chunk in stream:
                yield chunk


def execute_event_stream_sync(
    client: httpx.Client, kwargs: dict[str, Any], model_class: type[T], *, terminal_event: str | None = None
) -> Iterator[T]:
    """Execute an SSE request and yield parsed named or unnamed events."""
    from gigachat._core.execution import stream_sync
    from gigachat._core.streaming import Stream

    with stream_sync(client, **kwargs) as response:
        _check_response(response)
        with Stream(
            response, model_class, event_mode=True, terminal_event=terminal_event, max_event_size=_max_event_size()
        ) as stream:
            yield from stream


async def execute_event_stream_async(
    client: httpx.AsyncClient, kwargs: dict[str, Any], model_class: type[T], *, terminal_event: str | None = None
) -> AsyncIterator[T]:
    """Execute an asynchronous SSE request and yield parsed events."""
    from gigachat._core.execution import stream_async
    from gigachat._core.streaming import AsyncStream

    async with stream_async(client, **kwargs) as response:
        await _acheck_response(response)
        async with AsyncStream(
            response, model_class, event_mode=True, terminal_event=terminal_event, max_event_size=_max_event_size()
        ) as stream:
            async for chunk in stream:
                yield chunk
