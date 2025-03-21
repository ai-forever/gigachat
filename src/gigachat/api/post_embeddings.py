import json
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import Embeddings


def _get_kwargs(
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


def sync(
    client: httpx.Client,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Embeddings:
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Embeddings)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Embeddings:
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Embeddings)
