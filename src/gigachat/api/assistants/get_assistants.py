from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.assistants import Assistants


def _get_kwargs(
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params = {
        "method": "GET",
        "url": "/assistants",
        "headers": headers,
    }
    if assistant_id:
        params["params"] = {"assistant_id": assistant_id}
    return params


def _build_response(response: httpx.Response) -> Assistants:
    if response.status_code == HTTPStatus.OK:
        return Assistants(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Assistants:
    """Возвращает массив объектов с данными доступных ассистентов"""
    kwargs = _get_kwargs(assistant_id=assistant_id, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Assistants:
    """Возвращает массив объектов с данными доступных ассистентов"""
    kwargs = _get_kwargs(assistant_id=assistant_id, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
