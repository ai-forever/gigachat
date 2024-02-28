from http import HTTPStatus
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Embeddings


def _get_kwargs(
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/embeddings",
        "json": {"input": input_, "model": model},
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> Embeddings:
    if response.status_code == HTTPStatus.OK:
        return Embeddings(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Embeddings:
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Embeddings:
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
