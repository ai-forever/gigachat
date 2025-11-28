import json
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers, execute_request_async, execute_request_sync
from gigachat.models.embeddings import Embeddings


def _get_embeddings_kwargs(
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"

    return {
        "method": "POST",
        "url": "/embeddings",
        "content": json.dumps({"input": input_, "model": model}, ensure_ascii=False),
        "headers": headers,
    }


def embeddings_sync(
    client: httpx.Client,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Embeddings:
    """Return embeddings."""
    kwargs = _get_embeddings_kwargs(input_=input_, model=model, access_token=access_token)
    return execute_request_sync(client, kwargs, Embeddings)


async def embeddings_async(
    client: httpx.AsyncClient,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Embeddings:
    """Return embeddings."""
    kwargs = _get_embeddings_kwargs(input_=input_, model=model, access_token=access_token)
    return await execute_request_async(client, kwargs, Embeddings)
