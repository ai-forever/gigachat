import json
from typing import Any

import httpx2 as httpx

from gigachat.api.utils import build_headers, execute_request_async, execute_request_sync
from gigachat.models.embeddings import Embeddings


def _get_embeddings_kwargs(
    *,
    input_: str | list[str],
    model: str,
    encoding_format: str | None = None,
    truncate: str | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"

    body: dict[str, Any] = {"input": input_, "model": model}
    if encoding_format is not None:
        body["encoding_format"] = encoding_format
    if truncate is not None:
        body["truncate"] = truncate
    return {
        "method": "POST",
        "url": "/embeddings",
        "content": json.dumps(body, ensure_ascii=False),
        "headers": headers,
    }


def embeddings_sync(
    client: httpx.Client,
    *,
    input_: str | list[str],
    model: str,
    encoding_format: str | None = None,
    truncate: str | None = None,
    access_token: str | None = None,
) -> Embeddings:
    """Return embeddings."""
    kwargs = _get_embeddings_kwargs(
        input_=input_, model=model, encoding_format=encoding_format, truncate=truncate, access_token=access_token
    )
    return execute_request_sync(client, kwargs, Embeddings)


async def embeddings_async(
    client: httpx.AsyncClient,
    *,
    input_: str | list[str],
    model: str,
    encoding_format: str | None = None,
    truncate: str | None = None,
    access_token: str | None = None,
) -> Embeddings:
    """Return embeddings."""
    kwargs = _get_embeddings_kwargs(
        input_=input_, model=model, encoding_format=encoding_format, truncate=truncate, access_token=access_token
    )
    return await execute_request_async(client, kwargs, Embeddings)
