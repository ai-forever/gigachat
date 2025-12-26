import logging
from http import HTTPStatus
from typing import Any, AsyncIterator, Dict, Iterator, NoReturn, Optional, Type, TypeVar, Union

import httpx
from pydantic import BaseModel

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

logger = logging.getLogger(__name__)

USER_AGENT = "GigaChat-python-lib"
EVENT_STREAM = "text/event-stream"


def build_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    """Build headers for the request."""
    headers = {}

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
    return headers


T = TypeVar("T", bound=BaseModel)


def parse_chunk(line: str, model_class: Type[T]) -> Optional[T]:
    """Parse a single line of SSE event data."""
    try:
        name, _, value = line.partition(":")
        if name == "data":
            value = value.lstrip()
            if value == "[DONE]":
                return None
            else:
                return model_class.model_validate_json(value)
    except Exception as e:
        logger.error("Error parsing chunk from server: %s, raw value: %s", e, line)
        raise
    else:
        return None


def build_x_headers(response: httpx.Response) -> Dict[str, Optional[str]]:
    """Extract X-Headers from response."""
    return {
        "x-request-id": response.headers.get("x-request-id"),
        "x-session-id": response.headers.get("x-session-id"),
        "x-client-id": response.headers.get("x-client-id"),
    }


def _check_content_type(response: httpx.Response) -> None:
    content_type, _, _ = response.headers.get("content-type", "").partition(";")
    if content_type != EVENT_STREAM:
        raise httpx.TransportError(f"Expected response Content-Type to be '{EVENT_STREAM}', got {content_type!r}")


def _raise_for_status(url: Union[httpx.URL, str], status_code: int, content: bytes, headers: httpx.Headers) -> NoReturn:
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
        logger.warning("Server error (%d) from %s", status_code, url)
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


def build_response(response: httpx.Response, model_class: Type[T]) -> T:
    """Parse successful response into Pydantic model or raise error."""
    if response.status_code == HTTPStatus.OK:
        return model_class(x_headers=build_x_headers(response), **response.json())
    else:
        _raise_for_status(response.url, response.status_code, response.content, response.headers)


def execute_request_sync(client: httpx.Client, kwargs: Dict[str, Any], model_class: Type[T]) -> T:
    """Execute sync request and parse response."""
    response = client.request(**kwargs)
    return build_response(response, model_class)


async def execute_request_async(client: httpx.AsyncClient, kwargs: Dict[str, Any], model_class: Type[T]) -> T:
    """Execute async request and parse response."""
    response = await client.request(**kwargs)
    return build_response(response, model_class)


def execute_stream_sync(client: httpx.Client, kwargs: Dict[str, Any], model_class: Type[T]) -> Iterator[T]:
    """Execute sync streaming request and yield parsed chunks."""
    with client.stream(**kwargs) as response:
        _check_response(response)
        x_headers = build_x_headers(response)
        for line in response.iter_lines():
            if chunk := parse_chunk(line, model_class):
                if hasattr(chunk, "x_headers"):
                    chunk.x_headers = x_headers
                yield chunk


async def execute_stream_async(
    client: httpx.AsyncClient, kwargs: Dict[str, Any], model_class: Type[T]
) -> AsyncIterator[T]:
    """Execute async streaming request and yield parsed chunks."""
    async with client.stream(**kwargs) as response:
        await _acheck_response(response)
        x_headers = build_x_headers(response)
        async for line in response.aiter_lines():
            if chunk := parse_chunk(line, model_class):
                if hasattr(chunk, "x_headers"):
                    chunk.x_headers = x_headers
                yield chunk
