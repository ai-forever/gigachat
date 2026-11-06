from collections.abc import AsyncIterable, Iterable
from typing import Any, Literal

import httpx2 as httpx

from gigachat.api.utils import build_headers, execute_request_async, execute_request_sync
from gigachat.models.batches import Batch, Batches


def create_batch_sync(
    client: httpx.Client,
    *,
    data: bytes | Iterable[bytes],
    method: Literal["chat_completions", "embedder"],
    access_token: str | None = None,
) -> Batch:
    """Submit raw JSONL bytes or a byte stream as a stateful batch."""
    if not isinstance(data, bytes) and not isinstance(data, Iterable):
        raise TypeError("Batch data must be bytes or an iterable of bytes")
    kwargs = _get_create_batch_kwargs(data=data, method=method, access_token=access_token)
    return execute_request_sync(client, kwargs, Batch)


def get_batches_sync(client: httpx.Client, *, batch_id: str | None = None, access_token: str | None = None) -> Batches:
    """Query batches, optionally selecting one by its query identifier."""
    kwargs = _get_get_batches_kwargs(batch_id=batch_id, access_token=access_token)
    return execute_request_sync(client, kwargs, Batches)


async def create_batch_async(
    client: httpx.AsyncClient,
    *,
    data: bytes | AsyncIterable[bytes],
    method: Literal["chat_completions", "embedder"],
    access_token: str | None = None,
) -> Batch:
    """Submit raw JSONL bytes or a byte stream as a stateful batch."""
    if not isinstance(data, bytes) and not isinstance(data, AsyncIterable):
        raise TypeError("Batch data must be bytes or an async iterable of bytes")
    kwargs = _get_create_batch_kwargs(data=data, method=method, access_token=access_token)
    return await execute_request_async(client, kwargs, Batch)


async def get_batches_async(
    client: httpx.AsyncClient, *, batch_id: str | None = None, access_token: str | None = None
) -> Batches:
    """Query batches, optionally selecting one by its query identifier."""
    kwargs = _get_get_batches_kwargs(batch_id=batch_id, access_token=access_token)
    return await execute_request_async(client, kwargs, Batches)


def _get_create_batch_kwargs(
    *,
    data: bytes | Iterable[bytes] | AsyncIterable[bytes],
    method: Literal["chat_completions", "embedder"],
    access_token: str | None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/octet-stream"
    return {"method": "POST", "url": "/batches", "headers": headers, "params": {"method": method}, "content": data}


def _get_get_batches_kwargs(*, batch_id: str | None, access_token: str | None) -> dict[str, Any]:
    return {
        "method": "GET",
        "url": "/batches",
        "headers": build_headers(access_token),
        "params": {"batch_id": batch_id} if batch_id is not None else {},
    }
