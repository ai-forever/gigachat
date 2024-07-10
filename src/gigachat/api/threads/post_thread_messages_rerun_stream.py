from http import HTTPStatus
from typing import Any, AsyncIterator, Dict, Iterator, Optional

import httpx

from gigachat.api.utils import build_headers, parse_chunk
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.threads import ThreadCompletionChunk, ThreadRunOptions

EVENT_STREAM = "text/event-stream"


def _get_kwargs(
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.dict(exclude_none=True)
    params = {
        "method": "POST",
        "url": "/threads/messages/rerun",
        "headers": headers,
        "json": {
            **thread_options_dict,
            **{
                "thread_id": thread_id,
                "update_interval": update_interval,
                "stream": True,
            },
        },
    }
    return params


def _check_content_type(response: httpx.Response) -> None:
    content_type, _, _ = response.headers.get("content-type", "").partition(";")
    if content_type != EVENT_STREAM:
        raise httpx.TransportError(f"Expected response Content-Type to be '{EVENT_STREAM}', got {content_type!r}")


def _check_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.read(), response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.read(), response.headers)


async def _acheck_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, await response.aread(), response.headers)
    else:
        raise ResponseError(response.url, response.status_code, await response.aread(), response.headers)


def sync(
    client: httpx.Client,
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Iterator[ThreadCompletionChunk]:
    """Перегенерация ответа модели"""
    kwargs = _get_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    with client.stream(**kwargs) as response:
        _check_response(response)
        for line in response.iter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                yield chunk


async def asyncio(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Перегенерация ответа модели"""
    kwargs = _get_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    async with client.stream(**kwargs) as response:
        await _acheck_response(response)
        async for line in response.aiter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                yield chunk
