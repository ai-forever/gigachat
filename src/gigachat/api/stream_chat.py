import json
from http import HTTPStatus
from typing import Any, AsyncIterator, Dict, Iterator, Optional

import httpx

from gigachat.api.utils import build_headers, build_x_headers, parse_chunk
from gigachat.context import chat_url_cvar
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Chat, ChatCompletionChunk

EVENT_STREAM = "text/event-stream"


def _get_kwargs(
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Accept"] = EVENT_STREAM
    headers["Cache-Control"] = "no-store"
    headers["Content-Type"] = "application/json"
    json_data = chat.dict(exclude_none=True, by_alias=True)
    fields = json_data.pop("additional_fields", None)
    if fields:
        json_data = {**json_data, **fields}

    return {
        "method": "POST",
        "url": chat_url_cvar.get(),
        "content": json.dumps({**json_data, **{"stream": True}}, ensure_ascii=False),
        "headers": headers,
    }


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
    chat: Chat,
    access_token: Optional[str] = None,
) -> Iterator[ChatCompletionChunk]:
    kwargs = _get_kwargs(chat=chat, access_token=access_token)
    with client.stream(**kwargs) as response:
        _check_response(response)
        x_headers = build_x_headers(response)
        for line in response.iter_lines():
            if chunk := parse_chunk(line, ChatCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk


async def asyncio(
    client: httpx.AsyncClient,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> AsyncIterator[ChatCompletionChunk]:
    kwargs = _get_kwargs(chat=chat, access_token=access_token)
    async with client.stream(**kwargs) as response:
        await _acheck_response(response)
        x_headers = build_x_headers(response)
        async for line in response.aiter_lines():
            if chunk := parse_chunk(line, ChatCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk
