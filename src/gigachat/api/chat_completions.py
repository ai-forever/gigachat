import json
from typing import Any, AsyncIterator, Dict, Iterator, Optional

import httpx

from gigachat.api.utils import (
    EVENT_STREAM,
    build_headers,
    execute_request_async,
    execute_request_sync,
    execute_stream_async,
    execute_stream_sync,
)
from gigachat.context import chat_completions_url_cvar
from gigachat.models.chat_completions import ChatCompletionChunk, ChatCompletionRequest, ChatCompletionResponse


def _build_request_json(chat: ChatCompletionRequest) -> Dict[str, Any]:
    """Serialize *chat* to a JSON-ready dict."""
    return chat.model_dump(exclude_none=True, by_alias=True, exclude={"stream"})


def _get_chat_kwargs(
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"

    return {
        "method": "POST",
        "url": chat_completions_url_cvar.get(),
        "content": json.dumps(_build_request_json(chat), ensure_ascii=False),
        "headers": headers,
    }


def _get_stream_kwargs(
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Accept"] = EVENT_STREAM
    headers["Cache-Control"] = "no-store"
    headers["Content-Type"] = "application/json"

    request_data = _build_request_json(chat)
    request_data["stream"] = True

    return {
        "method": "POST",
        "url": chat_completions_url_cvar.get(),
        "content": json.dumps(request_data, ensure_ascii=False),
        "headers": headers,
    }


def chat_sync(
    client: httpx.Client,
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> ChatCompletionResponse:
    """Return a primary chat completion based on the provided messages."""
    kwargs = _get_chat_kwargs(chat=chat, access_token=access_token)
    return execute_request_sync(client, kwargs, ChatCompletionResponse)


async def chat_async(
    client: httpx.AsyncClient,
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> ChatCompletionResponse:
    """Return a primary chat completion based on the provided messages."""
    kwargs = _get_chat_kwargs(chat=chat, access_token=access_token)
    return await execute_request_async(client, kwargs, ChatCompletionResponse)


def stream_sync(
    client: httpx.Client,
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> Iterator[ChatCompletionChunk]:
    """Return a primary chat completion stream based on the provided messages."""
    kwargs = _get_stream_kwargs(chat=chat, access_token=access_token)
    return execute_stream_sync(client, kwargs, ChatCompletionChunk)


async def stream_async(
    client: httpx.AsyncClient,
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> AsyncIterator[ChatCompletionChunk]:
    """Return a primary chat completion stream based on the provided messages."""
    kwargs = _get_stream_kwargs(chat=chat, access_token=access_token)
    async for chunk in execute_stream_async(client, kwargs, ChatCompletionChunk):
        yield chunk


__all__ = [
    "_build_request_json",
    "_get_chat_kwargs",
    "_get_stream_kwargs",
    "chat_async",
    "chat_sync",
    "stream_async",
    "stream_sync",
]
