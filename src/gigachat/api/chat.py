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
from gigachat.context import chat_url_cvar
from gigachat.models.chat import Chat, ChatCompletion, ChatCompletionChunk


def _get_chat_kwargs(
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"
    json_data = chat.model_dump(exclude_none=True, by_alias=True, exclude={"stream"})
    fields = json_data.pop("additional_fields", None)

    if fields:
        json_data = {**json_data, **fields}
    return {
        "method": "POST",
        "url": chat_url_cvar.get(),
        "content": json.dumps(json_data, ensure_ascii=False),
        "headers": headers,
    }


def chat_sync(
    client: httpx.Client,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> ChatCompletion:
    """Return a model response based on the provided messages."""
    kwargs = _get_chat_kwargs(chat=chat, access_token=access_token)
    return execute_request_sync(client, kwargs, ChatCompletion)


async def chat_async(
    client: httpx.AsyncClient,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> ChatCompletion:
    """Return a model response based on the provided messages."""
    kwargs = _get_chat_kwargs(chat=chat, access_token=access_token)
    return await execute_request_async(client, kwargs, ChatCompletion)


def _get_stream_kwargs(
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Accept"] = EVENT_STREAM
    headers["Cache-Control"] = "no-store"
    headers["Content-Type"] = "application/json"
    json_data = chat.model_dump(exclude_none=True, by_alias=True)
    fields = json_data.pop("additional_fields", None)
    if fields:
        json_data = {**json_data, **fields}

    return {
        "method": "POST",
        "url": chat_url_cvar.get(),
        "content": json.dumps({**json_data, **{"stream": True}}, ensure_ascii=False),
        "headers": headers,
    }


def stream_sync(
    client: httpx.Client,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> Iterator[ChatCompletionChunk]:
    """Return a model response based on the provided messages (streaming)."""
    kwargs = _get_stream_kwargs(chat=chat, access_token=access_token)
    return execute_stream_sync(client, kwargs, ChatCompletionChunk)


def stream_async(
    client: httpx.AsyncClient,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> AsyncIterator[ChatCompletionChunk]:
    """Return a model response based on the provided messages (streaming)."""
    kwargs = _get_stream_kwargs(chat=chat, access_token=access_token)
    return execute_stream_async(client, kwargs, ChatCompletionChunk)
