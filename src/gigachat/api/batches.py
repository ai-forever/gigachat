from typing import Any, Dict, Literal, Optional

import httpx

from gigachat._types import FileContent
from gigachat.api.utils import build_headers, execute_request_async, execute_request_sync
from gigachat.models.batches import Batch, Batches


def _get_batch_content(file: FileContent) -> bytes:
    if isinstance(file, bytes):
        return file
    if isinstance(file, str):
        return file.encode("utf-8")

    content = file.read()
    if isinstance(content, bytes):
        return content
    return content.encode("utf-8")


def _create_batch_kwargs(
    *,
    file: FileContent,
    method: Literal["chat_completions", "embedder"],
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/octet-stream"

    return {
        "method": "POST",
        "url": "/batches",
        "content": _get_batch_content(file),
        "params": {"method": method},
        "headers": headers,
    }


def create_batch_sync(
    client: httpx.Client,
    *,
    file: FileContent,
    method: Literal["chat_completions", "embedder"],
    access_token: Optional[str] = None,
) -> Batch:
    """Create a batch task for asynchronous processing."""
    kwargs = _create_batch_kwargs(file=file, method=method, access_token=access_token)
    return execute_request_sync(client, kwargs, Batch)


async def create_batch_async(
    client: httpx.AsyncClient,
    *,
    file: FileContent,
    method: Literal["chat_completions", "embedder"],
    access_token: Optional[str] = None,
) -> Batch:
    """Create a batch task for asynchronous processing."""
    kwargs = _create_batch_kwargs(file=file, method=method, access_token=access_token)
    return await execute_request_async(client, kwargs, Batch)


def _get_batches_kwargs(
    *,
    batch_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"

    params = {"batch_id": batch_id} if batch_id is not None else None
    return {
        "method": "GET",
        "url": "/batches",
        "params": params,
        "headers": headers,
    }


def get_batches_sync(
    client: httpx.Client,
    *,
    batch_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Batches:
    """Return batch tasks or a specific batch task."""
    kwargs = _get_batches_kwargs(batch_id=batch_id, access_token=access_token)
    return execute_request_sync(client, kwargs, Batches)


async def get_batches_async(
    client: httpx.AsyncClient,
    *,
    batch_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Batches:
    """Return batch tasks or a specific batch task."""
    kwargs = _get_batches_kwargs(batch_id=batch_id, access_token=access_token)
    return await execute_request_async(client, kwargs, Batches)
