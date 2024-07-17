from http import HTTPStatus
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.threads import Threads


def _get_kwargs(
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params = {
        "method": "POST",
        "url": "/threads/retrieve",
        "json": {
            "threads_ids": threads_ids,
        },
        "headers": headers,
    }
    return params


def _build_response(response: httpx.Response) -> Threads:
    if response.status_code == HTTPStatus.OK:
        return Threads(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов по идентификаторам"""
    kwargs = _get_kwargs(threads_ids=threads_ids, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов по идентификаторам"""
    kwargs = _get_kwargs(threads_ids=threads_ids, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
