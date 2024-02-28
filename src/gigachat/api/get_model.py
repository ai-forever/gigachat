from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Model


def _get_kwargs(
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": f"/models/{model}",
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> Model:
    if response.status_code == HTTPStatus.OK:
        return Model(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Model:
    """Возвращает объект с описанием указанной модели"""
    kwargs = _get_kwargs(model=model, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Model:
    """Возвращает объект с описанием указанной модели"""
    kwargs = _get_kwargs(model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
