import json
from typing import Any, AsyncIterator, Dict, Iterator, Mapping, Optional

import httpx

from gigachat.api.utils import (
    EVENT_STREAM,
    build_headers,
    execute_request_async,
    execute_request_sync,
    execute_stream_async,
    execute_stream_sync,
)
from gigachat.context import chat_v2_url_cvar
from gigachat.models.chat_v2 import ChatCompletionV2, ChatCompletionV2Chunk, ChatV2


def _deep_merge_with_typed_precedence(base: Mapping[str, Any], typed: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in typed.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_with_typed_precedence(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_chat_v2_url(base_url: str) -> str:
    """Resolve the absolute v2 chat URL from settings or an override context var."""
    override = chat_v2_url_cvar.get()
    parsed_base_url = httpx.URL(base_url)
    origin = parsed_base_url.copy_with(path="/", query=None, fragment=None)

    if override is not None:
        if override.startswith(("http://", "https://")):
            return override
        if override.startswith("/"):
            return str(origin.copy_with(path=override))
        raise ValueError("chat_v2_url_cvar must be an absolute URL or an absolute path starting with '/'")

    base_path = parsed_base_url.path.rstrip("/")
    if not base_path.endswith("/v1"):
        raise ValueError(
            f"Cannot derive v2 chat URL from base_url={base_url!r}; "
            "set chat_v2_url_cvar or use a base_url ending with '/api/v1'"
        )

    v2_path = f"{base_path[:-len('/api/v1')]}/v2/chat/completions"
    return str(origin.copy_with(path=v2_path))


def _build_chat_v2_payload(*, chat: ChatV2, stream: bool) -> Dict[str, Any]:
    typed_payload = chat.model_dump(exclude_none=True, by_alias=True, exclude={"stream", "additional_fields"})
    additional_fields = chat.additional_fields or {}
    payload = _deep_merge_with_typed_precedence(additional_fields, typed_payload)
    if stream:
        payload["stream"] = True
    return payload


def _get_chat_v2_kwargs(
    *,
    chat: ChatV2,
    base_url: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"
    payload = _build_chat_v2_payload(chat=chat, stream=False)

    return {
        "method": "POST",
        "url": resolve_chat_v2_url(base_url),
        "content": json.dumps(payload, ensure_ascii=False),
        "headers": headers,
    }


def chat_v2_sync(
    client: httpx.Client,
    *,
    chat: ChatV2,
    base_url: str,
    access_token: Optional[str] = None,
) -> ChatCompletionV2:
    """Return a v2 model response based on the provided messages."""
    kwargs = _get_chat_v2_kwargs(chat=chat, base_url=base_url, access_token=access_token)
    return execute_request_sync(client, kwargs, ChatCompletionV2)


async def chat_v2_async(
    client: httpx.AsyncClient,
    *,
    chat: ChatV2,
    base_url: str,
    access_token: Optional[str] = None,
) -> ChatCompletionV2:
    """Return an async v2 model response based on the provided messages."""
    kwargs = _get_chat_v2_kwargs(chat=chat, base_url=base_url, access_token=access_token)
    return await execute_request_async(client, kwargs, ChatCompletionV2)


def _get_stream_v2_kwargs(
    *,
    chat: ChatV2,
    base_url: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Accept"] = EVENT_STREAM
    headers["Cache-Control"] = "no-store"
    headers["Content-Type"] = "application/json"
    payload = _build_chat_v2_payload(chat=chat, stream=True)

    return {
        "method": "POST",
        "url": resolve_chat_v2_url(base_url),
        "content": json.dumps(payload, ensure_ascii=False),
        "headers": headers,
    }


def stream_v2_sync(
    client: httpx.Client,
    *,
    chat: ChatV2,
    base_url: str,
    access_token: Optional[str] = None,
) -> Iterator[ChatCompletionV2Chunk]:
    """Return a streaming v2 model response based on the provided messages."""
    kwargs = _get_stream_v2_kwargs(chat=chat, base_url=base_url, access_token=access_token)
    return execute_stream_sync(client, kwargs, ChatCompletionV2Chunk)


def stream_v2_async(
    client: httpx.AsyncClient,
    *,
    chat: ChatV2,
    base_url: str,
    access_token: Optional[str] = None,
) -> AsyncIterator[ChatCompletionV2Chunk]:
    """Return an async streaming v2 model response based on the provided messages."""
    kwargs = _get_stream_v2_kwargs(chat=chat, base_url=base_url, access_token=access_token)
    return execute_stream_async(client, kwargs, ChatCompletionV2Chunk)
