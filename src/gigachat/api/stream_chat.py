from http import HTTPStatus
from typing import Any, AsyncIterator, Dict, Iterator, Mapping, Optional

import httpx

from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Chat, ChatCompletionChunk

EVENT_STREAM = "text/event-stream"


def _get_kwargs(chat: Chat, headers: Optional[Mapping[str, str]]) -> Dict[str, Any]:
    _headers = {
        "Accept": EVENT_STREAM,
        "Cache-Control": "no-store",
    }
    _headers.update(headers or {})

    return {
        "method": "POST",
        "url": "/chat/completions",
        "json": {**chat.dict(exclude_none=True), **{"stream": True}},
        "headers": _headers,
    }


def _parse_chunk(line: str) -> Optional[ChatCompletionChunk]:
    name, _, value = line.partition(": ")
    if name == "data":
        if value == "[DONE]":
            return None
        else:
            return ChatCompletionChunk.parse_raw(value)
    else:
        return None


def _check_content_type(response: httpx.Response) -> None:
    content_type, _, _ = response.headers.get("content-type", "").partition(";")
    if content_type != EVENT_STREAM:
        raise httpx.TransportError(f"Expected response Content-Type to be '{EVENT_STREAM}', got {content_type!r}")


def _check_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, b"", response.headers)
    else:
        raise ResponseError(response.url, response.status_code, b"", response.headers)


def sync(client: httpx.Client, chat: Chat, headers: Optional[Mapping[str, str]]) -> Iterator[ChatCompletionChunk]:
    kwargs = _get_kwargs(chat, headers)
    with client.stream(**kwargs) as response:
        _check_response(response)
        for line in response.iter_lines():
            if chunk := _parse_chunk(line):
                yield chunk


async def asyncio(
    client: httpx.AsyncClient, chat: Chat, headers: Optional[Mapping[str, str]]
) -> AsyncIterator[ChatCompletionChunk]:
    kwargs = _get_kwargs(chat, headers)
    async with client.stream(**kwargs) as response:
        _check_response(response)
        async for line in response.aiter_lines():
            if chunk := _parse_chunk(line):
                yield chunk
