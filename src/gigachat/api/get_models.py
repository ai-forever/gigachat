from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Models


def _get_kwargs(
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": "/models",
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> Models:
    if response.status_code == HTTPStatus.OK:
        return Models(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    access_token: Optional[str] = None,
) -> Models:
    """Возвращает массив объектов с данными доступных моделей"""
    kwargs = _get_kwargs(access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Models:
    """Возвращает массив объектов с данными доступных моделей"""
    kwargs = _get_kwargs(access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
