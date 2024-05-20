from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.threads import ThreadRunResult


def _get_kwargs(
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params = {
        "method": "GET",
        "url": "/threads/run",
        "headers": headers,
        "params": {"thread_id": thread_id},
    }
    return params


def _build_response(response: httpx.Response) -> ThreadRunResult:
    if response.status_code == HTTPStatus.OK:
        return ThreadRunResult(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> ThreadRunResult:
    """Получить результат run треда"""
    kwargs = _get_kwargs(thread_id=thread_id, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> ThreadRunResult:
    """Получить результат run треда"""
    kwargs = _get_kwargs(thread_id=thread_id, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
