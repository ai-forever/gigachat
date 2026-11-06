import logging
import re
from collections.abc import AsyncIterator, Iterator
from typing import (
    Any,
    TypeVar,
)
from urllib.parse import urlsplit, urlunsplit

import httpx2 as httpx
from pydantic import BaseModel

from gigachat._core.request import USER_AGENT as USER_AGENT
from gigachat._core.request import build_headers as build_headers
from gigachat._core.response import EVENT_STREAM as EVENT_STREAM
from gigachat._core.response import _acheck_response as _acheck_response
from gigachat._core.response import _check_content_type as _check_content_type
from gigachat._core.response import _check_response as _check_response
from gigachat._core.response import _raise_for_status as _raise_for_status
from gigachat._core.response import build_response as build_response
from gigachat._core.response import build_x_headers as build_x_headers
from gigachat._core.response import parse_chunk as parse_chunk
from gigachat._core.response import parse_data_chunk as parse_data_chunk
from gigachat._core.response import parse_event_chunk as parse_event_chunk

logger = logging.getLogger(__name__)


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


T = TypeVar("T", bound=BaseModel)


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
