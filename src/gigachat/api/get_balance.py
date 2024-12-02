from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.balance import Balance


def _get_kwargs(
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": "/balance",
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> Balance:
    if response.status_code == HTTPStatus.OK:
        return Balance(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    access_token: Optional[str] = None,
) -> Balance:
    """Метод для получения баланса доступных для использования токенов.
    Только для клиентов с предоплатой иначе http 403"""
    kwargs = _get_kwargs(access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Balance:
    """Метод для получения баланса доступных для использования токенов.
    Только для клиентов с предоплатой иначе http 403"""
    kwargs = _get_kwargs(access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
